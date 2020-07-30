#!/usr/bin/env python3

from argparse import ArgumentParser
import json
from paho.mqtt.client import topic_matches_sub, Client as MqttClient
from prometheus_client import start_http_server, Gauge
import re
import signal
import sys
import threading


class State(Gauge):
    pass


METRICS = {
    'linkquality': Gauge('linkquality', 'Quality of the Zigbee connection', ['topic']),
    'state': State('state', 'State of the switch', ['topic']),
    'battery': Gauge('battery', 'Remaining capacity of battery', ['topic']),
    'temperature': Gauge('temperature', 'Temperature', ['topic'], unit='celsius'),
    'illuminance': Gauge('illuminance_raw', 'Illuminance', ['topic']),
    'lux': Gauge('lux', 'Lux', ['topic']),
}
SERVICE_SUBSCRIPTION = 'service/#'
SERVICE_REGEX = re.compile('^service/')
SERVICE_METRIC = Gauge('service', 'State of the service', ['topic'])


class MqttToPrometheus(object):
    def __init__(self):
        self.__verbose = False
        self.__config = {}

        self.__wait_mutex = threading.Event()
        signal.signal(signal.SIGINT, self.__signal_handler)

        self.__mqtt = MqttClient()

    def run(self):
        try:
            parser = ArgumentParser(description='Read data from MQTT and make it available for Prometheus')
            parser.add_argument(
                '-c',
                '--config',
                action='store',
                default='/etc/nerdhome/mqtt-to-prometheus.json',
                dest='config'
            )
            parser.add_argument('-v', '--verbose', action='store_true', default=False, dest='verbose')
            argv = parser.parse_args()

            self.__verbose = argv.verbose
            with open(argv.config) as fd:
                self.__config = json.load(fd)

            self.__mqtt.connect(
                self.__config.get('mqtt', {}).get('host'),
                port=self.__config.get('mqtt', {}).get('port', 1883)
            )

            self.__mqtt.on_connect = self.__mqtt_on_connect

            self.__mqtt.message_callback_add(SERVICE_SUBSCRIPTION, self._mqtt_handle_topic)
            for subscription in self.__config.get('topics', {}).keys():
                self.__mqtt.message_callback_add(subscription, self._mqtt_handle_topic)

            self.__mqtt.loop_start()

            start_http_server(self.__config.get('prometheus-exporter', {}).get('port', 8000))

            while not self.__wait_mutex.wait():
                pass
        except KeyboardInterrupt:
            pass
        finally:
            self.__mqtt.publish('service/mqtt-to-prometheus', 0, qos=1, retain=True)
            self.__mqtt.loop_stop()
            self.__mqtt.disconnect()

        sys.exit(0)

    def __mqtt_on_connect(self, client, userdata, flags, rc):
        if self.__verbose:
            print('MQTT connected to', str(rc))

        client.will_set('service/mqtt-to-prometheus', 0, qos=1, retain=True)
        client.publish('service/mqtt-to-prometheus', 1, qos=1, retain=True)

        for subscription in self.__config.get('topics', {}).keys():
            if self.__verbose:
                print('MQTT subscribed to', subscription)
            client.subscribe(subscription, qos=0)

    def _mqtt_handle_topic(self, client, userdata, message):
        if self.__verbose:
            print('MQTT message: ', message.topic, message.payload.decode('utf-8'))

        for subscription, fields in self.__config.get('topics', {}).items():
            payload = message.payload
            if payload is not None:
                payload = payload.decode('utf-8')

            if SERVICE_REGEX.match(message.topic):
                metric = SERVICE_METRIC.labels(topic=message.topic)
                metric.set(self.__payload_to_metric_value(payload))
            elif topic_matches_sub(subscription, message.topic):
                try:
                    data = json.loads(payload)
                except json.JSONDecodeError:
                    return

                for field, metric_label in fields.items():
                    if field in data:
                        metric = METRICS[metric_label].labels(topic=message.topic)

                        if isinstance(metric, State):
                            metric.set(self.__payload_to_metric_value(data[field]))
                        elif isinstance(metric, Gauge):
                            metric.set(data[field])

                return

    @staticmethod
    def __payload_to_metric_value(payload):
        return 0 if str(payload).lower() in ['0', 'null', 'false', 'off', 'no'] else 1

    def __signal_handler(self, signal, frame):
        self.__wait_mutex.set()


if __name__ == '__main__':
    MqttToPrometheus().run()

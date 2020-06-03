#!/usr/bin/env python3

from argparse import ArgumentParser
import json
from paho.mqtt.client import Client as MqttClient
from prometheus_client import start_http_server, Enum, Gauge
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

TOPICS = {
    'zigbee2mqtt/lights_werkkamer': {
        'linkquality': 'linkquality',
        'state': 'state',
    },
    'zigbee2mqtt/werkkamer_motionsensor': {
        'battery': 'battery',
        'linkquality': 'linkquality',
        'occupancy': 'state',
        'temperature': 'temperature',
        'illuminance': 'illuminance',
        'illuminance_lux': 'lux',
    }
}


class MqttToPrometheus(object):
    def __init__(self):
        self.__verbose = False

        self.__wait_mutex = threading.Event()
        signal.signal(signal.SIGINT, self.__signal_handler)

        self.__mqtt = MqttClient()

        self.__stats = {}
        self.__stats_mutex = threading.Lock()

    def run(self):
        try:
            parser = ArgumentParser(description='Read data from MQTT and make it available for Prometheus')
            parser.add_argument('-m', '--mqtt', action='store', default='localhost', dest='mqtt')
            parser.add_argument('-p', '--port', action='store', default=8000, dest='port', type=int)
            parser.add_argument('-v', '--verbose', action='store_true', default=False, dest='verbose')
            argv = parser.parse_args()

            self.__verbose = argv.verbose

            self.__mqtt.on_connect = self.__mqtt_on_connect

            for topic in TOPICS.keys():
                self.__mqtt.message_callback_add(topic, self._mqtt_handle_topic)

            self.__mqtt.connect(argv.mqtt)
            self.__mqtt.loop_start()

            start_http_server(argv.port)

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

        for topic in TOPICS.keys():
            if self.__verbose:
                print('MQTT subscribed to', topic)
            client.subscribe(topic, qos=0)

    def _mqtt_handle_topic(self, client, userdata, message):
        if self.__verbose:
            print('MQTT message: ', message.topic, message.payload.decode('utf-8'))

        data = json.loads(message.payload.decode('utf-8'))

        fields = TOPICS.get(message.topic, {})
        for field, metric_label in fields.items():
            if field in data:
                metric = METRICS[metric_label].labels(topic=message.topic)

                if isinstance(metric, State):
                    metric.set(0 if str(data[field]).lower() in ['0', 'null', 'false', 'off', 'no'] else 1)
                elif isinstance(metric, Gauge):
                    metric.set(data[field])

    def __signal_handler(self, signal, frame):
        self.__wait_mutex.set()


if __name__ == '__main__':
    MqttToPrometheus().run()

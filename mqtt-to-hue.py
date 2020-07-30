#!/usr/bin/env python3

from argparse import ArgumentParser
import json
from paho.mqtt.client import topic_matches_sub, Client as MqttClient
from phue import Bridge
import signal
import sys
import threading


class MqttToHue(object):
    def __init__(self):
        self.__verbose = False
        self.__config = {}

        self.__wait_mutex = threading.Event()
        signal.signal(signal.SIGINT, self.__signal_handler)

        self.__mqtt = MqttClient()
        self.__bridge = None

    def run(self):
        try:
            parser = ArgumentParser(description='Read data from MQTT and map it to a light in Philips Hue')
            parser.add_argument(
                '-c',
                '--config',
                action='store',
                default='/etc/nerdhome/mqtt-to-hue.json',
                dest='config'
            )
            parser.add_argument('-v', '--verbose', action='store_true', default=False, dest='verbose')
            argv = parser.parse_args()

            self.__verbose = argv.verbose
            with open(argv.config) as fd:
                self.__config = json.load(fd)

            self.__bridge = Bridge(self.__config.get('hue', {}).get('host'))
            self.__bridge.connect()

            self.__bridge.set_light('Slaapkamer', 'on', True)

            self.__mqtt.connect(
                self.__config.get('mqtt', {}).get('host'),
                port=self.__config.get('mqtt', {}).get('port', 1883)
            )

            self.__mqtt.on_connect = self.__mqtt_on_connect

            for topic in self.__config.get('mapping', {}).keys():
                self.__mqtt.message_callback_add(topic, self._mqtt_handle_topic)

            self.__mqtt.loop_start()

            while not self.__wait_mutex.wait():
                pass
        except KeyboardInterrupt:
            pass
        finally:
            self.__mqtt.publish('service/mqtt-to-hue', 0, qos=1, retain=True)
            self.__mqtt.loop_stop()
            self.__mqtt.disconnect()

        sys.exit(0)

    def __mqtt_on_connect(self, client, userdata, flags, rc):
        if self.__verbose:
            print('MQTT connected to', str(rc))

        client.will_set('service/mqtt-to-hue', 0, qos=1, retain=True)
        client.publish('service/mqtt-to-hue', 1, qos=1, retain=True)

        for topic in self.__config.get('mapping', {}).keys():
            if self.__verbose:
                print('MQTT subscribed to', topic)
            client.subscribe(topic, qos=0)

    def _mqtt_handle_topic(self, client, userdata, message):
        if self.__verbose:
            print('MQTT message: ', message.topic, message.payload.decode('utf-8'))

        for topic, light in self.__config.get('mapping', {}).items():
            try:
                data = json.loads(message.payload.decode('utf-8'))
                if 'click' in data:
                    if self.__verbose:
                        print('Turning', light, 'on' if data['click'] == 'on' else 'off')
                    self.__bridge.set_light(light, 'on', data['click'] == 'on')
            except json.JSONDecodeError:
                pass

    def __signal_handler(self, signal, frame):
        self.__wait_mutex.set()


if __name__ == '__main__':
    MqttToHue().run()

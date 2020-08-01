from argparse import ArgumentParser
from datetime import datetime
import json
from paho.mqtt.client import Client as MqttClient
import signal
import threading
from time import time

import RPi.GPIO as GPIO
from Nerdman.LedButton import LedButton
from Nerdman.Doorbell import Doorbell


class Application(object):
    def __init__(self):
        self.__verbose = False
        self.__config = {}

        self.__doorbell = None
        self.__doorbells = []

        self.__wait_mutex = threading.Event()
        signal.signal(signal.SIGINT, self.__signal_handler)

        self.__mqtt = MqttClient()

    def run(self):
        try:
            parser = ArgumentParser(description='Ring the physical doorbell and report to MQTT')
            parser.add_argument(
                '-c',
                '--config',
                action='store',
                default='/etc/nerdhome/doorbell.json',
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
            self.__mqtt.loop_start()

            GPIO.setmode(GPIO.BOARD)

            for doorbell, config in self.__config.get('doorbells', {}).items():
                if self.__verbose:
                    print('Adding doorbell', doorbell, ':', config)

                button = LedButton(config['button_gpio'], config['relay_gpio'], name=doorbell)

                if button.button_state() == LedButton.PRESSED:
                    self.__mqtt.publish(
                        'doorbell/' + button.name(),
                        json.dumps({'state': 'on', 'timestamp': time()}),
                        qos=1
                    )

                button.on_changed(self._handle_doorbell)
                self.__doorbells.append(button)

            self.__doorbell = Doorbell(self.__verbose)
            self.__doorbell.start()

            while not self.__wait_mutex.wait():
                pass
        except KeyboardInterrupt:
            pass
        finally:
            if self.__doorbell is not None:
                self.__doorbell.stop()
                self.__doorbell.join()

            self.__mqtt.publish('service/doorbell', 0, qos=1, retain=True)
            self.__mqtt.loop_stop()
            self.__mqtt.disconnect()

            GPIO.cleanup()

    def _handle_doorbell(self, button):
        timestamp = time()
        state = 'on' if button.button_state() == LedButton.PRESSED else 'off'

        if state == 'on':
            self.__mqtt.publish(
                'doorbell/' + button.name(),
                json.dumps({'state': state, 'timestamp': timestamp}),
                qos=1
            )

            rings = self.__config.get('doorbells', {}).get(button.name(), {}).get('rings', 1)
            self.__doorbell.ring(button, rings)

        if self.__verbose:
            print(
                datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S.%f'),
                'The', button.name(), 'doorbell is', 'pressed' if state == 'on' else 'released'
            )

    def __mqtt_on_connect(self, client, userdata, flags, rc):
        if self.__verbose:
            print('MQTT connected to', str(rc))

        client.will_set('service/doorbell', 0, qos=1, retain=True)
        client.publish('service/doorbell', 1, qos=1, retain=True)

    def __signal_handler(self, signal, frame):
        self.__wait_mutex.set()


if __name__ == '__main__':
    Application().run()

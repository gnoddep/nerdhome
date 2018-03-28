#!/usr/bin/env python3

import sys
import signal
import threading
from datetime import datetime
from time import time
from argparse import ArgumentParser
from paho.mqtt.client import Client as MqttClient

import RPi.GPIO as GPIO
from Nerdman.Button import Button

class Doorbell:
    DOORBELL_INTERCOM = 18
    DOORBELL_DOOR = 15

    def __init__(self):
        self.wait_mutex = threading.Event()
        signal.signal(signal.SIGINT, self._signal_handler)
        self.mqtt = MqttClient()
        self.verbose = False

    def run(self):
        parser = ArgumentParser(description='Read data from the doorbell relays send it to MQTT')
        parser.add_argument('-m', '--hostname', action='store', default='localhost', dest='hostname')
        parser.add_argument('-v', '--verbose', action='store_true', default=False, dest='verbose')
        argv = parser.parse_args()

        self.verbose = argv.verbose

        GPIO.setmode(GPIO.BOARD)

        door = Button(self.DOORBELL_DOOR, name='door', bouncetime=100)
        door.on_changed(self._handle_doorbell)

        intercom = Button(self.DOORBELL_INTERCOM, name='intercom', bouncetime=100)
        intercom.on_changed(self._handle_doorbell)

        try:
            self.mqtt.on_connect = self._mqtt_on_connect
            self.mqtt.connect(argv.hostname)
            self.mqtt.loop_start()

            if self.verbose:
                print("Press CTRL+C to exit")
            while not self.wait_mutex.wait():
                pass
        except KeyboardInterrupt:
            pass
        finally:
            self.mqtt.publish('service/doorbell', 0, qos=1, retain=True)
            self.mqtt.loop_stop()
            self.mqtt.disconnect()
            GPIO.cleanup()

        sys.exit(0)

    def _handle_doorbell(self, button):
        timestamp = time()
        state = button.button_state()
        self.mqtt.publish('doorbell/' + button.name(), str(state) + ':' + str(timestamp), qos=0)

        if self.verbose:
            print(datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S.%f'), 'The', button.name(), 'doorbell is', 'pressed' if state else 'released')

    def _mqtt_on_connect(self, client, userdata, flags, rc):
        if self.verbose:
            print('Connected to MQTT:', str(rc))

        client.will_set('service/doorbell', 0, qos=1, retain=True)
        client.publish('service/doorbell', 1, qos=1, retain=True)

    def _signal_handler(self, signal, frame):
        self.wait_mutex.set()

if __name__ == '__main__':
    Doorbell().run()


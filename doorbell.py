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

    def run(self):
        parser = ArgumentParser(description='Read data from the doorbell relays send it to MQTT')
        parser.add_argument('-m', '--hostname', action='store', default='localhost', dest='hostname')
        argv = parser.parse_args()

        GPIO.setmode(GPIO.BOARD)

        door = Button(self.DOORBELL_DOOR, name='door', bouncetime=100)
        door.on_changed(self._handle_doorbell)

        intercom = Button(self.DOORBELL_INTERCOM, name='intercom', bouncetime=100)
        intercom.on_changed(self._handle_doorbell)

        try:
            self.mqtt.connect(argv.hostname)
            self.mqtt.loop_start()

            self._handle_doorbell(door)

            print("Press CTRL+C to exit")
            while not self.wait_mutex.wait():
                pass
        except KeyboardInterrupt:
            pass
        finally:
            self.mqtt.loop_stop()
            self.mqtt.disconnect()
            GPIO.cleanup()

        sys.exit(0)

    def _handle_doorbell(self, button):
        state = button.button_state()
        self.mqtt.publish('doorbell/' + button.name(), str(state) + ':' + str(time()), qos=0)
        print(datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'), 'The', button.name(), 'doorbell is', 'pressed' if state else 'released')

    def _signal_handler(self, signal, frame):
        self.wait_mutex.set()

if __name__ == '__main__':
    Doorbell().run()


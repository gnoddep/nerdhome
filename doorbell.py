#!/usr/bin/env python3

import signal
import threading
from datetime import datetime
from influxdb import InfluxDBClient
from socket import getfqdn
from argparse import ArgumentParser

import RPi.GPIO as GPIO
from Nerdman.Button import Button

class Doorbell:
    DOORBELL_DOWNSTAIRS = 18
    DOORBELL_UPSTAIRS = 15

    def __init__(self):
        self.wait_mutex = threading.Event()
        signal.signal(signal.SIGINT, self._signal_handler)
        self.influxdb = None
        self.fqdn = getfqdn()

    def run(self):
        parser = ArgumentParser(description='Read data from the doorbell relays send it to influxdb')
        parser.add_argument('-i', '--hostname', action='store', default='localhost', dest='hostname')
        parser.add_argument('-d', '--database', action='store', default='doorbell', dest='database')

        argv = parser.parse_args()

        GPIO.setmode(GPIO.BOARD)

        doorbellDownstairs = Button(self.DOORBELL_DOWNSTAIRS, name='intercom', bouncetime=100)
        doorbellDownstairs.on_changed(self._handle_doorbell)

        doorbellUpstairs = Button(self.DOORBELL_UPSTAIRS, name='door', bouncetime=100)
        doorbellUpstairs.on_changed(self._handle_doorbell)

        try:
            self.influxdb = InfluxDBClient(argv.hostname, database=argv.database)
            self.influxdb.create_database(argv.database)

            print("Press CTRL+C to exit")
            while not self.wait_mutex.wait():
                pass

            return
        except KeyboardInterrupt:
            pass
        finally:
            GPIO.cleanup()

        sys.exit(0)

    def _handle_doorbell(self, button):
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        state = button.button_state()
        self._send_to_influxdb(button.name(), state)
        print(timestamp, 'The', button.name(), 'doorbell is', 'pressed' if state else 'released')

    def _signal_handler(self, signal, frame):
        self.wait_mutex.set()

    def _send_to_influxdb(self, doorbell, state):
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        data = [
            {
                'measurement': 'doorbell',
                'tags': {
                    'host': self.fqdn,
                    'doorbell': doorbell,
                },
                'time': timestamp,
                'fields': {
                    'state': state,
                },
            },
        ]

        self.influxdb.write_points(data, time_precision='u')

if __name__ == '__main__':
    Doorbell().run()


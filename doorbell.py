#!/usr/bin/env python3

import signal
import threading
from datetime import datetime
from influxdb import InfluxDBClient
from socket import getfqdn
from argparse import ArgumentParser

import RPi.GPIO as GPIO
from Nerdman.Button import Button

DOORBELL_DOWNSTAIRS = 18
DOORBELL_UPSTAIRS = 15

wait_mutex = threading.Event()
influxdb = None
fqdn = getfqdn()

def main():
    global influxdb

    parser = ArgumentParser(description='Read data from the doorbell relays send it to influxdb')
    parser.add_argument('-i', '--hostname', action='store', default='localhost', dest='hostname')
    parser.add_argument('-d', '--database', action='store', default='doorbell', dest='database')

    argv = parser.parse_args()

    GPIO.setmode(GPIO.BOARD)

    doorbellDownstairs = Button(DOORBELL_DOWNSTAIRS, name='intercom', bouncetime=100)
    doorbellDownstairs.on_changed(handle_doorbell)

    doorbellUpstairs = Button(DOORBELL_UPSTAIRS, name='door', bouncetime=100)
    doorbellUpstairs.on_changed(handle_doorbell)

    influxdb = InfluxDBClient(argv.hostname, database=argv.database)
    influxdb.create_database(argv.database)

    try:
        print("Press CTRL+C to exit")
        while not wait_mutex.wait():
            pass
        return
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

    sys.exit(0)

def handle_doorbell(button):
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
    state = button.button_state()
    send_to_influxdb(button.name(), state)
    print(timestamp, 'The', button.name(), 'doorbell is', 'pressed' if state else 'released')

def signal_handler(signal, frame):
    global wait_mutex
    wait_mutex.set()

def send_to_influxdb(doorbell, state):
    global influxdb

    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    data = [
        {
            'measurement': 'doorbell',
            'tags': {
                'host': fqdn,
                'doorbell': doorbell,
            },
            'time': timestamp,
            'fields': {
                'state': state,
            },
        },
    ]

    influxdb.write_points(data, time_precision='u')

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()


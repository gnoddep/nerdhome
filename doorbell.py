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

    doorbellDownstairs = Button(DOORBELL_DOWNSTAIRS)
    doorbellDownstairs.set_callback(Button.PRESSED, doorbell_downstairs_pressed)
    doorbellDownstairs.set_callback(Button.RELEASED, doorbell_downstairs_released)

    doorbellUpstairs = Button(DOORBELL_UPSTAIRS)
    doorbellUpstairs.set_callback(Button.PRESSED, doorbell_upstairs_pressed)
    doorbellUpstairs.set_callback(Button.RELEASED, doorbell_upstairs_released)

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

def doorbell_downstairs_pressed(button):
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
    send_to_influxdb('intercom', 1)
    print(timestamp, 'The intercom doorbell is pressed')

def doorbell_downstairs_released(button):
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
    send_to_influxdb('intercom', 0)
    print(timestamp, 'The intercom doorbell is released')

def doorbell_upstairs_pressed(button):
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
    send_to_influxdb('door', 1)
    print(timestamp, 'The door doorbell is pressed')

def doorbell_upstairs_released(button):
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
    send_to_influxdb('door', 0)
    print(timestamp, 'The door doorbell is released')

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


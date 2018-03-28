#!/usr/bin/env python3

import sys
import signal
import threading
import re
from datetime import datetime, timezone
from argparse import ArgumentParser
from paho.mqtt.client import Client as MqttClient
from influxdb import InfluxDBClient

class MqttToInfluxdb:
    def __init__(self):
        self.wait_mutex = threading.Event()
        signal.signal(signal.SIGINT, self._signal_handler)
        self.mqtt = MqttClient()
        self.influxdb = None
        self.verbose = False

        self.doorbell_re = re.compile(r'^doorbell/(?P<name>.+)$')
        self.doorbell_state_re = re.compile(r'^(?P<state>[0-9]+):(?P<timestamp>[0-9.]+)$')

    def run(self):
        parser = ArgumentParser(description='Read data from MQTT and pass it to influxdb')
        parser.add_argument('-m', '--mqtt', action='store', default='localhost', dest='mqtt')
        parser.add_argument('-i', '--influxdb', action='store', default='localhost', dest='influxdb')
        parser.add_argument('-d', '--database', action='store', default='mqtt', dest='database')
        parser.add_argument('-v', '--verbose', action='store_true', default=False, dest='verbose')
        argv = parser.parse_args()

        self.verbose = argv.verbose

        if self.verbose:
            print('Connecting to influxdb', argv.influxdb, 'db', argv.database)

        self.influxdb = InfluxDBClient(argv.influxdb, database=argv.database)
        self.influxdb.create_database(argv.database)

        try:
            self.mqtt.on_connect = self._mqtt_on_connect

            self.mqtt.message_callback_add('doorbell/+', self._mqtt_handle_doorbell)

            self.mqtt.connect(argv.mqtt)
            self.mqtt.loop_start()

            if self.verbose:
                print("Press CTRL+C to exit")
            while not self.wait_mutex.wait():
                pass
        except KeyboardInterrupt:
            pass
        finally:
            self.mqtt.loop_stop()
            self.mqtt.disconnect()

        sys.exit(0)

    def _mqtt_on_connect(self, client, userdata, flags, rc):
        if self.verbose:
            print('Connected to MQTT:', str(rc))

        client.will_set('service/mqtt-to-influxdb', 0, qos=1, retain=True)
        client.publish('service/mqtt-to-influxdb', 1, qos=1, retain=True)

        client.subscribe('doorbell/+', qos=0)

    def _mqtt_handle_doorbell(self, client, userdata, message):
        if self.verbose:
            print(message.topic, message.payload.decode('utf-8'))

        name = self.doorbell_re.match(message.topic).group('name')

        match = self.doorbell_state_re.match(message.payload.decode('utf-8'))
        state = int(match.group('state'))
        timestamp = datetime.fromtimestamp(float(match.group('timestamp')), timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        data = [
            {
                'measurement': 'doorbell',
                'tags': {
                    'doorbell': name,
                },
                'time': timestamp,
                'fields': {
                    'state': state,
                },
            },
        ]

        if self.verbose:
            print(data)

        self.influxdb.write_points(data, time_precision='u')

    def _signal_handler(self, signal, frame):
        self.wait_mutex.set()

if __name__ == '__main__':
    MqttToInfluxdb().run()


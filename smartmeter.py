from argparse import ArgumentParser
from datetime import datetime
import json
from paho.mqtt.client import Client as MqttClient
import signal
import smeterd.meter
import threading
from time import time


class SmartMeter(object):
    def __init__(self):
        self.__verbose = False
        self.__config = {}

        self.__smeter = None

        self.__wait_mutex = threading.Event()
        signal.signal(signal.SIGINT, self.__signal_handler)

        self.__mqtt = MqttClient()

    def run(self):
        try:
            parser = ArgumentParser(description='Report the Smart Meter data to MQTT')
            parser.add_argument(
                '-c',
                '--config',
                action='store',
                default='/etc/nerdhome/smartmeter.json',
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

            device = self.__config.get('device', '/dev/ttyUSB0')
            baudrate = self.__config.get('baudrate', 115200)

            if self.__verbose:
                print('Starting SmartMeter', device, '@', baudrate)

            self.__smeter = smeterd.meter.SmartMeter(device, baudrate=baudrate)

            while not self.__wait_mutex.wait(0):
                self.__smeter.connect()
                packet = self.__smeter.read_one_packet()

                timestamp = time()

                tariff = 'high' if packet['kwh']['tariff'] == 2 else 'low'

                data = {
                    'kwh_produced': packet['kwh'][tariff]['produced'],
                    'kwh_consumed': packet['kwh'][tariff]['consumed'],
                    'current_produced': packet['kwh'][tariff]['current_produced'],
                    'current_consumed': packet['kwh'][tariff]['current_consumed'],
                    'gas_consumed': packet['gas']['total'],
                    'tags': {
                        'tariff': tariff,
                    },
                    'timestamp': timestamp,
                }

                self.__mqtt.publish('smartmeter', json.dumps(data), qos=1)

                if self.__verbose:
                    print(
                        datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S.%f'),
                        data
                    )
        except KeyboardInterrupt:
            pass
        finally:
            self.__mqtt.publish('service/smartmeter', 0, qos=1, retain=True)
            self.__mqtt.loop_stop()
            self.__mqtt.disconnect()

    def __mqtt_on_connect(self, client, userdata, flags, rc):
        if self.__verbose:
            print('Connected to MQTT:', str(rc))

        client.will_set('service/smartmeter', 0, qos=1, retain=True)
        client.publish('service/smartmeter', 1, qos=1, retain=True)

    def __signal_handler(self, signal, frame):
        self.__wait_mutex.set()


if __name__ == '__main__':
    SmartMeter().run()

#!/usr/bin/env python3

from argparse import ArgumentParser
from importlib import import_module
import signal
from threading import Event

from Nerdhome import Application
from Nerdhome import Configuration


class Nerdhome:
    verbose = 0
    configuration = None

    __applications = {}
    __exit = Event()

    def __init__(self):
        signal.signal(signal.SIGINT, self.__signal_handler)
        self.__verbose = 0
        self.__mqtt = None
        self.__influxdb = None

    def run(self):
        try:
            parser = ArgumentParser()
            parser.add_argument(
                '-c',
                '--configuration',
                action='store',
                default='/etc/nerdhome/nerdhome.json',
                help='Path to the configuration file'
            )
            parser.add_argument(
                '-v',
                '--verbose',
                action='count',
                default=0,
                help='Set verbosity level, can be used multiple times'
            )

            args = parser.parse_args()

            self.__verbose = min(3, args.verbose)
            configuration = Configuration(args.configuration)

            # Initialize the threads
            mqtt = configuration.get('mqtt', default=None)
            if mqtt is not None:
                from paho.mqtt.client import Client as MqttClient
                self.__mqtt = MqttClient()
                self.__mqtt.on_connect = self.__on_mqtt_connect

            influxdb = configuration.get('influxdb', default=None)
            if influxdb is not None:
                from Nerdhome import InfluxDB
                self.__influxdb = InfluxDB(configuration=Configuration(influxdb))

            for application, config in configuration.get('applications').items():
                self.__applications[application] = import_module(application).Application(
                    configuration=Configuration(configuration=config),
                    mqtt=self.__mqtt,
                    influxdb=self.__influxdb,
                    name=application,
                    verbose=self.__verbose
                )

                if not isinstance(self.__applications[application], Application):
                    raise NotImplementedError(application + ' is not of the right type')

            # Start the threads
            if self.__mqtt is not None:
                self.__mqtt.connect(mqtt.get('hostname', 'localhost'), port=mqtt.get('port', 1883))
                self.__mqtt.loop_start()

            if self.__influxdb is not None:
                self.__influxdb.connect()
                self.__influxdb.start()

            for name, application in self.__applications.items():
                application.start()

            # And now, we wait!
            while not self.__exit.wait(1):

                # But not without checking for live
                alive_count = 0
                for name, application in self.__applications.items():
                    if not application.is_alive():
                        if self.__verbose:
                            print('Application', name, 'is not alive anymore')

                if alive_count == 0:
                    raise RuntimeError('No active applications anymore')

            if self.__verbose:
                print('Exiting')

        except KeyboardInterrupt:
            if self.__verbose:
                print('Ctrl-C is hit')
            self.__exit.set()
        finally:
            for name, application in self.__applications.items():
                if self.__verbose:
                    print('Stopping application', name)
                application.stop()

            for name, application in self.__applications.items():
                if self.__verbose > 2:
                    print('Joining application', name)
                application.join()

            if self.__influxdb is not None:
                self.__influxdb.stop()
                self.__influxdb.join()

            if self.__mqtt is not None:
                self.__mqtt.loop_stop()
                self.__mqtt.disconnect()

            pass

    def __signal_handler(self, signum, frame):
        if self.__verbose:
            print('Caught signal', signum)
        self.__exit.set()

    def __on_mqtt_connect(self, client, userdata, flags, rc):
        if self.__verbose:
            print('Connected to MQTT')

        for name, application in self.__applications.items():
            application.on_mqtt_connect(client, userdata, flags, rc)


if __name__ == '__main__':
    Nerdhome().run()

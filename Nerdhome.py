#!/usr/bin/env python3

from argparse import ArgumentParser, FileType
from importlib import import_module
import json
import signal
from threading import Event

from Nerdhome import Application
from Nerdhome import Configuration


class Nerdhome:
    verbose = 0
    configuration = None

    __applications = {}
    __exit = Event()
    __mqtt = None

    def __init__(self):
        signal.signal(signal.SIGINT, self.__signal_handler)

    def run(self):
        try:
            parser = ArgumentParser()
            parser.add_argument(
                '-c', '--configuration',
                required=True,
                help='Path to the configuration file'
            )
            parser.add_argument(
                '-v', '--verbose',
                action='count',
                default=0,
                help='Set verbosity level, can be used multiple times'
            )

            args = parser.parse_args()

            verbose = min(3, args.verbose)
            configuration = Configuration(args.configuration)

            # Initialize the threads
            mqtt = configuration.get('mqtt', default=None)
            if mqtt is not None:
                from paho.mqtt.client import Client as MqttClient
                self.__mqtt = MqttClient()
                self.__mqtt.on_connect = self.__on_mqtt_connect

            for application, config in configuration.get('applications').items():
                self.__applications[application] = import_module(application).Application(
                    configuration=Configuration(configuration=config),
                    mqtt=self.__mqtt,
                    name=application
                )

                if not isinstance(self.__applications[application], Application):
                    raise NotImplementedError(application + ' is not of the right type')

            # Start the threads
            if self.__mqtt is not None:
                self.__mqtt.connect(mqtt['hostname'])
                self.__mqtt.loop_start()

            for name, application in self.__applications.items():
                application.start()

            # And now, we wait!
            while not self.__exit.wait(1):

                # But not without checking for live
                alive_count = 0
                for name, application in self.__applications.items():
                    if not application.is_alive():
                        if verbose:
                            print('Application', name, 'is not alive anymore')

                if alive_count == 0:
                    raise RuntimeError('No active applications anymore')
        except KeyboardInterrupt:
            self.__exit.set()
        finally:
            for name, application in self.__applications.items():
                application.stop()

            for name, application in self.__applications.items():
                application.join()

            if self.__mqtt is not None:
                self.__mqtt.loop_stop()
                self.__mqtt.disconnect()

            pass

    def __signal_handler(self, signum, frame):
        self.__exit.set()

    def __on_mqtt_connect(self, client, userdata, flags, rc):
        for name, application in self.__applications.items():
            application.on_mqtt_connect(client, userdata, flags, rc)


if __name__ == '__main__':
    Nerdhome().run()

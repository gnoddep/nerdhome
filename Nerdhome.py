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

    __exit = Event()
    __applications = {}

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

            for application, config in configuration.get('applications').items():
                self.__applications[application] = import_module(application).Application(
                    configuration=Configuration(configuration=config),
                    name=application
                )

                if not isinstance(self.__applications[application], Application):
                    raise NotImplementedError(application + ' is not of the right type')

                self.__applications[application].start()

            while not self.__exit.wait():
                pass
        except KeyboardInterrupt:
            self.__exit.set()
        finally:
            for name, application in self.__applications.items():
                application.stop()

            for name, application in self.__applications.items():
                application.join()

            pass

    def __signal_handler(self, signum, frame):
        self.__exit.set()


if __name__ == '__main__':
    Nerdhome().run()

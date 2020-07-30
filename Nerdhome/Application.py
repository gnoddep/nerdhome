import threading


class Application(threading.Thread):
    def __init__(self, configuration={}, verbose=0, mqtt=None, influxdb=None, loop_interval=None, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)

        self.__exit = threading.Event()
        self.__loop_interval = loop_interval

        self.configuration = configuration
        self.verbose = verbose
        self.mqtt = mqtt
        self.influxdb = influxdb

        self.name = kwargs.get('name', 'Unknown')

    def run(self):
        try:
            if self.verbose > 2:
                print(self.name, 'Initialize')
            self.initialize()

            while not self.wait():
                if self.verbose > 2:
                    print(self.name, 'Loop')
                self.loop()
        finally:
            if self.verbose > 2:
                print(self.name, 'Cleanup')
            self.cleanup()

    def loop(self):
        pass

    def initialize(self):
        pass

    def cleanup(self):
        pass

    def on_mqtt_connect(self, client, userdata, flags, rc):
        pass

    def wait(self):
        return self.__exit.wait(self.__loop_interval)

    def stop(self):
        self.__exit.set()

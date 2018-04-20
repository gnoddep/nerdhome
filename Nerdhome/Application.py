import threading


class Application(threading.Thread):
    def __init__(self, configuration={}, mqtt=None, loop_interval=None, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)

        self.__exit = threading.Event()
        self.__loop_interval = loop_interval

        self.configuration = configuration
        self.mqtt = mqtt

    def run(self):
        try:
            self.initialize()

            while not self.wait():
                self.loop()
        finally:
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

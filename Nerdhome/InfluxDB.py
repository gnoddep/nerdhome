from influxdb import InfluxDBClient
import threading
from queue import Queue
from copy import deepcopy


class InfluxDB(threading.Thread):
    def __init__(self, configuration, *args, **kwargs):
        super(InfluxDB, self).__init__(name='InfluxDB', *args, **kwargs)
        self.configuration = configuration

        self.__is_stopping = False
        self.__is_stopping_lock = threading.Lock()
        self.__client = None
        self.__messages = Queue(configuration.get('queue_size', default=0))

    def run(self):
        while True:
            data = self.__messages.get()
            if data is None:
                return

            self.__client.write_points(**data)
            self.__messages.task_done()

    def stop(self):
        self.is_stopping = True
        self.__messages.put(None)
        self.__messages.join()

    @property
    def is_stopping(self):
        with self.__is_stopping_lock:
            return self.__is_stopping

    @is_stopping.setter
    def is_stopping(self, status):
        with self.__is_stopping_lock:
            self.__is_stopping = status

    def connect(self):
        database = self.configuration.get('database', default='nerdhome')
        self.__client = InfluxDBClient(
            host=self.configuration.get('hostname', default='localhost'),
            database=database
        )
        self.__client.create_database(database)

    def write_points(self, points, **kwargs):
        if not self.is_stopping:
            data = deepcopy(kwargs)
            data['points'] = deepcopy(points)

            self.__messages.put(data)

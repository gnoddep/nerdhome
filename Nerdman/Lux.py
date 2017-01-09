#!/usr/bin/python

# i2c addresses
# Lux sensor        0x39

from collections import deque
import threading
import math
from Adafruit_TSL2561.TSL2561 import TSL2561

class Lux(threading.Thread):
    DEFAULT_INTERVAL = 1
    DEFAULT_LOG_SIZE = 30

    def __init__(self, interval = DEFAULT_INTERVAL, maximum_log_size = DEFAULT_LOG_SIZE):
        threading.Thread.__init__(self)
        
        self.running = threading.Event()
        self.interval = interval

        self.log = deque(maxlen = maximum_log_size)
        self.log_mutex = threading.Lock()

        self.sensor = TSL2561() # Default on 0x39
        self.sensor.begin()
        self.sensor.set_integration_time(TSL2561.TSL2561_INTEGRATIONTIME_101MS)

    def run(self):
        self._update_lux_log()
        while not self.running.wait(self.interval):
            self._update_lux_log()

    def stop(self):
        self.running.set()
        self.join()

    def get_lux(self):
        with self.log_mutex:
            weighted_lux = 0
            total_weight = 0
            index = 0

            for lux in self.log:
                index += 1

                weight = math.exp(index)
                weighted_lux += lux * weight
                total_weight += weight

            if index == 0:
                return None

            return weighted_lux / total_weight

    def _update_lux_log(self):
        lux = self.sensor.calculate_avg_lux(10)
        with self.log_mutex:
            self.log.append(lux)

    def display(self, display):
        lux = self.get_lux()

        if lux is None or lux >= 10000:
            display.set_digit(0, '-')
            display.set_digit(1, '-')
            display.set_digit(2, '-')
            display.set_digit(3, '-')
        else:
            lux = int(lux)
            display.set_digit(3, lux % 10)

            if lux >= 10:
                display.set_digit(2, int(lux / 10) % 10)

                if lux >= 100:
                    display.set_digit(1, int(lux / 100) % 10)

                    if lux >= 1000:
                        display.set_digit(0, int(lux / 1000) % 10)


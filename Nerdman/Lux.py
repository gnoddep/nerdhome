#!/usr/bin/python

# i2c addresses
# Lux sensor        0x39

from collections import deque
import threading
import Adafruit_TSL2561.TSL2561 as TSL2561

class Lux(threading.Thread):
    def __init__(self, interval = 0.5, maximum_log_size = 30):
        threading.Thread.__init__(self)
        
        self.running = threading.Event()
        self.interval = interval

        self.log = deque(maxlen = maximum_log_size)
        self.log_mutex = threading.Lock()

        self.sensor = TSL2561.TSL2561() # Default on 0x39
        self.sensor.begin()

    def run(self):
        self._update_lux_log()
        while not self.running.wait(self.interval):
            self._update_lux_log()

    def stop(self):
        self.running.set()
        self.join()

    def get_lux(self):
        with self.log_mutex:
            try:
                lux = self.log.pop()
                self.log.append(lux)
                return lux
            except IndexError:
                return None

    def _update_lux_log(self):
        lux = self.sensor.calculate_avg_lux()
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


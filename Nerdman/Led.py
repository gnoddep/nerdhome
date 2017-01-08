import threading
import RPi.GPIO as GPIO

class Led(object):
    ON = 1
    OFF = 0

    def __init__(self, gpio_pin, state = OFF):
        self._led_mutex = threading.Lock()
        self._led_gpio_pin = gpio_pin

        with self._led_mutex:
            self._led_state = state
            GPIO.setup(self._led_gpio_pin, GPIO.OUT)
            GPIO.output(self._led_gpio_pin, self._led_state)

    def led_state(self):
        with self._led_mutex:
            return GPIO.input(self._led_gpio_pin)

    def on(self):
        self._led_change_state(self.ON)

    def off(self):
        self._led_change_state(self.OFF)

    def toggle(self):
        self._led_change_state(self._led_state ^ 1)

    def _led_change_state(self, state):
        with self._led_mutex:
            self._led_state = state
            GPIO.output(self._led_gpio_pin, self._led_state)


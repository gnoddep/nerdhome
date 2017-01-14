import threading
import RPi.GPIO as GPIO

class Button(object):
    PRESSED = 1
    RELEASED = 0

    def __init__(self, gpio_pin):
        self._button_mutex = threading.Lock()
        self._button_gpio_pin = gpio_pin

        self._callbacks = [
            self._button_default_callback,
            self._button_default_callback,
        ]

        with self._button_mutex:
            GPIO.setup(self._button_gpio_pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
            self._button_state = GPIO.input(self._button_gpio_pin)
            GPIO.add_event_detect(self._button_gpio_pin, GPIO.BOTH, self._button_state_change)

    def set_callback(self, state, callback):
        with self._button_mutex:
            if callback is not None:
                self._callbacks[state] = callback
            else:
                self._callbacks[state] = self.default_button_callback

    def button_state(self):
        return self._button_state

    def _real_button_state(self):
        with self._button_mutex:
            return GPIO.input(self._button_gpio_pin)

    def _button_state_change(self, gpio_pin):
        state = self._real_button_state()
        if state != self._button_state:
            self._button_state = state
            self._callbacks[self._button_state](self)

    def _button_default_callback(self, button):
        pass

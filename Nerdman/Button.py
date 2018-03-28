import threading
import RPi.GPIO as GPIO

class Button(object):
    PRESSED = 1
    RELEASED = 0

    def __init__(self, gpio_pin, bouncetime = None, name = None):
        self._button_mutex = threading.Lock()
        self._button_gpio_pin = gpio_pin
        self._name = name

        self._callbacks = [
            self._button_default_callback,
            self._button_default_callback,
        ]

        with self._button_mutex:
            GPIO.setup(self._button_gpio_pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
            self._button_state = GPIO.input(self._button_gpio_pin)
            if bouncetime is None:
                GPIO.add_event_detect(self._button_gpio_pin, GPIO.BOTH, self._button_state_change)
            else:
                GPIO.add_event_detect(self._button_gpio_pin, GPIO.BOTH, self._button_state_change, bouncetime = bouncetime)

    def on_released(self, callback):
        with self._button_mutex:
            self._callbacks[self.RELEASED] = callback or self._button_default_callback

    def on_pressed(self, callback):
        with self._button_mutex:
            self._callbacks[self.PRESSED] = callback or self._button_default_callback

    def on_changed(self, callback):
        with self._button_mutex:
            callback = callback or self._button_default_callback
            self._callbacks[self.RELEASED] = callback
            self._callbacks[self.PRESSED] = callback

    def button_state(self):
        return self._button_state

    def name(self):
        return self._name

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

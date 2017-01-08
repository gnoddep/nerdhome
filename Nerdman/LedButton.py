import Nerdman.Button as Button
import Nerdman.Led as Led

class LedButton(Button.Button, Led.Led):
    def __init__(self, button_gpio_pin, led_gpio_pin, led_state = Led.Led.OFF):
        Button.Button.__init__(self, button_gpio_pin)
        Led.Led.__init__(self, led_gpio_pin, led_state)

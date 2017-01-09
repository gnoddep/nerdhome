# i2c addresses
# 7 segment display     0x70
# Temperature sensor    0x18
# RTC                   0x68
# Lux sensor            0x39

from datetime import datetime
import fileinput
import signal
import threading

import RPi.GPIO as GPIO

from Nerdman.RealTimeClock import RealTimeClock
from Nerdman.Temperature import Temperature
from Nerdman.Lux import Lux
from Nerdman.Display import Display
from Nerdman.LedButton import LedButton
from Nerdman.Button import Button

RTC_INTERRUPT = 26
RED_led = 23
RED_button = 24
GREEN_led = 21
GREEN_button = 22
ORANGE_led = 19
ORANGE_button = 18
BLUE_led = 15
BLUE_button = 16

temperature = None
lux = None
display = None
led_buttons = []

wait_mutex = threading.Event()

def main():
    global display
    global temperature
    global lux
    global wait_mutex
    global led_buttons

    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(RTC_INTERRUPT, GPIO.IN)
    GPIO.add_event_detect(RTC_INTERRUPT, GPIO.FALLING, callback=handle_rtc_interrupt)

    led_buttons = [
        LedButton(RED_button, RED_led),
        LedButton(GREEN_button, GREEN_led),
        LedButton(ORANGE_button, ORANGE_led),
        LedButton(BLUE_button, BLUE_led),
    ]

    for button in led_buttons:
        button.set_callback(Button.PRESSED, handle_button_action)
        button.set_callback(Button.RELEASED, handle_button_action)

    led_buttons[2].set_callback(Button.RELEASED, handle_orange_button_release)
    led_buttons[3].set_callback(Button.RELEASED, handle_blue_button_release)

    temperature = Temperature()
    lux = Lux()
    display = Display(display_time)
    rtc = RealTimeClock()

    temperature.start()
    lux.start()
    display.start()

    rtc.enable_interrupt()

    try:
        print("Press CTRL+C to exit")
        while not wait_mutex.wait():
            pass
        return
    except KeyboardInterrupt:
        pass
    finally:
        display.set_display_function(None)
        rtc.disable_interrupt()

        display.stop()
        lux.stop()
        temperature.stop()

        for led in led_buttons:
            led.off()

        GPIO.cleanup()

    sys.exit(0)

ticks = 0
state = 0
def handle_rtc_interrupt(gpio):
    global display
    global temperature
    global lux
    global ticks
    global state

    ticks += 1

    if ticks % 5 == 0:
        state += 1
        state %= 3

        if state == 1:
            display.set_display_function(temperature.display)
        elif state == 2:
            display.set_display_function(lux.display)
        else:
            display.set_display_function(display_time)

    if not display is None:
        display.update()

def display_time(display):
    now = datetime.now()

    display.set_digit(0, int(now.hour / 10))
    display.set_digit(1, now.hour % 10)

    display.set_digit(2, int(now.minute / 10))
    display.set_digit(3, now.minute % 10)

    display.set_colon(now.second & 1)

def handle_button_action(button):
    state = button.button_state()
    button._led_change_state(state)

def handle_blue_button_release(button):
    global display
    display.set_brightness(display.get_brightness() + 1)
    handle_button_action(button)

def handle_orange_button_release(button):
    global display
    display.set_brightness(display.get_brightness() - 1)
    handle_button_action(button)

def signal_handler(signal, frame):
    global wait_mutex
    wait_mutex.set()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()


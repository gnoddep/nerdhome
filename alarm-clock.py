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

import Nerdman.Temperature as Temperature
import Nerdman.Lux as Lux
import Nerdman.RealTimeClock as RealTimeClock
import Nerdman.Display as Display
import Nerdman.LedButton as LedButton
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
        LedButton.LedButton(RED_button, RED_led),
        LedButton.LedButton(GREEN_button, GREEN_led),
        LedButton.LedButton(ORANGE_button, ORANGE_led),
        LedButton.LedButton(BLUE_button, BLUE_led),
    ]

    for button in led_buttons:
        button.set_callback(Button.PRESSED, handle_button_action)
        button.set_callback(Button.RELEASED, handle_button_action)

    temperature = Temperature.Temperature()
    lux = Lux.Lux()
    display = Display.Display(display_time)

    temperature.start()
    lux.start()
    display.start()

    rtc = RealTimeClock.RealTimeClock()
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

def signal_handler(signal, frame):
    global wait_mutex
    wait_mutex.set()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()


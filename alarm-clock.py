# i2c addresses
# 7 segment display     0x70
# Temperature sensor    0x18
# RTC                   0x68
# Lux sensor            0x39
# Amplifier             0x4B

from time import time
from datetime import datetime
import fileinput
import signal
import threading

import RPi.GPIO as GPIO

from Nerdman.RealTimeClock import RealTimeClock
from Nerdman.Temperature import Temperature
from Nerdman.Lux import Lux
from Nerdman.Display_Matrix import Display_Matrix
from Nerdman.LedButton import LedButton
from Nerdman.Button import Button
from Nerdman.Font.Fixed_6x8 import Fixed_6x8

RTC_INTERRUPT = 7
MUTE = 11
RED_led = 32
RED_button = 31
GREEN_led = 35
GREEN_button = 33
ORANGE_led = 40
ORANGE_button = 38
BLUE_led = 37
BLUE_button = 36

temperature = None
lux = None
display = None
rtc = None
led_buttons = []

wait_mutex = threading.Event()

font = Fixed_6x8()

def main():
    global display
    global temperature
    global lux
    global wait_mutex
    global led_buttons
    global rtc

    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(RTC_INTERRUPT, GPIO.IN)
    GPIO.add_event_detect(RTC_INTERRUPT, GPIO.FALLING, callback=handle_rtc_interrupt)

    GPIO.setup(MUTE, GPIO.OUT)
    GPIO.output(MUTE, 0)

    led_buttons = [
        LedButton(RED_button, RED_led),
        LedButton(GREEN_button, GREEN_led),
        LedButton(ORANGE_button, ORANGE_led),
        LedButton(BLUE_button, BLUE_led),
    ]

    for button in led_buttons:
        button.set_callback(Button.PRESSED, handle_button_action)
        button.set_callback(Button.RELEASED, handle_button_action)

    led_buttons[0].set_callback(Button.PRESSED, None)
    led_buttons[0].set_callback(Button.RELEASED, handle_toggle_mute)

    temperature = Temperature()
    lux = Lux()
    display = Display_Matrix(display_handler)
    rtc = RealTimeClock()

    temperature.start()
    lux.start()
    display.start()
    display.set_brightness(0x0)

    rtc.enable_interrupt(RealTimeClock.FREQ_4096HZ)

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
cur_time = 0
def handle_rtc_interrupt(gpio):
    global display
    global temperature
    global lux
    global rtc
    global ticks
    global cur_time

    ticks += 1

    if ticks % 200 == 0 and not display is None:
        new_time = int(time())

        if cur_time != new_time:
            cur_time = new_time
            display.update()

def display_handler(display):
    display.clear()
    display_time(display)

def display_time(display):
    global font

    now = datetime.now()

    hour = font.string('{:02d}'.format(now.hour))
    minute = font.string('{:02d}'.format(now.minute))

    for y in range(0, len(hour)):
        for x in range(0, len(hour[y])):
            if hour[y][x]:
                display.set_pixel(0 + x, y, display.RED)
            if minute[y][x]:
                display.set_pixel(14 + x, y, display.RED)

    if now.second & 1:
        display.set_pixel(12, 1, display.RED)
        display.set_pixel(12, 2, display.RED)

        display.set_pixel(12, 4, display.RED)
        display.set_pixel(12, 5, display.RED)

def handle_button_action(button):
    state = button.button_state()
    button._led_change_state(state)

def handle_toggle_mute(button):
    mute_state = GPIO.input(MUTE) ^ 1;
    GPIO.output(MUTE, mute_state)
    button._led_change_state(mute_state)

def signal_handler(signal, frame):
    global wait_mutex
    wait_mutex.set()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()


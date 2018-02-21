# i2c addresses
# 7 segment display     0x70
# Temperature sensor    0x18
# RTC                   0x68
# Lux sensor            0x39

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
    global image

    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(RTC_INTERRUPT, GPIO.IN, )
    GPIO.add_event_detect(RTC_INTERRUPT, GPIO.FALLING, callback=handle_rtc_interrupt)

#    led_buttons = [
#        LedButton(RED_button, RED_led),
#        LedButton(GREEN_button, GREEN_led),
#        LedButton(ORANGE_button, ORANGE_led),
#        LedButton(BLUE_button, BLUE_led),
#    ]

#    for button in led_buttons:
#        button.set_callback(Button.PRESSED, handle_button_action)
#        button.set_callback(Button.RELEASED, handle_button_action)

#    led_buttons[2].set_callback(Button.RELEASED, handle_orange_button_release)
#    led_buttons[3].set_callback(Button.RELEASED, handle_blue_button_release)

    temperature = Temperature()
    lux = Lux()
    display = Display_Matrix(display_time)
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

#        for led in led_buttons:
#            led.off()

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

def display_time(display):
    global font

    now = datetime.now()
    bitmap = font.string('{:02d}:{:02d}:{:02d}'.format(now.hour, now.minute, now.second))

    display.clear()

    for y in range(0, len(bitmap)):
        for x in range(0, len(bitmap[y])):
            if bitmap[y][x]:
                display.set_pixel(2 + x, y, display.RED)

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


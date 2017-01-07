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

RTC_INTERRUPT = 26
RED_led = 23
RED_button = 24
GREEN_led = 21
GREEN_button = 22
ORANGE_led = 19
ORANGE_button = 18
BLUE_led = 15
BLUE_button = 16

button_led_map = {
        RED_button: {'led': RED_led, 'status': 0},
        GREEN_button: {'led': GREEN_led, 'status': 0},
        ORANGE_button: {'led': ORANGE_led, 'status' : 0},
        BLUE_button: {'led': BLUE_led, 'status': 0},
    }

temperature = None
lux = None
display = None
wait_mutex = threading.Event()

def main():
    global display
    global temperature
    global lux
    global wait_mutex

    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(RTC_INTERRUPT, GPIO.IN)
    GPIO.add_event_detect(RTC_INTERRUPT, GPIO.FALLING, callback=handle_rtc_interrupt)

    for button, led in button_led_map.items():
        GPIO.setup(led['led'], GPIO.OUT)
        GPIO.output(led['led'], led['status'])

        GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(button, GPIO.BOTH, callback=handle_button_action)

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

        for button, led in button_led_map.items():
            GPIO.output(led['led'], 0)

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
    global button_led_map

    gpio = GPIO.input(button)
    if gpio != button_led_map[button]['status']:
        button_led_map[button]['status'] = gpio
        GPIO.output(button_led_map[button]['led'], button_led_map[button]['status'])

def signal_handler(signal, frame):
    global wait_mutex
    wait_mutex.set()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()


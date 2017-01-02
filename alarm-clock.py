#!/usr/bin/python

# i2c addresses
# 7 segment display     0x70
# Temperature sensor    0x18
# RTC                   0x68
# Lux sensor            0x39

# Bitmap for the 7-segment digits
# bit 1 (0x01) - top horizontal
# bit 2 (0x02) - top right vertical
# bit 3 (0x04) - bottom right vertical
# bit 4 (0x08) - bottom horizontal
# bit 5 (0x10) - bottom left vertical
# bit 6 (0x20) - top left vertical
# bit 7 (0x40) - middle vertical

import signal
import sys
import time
import datetime

import RPi.GPIO as GPIO

from Adafruit_LED_Backpack import SevenSegment
import Adafruit_TSL2561.TSL2561 as TSL2561

import Nerdman.Temperature as Temperature

segment = None
temperature = None

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

def main():
    global segment
    global temperature

    signal.signal(signal.SIGINT, signal_handler)

    GPIO.setmode(GPIO.BOARD)

    for button, led in button_led_map.iteritems():
        GPIO.setup(led['led'], GPIO.OUT)
        GPIO.output(led['led'], led['status'])
    
        GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(button, GPIO.BOTH, callback=handle_button_action)

    # Initialize the display. Must be called once before using the display.
    segment = SevenSegment.SevenSegment(address = 0x70)
    segment.begin()
    segment.set_brightness(0x00)

    temperature = Temperature.Temperature()
    temperature.start()

    lux_sensor = TSL2561.TSL2561() # Default on 0x39
    lux_sensor.begin()

    print "Press CTRL+C to exit"

    toggle = 0
    can_toggle = 1

    n = 0

    # Continually update the time on a 4 char, 7-segment display
    while (True):
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute
        second = now.second

        if can_toggle == 1 and second % 5 == 0:
            toggle = (toggle + 1) % 3
            can_toggle = 0
        elif can_toggle == 0 and second % 5 != 0:
            can_toggle = 1

        segment.clear()

        if toggle == 0:
            # Set hours
            segment.set_digit(0, int(hour / 10))     # Tens
            segment.set_digit(1, hour % 10)          # Ones
            # Set minutes
            segment.set_digit(2, int(minute / 10))   # Tens
            segment.set_digit(3, minute % 10)        # Ones
            # Toggle colon
            segment.set_colon(second % 2)              # Toggle colon at 1Hz
        elif toggle == 1:
            temp = temperature.get_temperature()
            if not temp is None:
                segment.set_digit(1, int(temp / 10))
                segment.set_digit(2, int(temp % 10))
            else:
                segment.set_digit(1, '-')
                segment.set_digit(2, '-')
            segment.set_digit_raw(3, 0x01 | 0x20 | 0x40)
            segment.set_fixed_decimal(True)
        elif toggle == 2:
            lux = int(lux_sensor.calculate_avg_lux())
            if lux >= 10000:
                segment.set_digit(0, '-')
                segment.set_digit(1, '-')
                segment.set_digit(2, '-')
                segment.set_digit(3, '-')
            else:
                segment.set_digit(3, lux % 10)

                if lux >= 10:
                    segment.set_digit(2, int(lux / 10) % 10)

                    if lux >= 100:
                        segment.set_digit(1, int(lux / 100) % 10)

                        if lux >= 1000:
                            segment.set_digit(0, int(lux / 1000) % 10)


        # Write the display buffer to the hardware.  This must be called to
        # update the actual display LEDs.
        segment.write_display()

        # Wait a quarter second (less than 1 second to prevent colon blinking getting$
        time.sleep(0.25)

def signal_handler(signal, frame):
    global segment
    global temperature

    if not segment is None:
        segment.clear()
        segment.write_display()

    temperature.stop()

    GPIO.output(RED_led, 0)
    GPIO.cleanup()

    sys.exit(0)

def handle_button_action(button):
    global button_led_map

    gpio = GPIO.input(button)
    if gpio != button_led_map[button]['status']:
        button_led_map[button]['status'] = gpio
        GPIO.output(button_led_map[button]['led'], button_led_map[button]['status'])

if __name__ == '__main__':
    main()


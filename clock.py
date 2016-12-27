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
import Adafruit_MCP9808.MCP9808 as MCP9808

segment = None
temp_sensor = None
led_status = 0

def main():
    global segment
    global temp_sensor
    global led_status

    signal.signal(signal.SIGINT, signal_handler)

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(15, GPIO.OUT)
    GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.output(15, led_status)
    
    GPIO.add_event_detect(18, GPIO.BOTH, callback=handle_button_action)

    # Initialize the display. Must be called once before using the display.
    segment = SevenSegment.SevenSegment(address = 0x70)
    segment.begin()
    segment.set_brightness(0x00)

    temp_sensor = MCP9808.MCP9808() # Default on 0x18
    temp_sensor.begin()

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

        if can_toggle == 1 and second % 10 == 0:
            toggle = toggle ^ 1
            can_toggle = 0
        elif can_toggle == 0 and second % 10 != 0:
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
        else:
            temp = temp_sensor.readTempC()
            segment.set_digit(1, int(temp / 10))
            segment.set_digit(2, int(temp % 10))
            segment.set_digit_raw(3, 0x01 | 0x20 | 0x40)
            segment.set_fixed_decimal(True)

        # Write the display buffer to the hardware.  This must be called to
        # update the actual display LEDs.
        segment.write_display()

        # Wait a quarter second (less than 1 second to prevent colon blinking getting$
        time.sleep(0.25)

def signal_handler(signal, frame):
    global segment
    if not segment is None:
        segment.clear()
        segment.write_display()

    GPIO.output(15, 0)
    GPIO.cleanup()

    sys.exit(0)

def handle_button_action(channel):
    global led_status
    gpio = GPIO.input(18)
    if gpio != led_status:
        led_status = gpio
        GPIO.output(15, led_status)

if __name__ == '__main__':
    main()


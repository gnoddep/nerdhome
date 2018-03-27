#!/usr/bin/env python3

import signal
import threading
from datetime import datetime

import RPi.GPIO as GPIO
from Nerdman.Button import Button

DOORBELL_DOWNSTAIRS = 18
DOORBELL_UPSTAIRS = 15

wait_mutex = threading.Event()

def main():
    global buttons

    GPIO.setmode(GPIO.BOARD)

    doorbellDownstairs = Button(DOORBELL_DOWNSTAIRS)
    doorbellDownstairs.set_callback(Button.PRESSED, doorbell_downstairs_pressed)
    doorbellDownstairs.set_callback(Button.RELEASED, doorbell_downstairs_released)

    doorbellUpstairs = Button(DOORBELL_UPSTAIRS)
    doorbellUpstairs.set_callback(Button.PRESSED, doorbell_upstairs_pressed)
    doorbellUpstairs.set_callback(Button.RELEASED, doorbell_upstairs_released)

    try:
        print("Press CTRL+C to exit")
        while not wait_mutex.wait():
            pass
        return
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

    sys.exit(0)

def doorbell_downstairs_pressed(button):
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    print(timestamp, 'The doorbell downstairs is pressed')

def doorbell_downstairs_released(button):
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    print(timestamp, 'The doorbell downstairs is released')

def doorbell_upstairs_pressed(button):
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    print(timestamp, 'The doorbell upstairs is pressed')

def doorbell_upstairs_released(button):
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    print(timestamp, 'The doorbell upstairs is released')

def signal_handler(signal, frame):
    global wait_mutex
    wait_mutex.set()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()


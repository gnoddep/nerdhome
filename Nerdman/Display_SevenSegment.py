import threading

# 7 segment display     0x70

# Bitmap for the 7-segment digits
# bit 1 (0x01) - top horizontal
# bit 2 (0x02) - top right vertical
# bit 3 (0x04) - bottom right vertical
# bit 4 (0x08) - bottom horizontal
# bit 5 (0x10) - bottom left vertical
# bit 6 (0x20) - top left vertical
# bit 7 (0x40) - middle vertical

import sys
from datetime import datetime
from Adafruit_LED_Backpack import SevenSegment

class Display(threading.Thread):
    def __init__(self, display_function = None):
        threading.Thread.__init__(self)

        self.wait_for_update = threading.Event()
        self.brightness = 0x00

        self.running = False

        self.display = SevenSegment.SevenSegment()
        self.display.begin()

        self.display_function = display_function

    def run(self):
        self.running = True
        while self.wait_for_update.wait():
            self.wait_for_update.clear()

            if not self.running:
                break

            self.display.clear()
            self.display.set_brightness(self.brightness)

            if not self.display_function is None:
                self.display_function(self.display)

            self.display.write_display()


    def update(self):
        self.wait_for_update.set()

    def stop(self):
        self.running = False
        self.update()

        self.join()

        self.display.clear()
        self.display.write_display()

    def set_brightness(self, brightness):
        self.brightness = min(max(brightness, 0), 0x0F)
        self.update()

    def get_brightness(self):
        return self.brightness

    def set_display_function(self, display_function):
        self.display_function = display_function
        self.update()


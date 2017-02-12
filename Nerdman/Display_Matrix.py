import threading

# 8x8 matrix display's      0x70, 0x71, 0x72, 0x73, 0x74, 0x75

import sys
import time
from datetime import datetime
from Adafruit_LED_Backpack import HT16K33

class Display_Matrix(threading.Thread):
    OFF = 0x00
    GREEN = 0x01
    RED = 0x02
    YELLOW = 0x03

    def __init__(self, display_function = None):
        threading.Thread.__init__(self)

        self.wait_for_update = threading.Event()
        self.brightness = 0x00

        self.running = False

        self.bitmap = [
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
        ]
        self.displays = []

#        for address in [0x70, 0x71, 0x72, 0x73, 0x74, 0x75]:
        for address in [0x70, 0x71, 0x72]:
            display = {'display': None, 'map': []}
            display['display'] = HT16K33.HT16K33(address=address)
            display['display'].begin()

            multiplier = len(self.displays)

            for y in range(8):
                self.bitmap[y].extend([0, 0, 0, 0, 0, 0, 0, 0])
                for x in range(8):
                    # The 0,0 point of the matrix is rotated 90 degrees clockwise
                    display['map'].append({'x': x + 8 * multiplier, 'y': y, 'led': (7 - x) * 16 + y})

            self.displays.append(display)

        self.display_function = display_function

    def run(self):
        self.running = True
        while self.wait_for_update.wait():
            self.wait_for_update.clear()

            if not self.running:
                break

            if not self.display_function is None:
                self.display_function(self)

            for display in self.displays:
                display['display'].clear()
                display['display'].set_brightness(self.brightness)

                for i in display['map']:
                    display['display'].set_led(i['led'], 1 if self.bitmap[i['y']][i['x']] & self.GREEN else 0)
                    display['display'].set_led(i['led'] + 8, 1 if self.bitmap[i['y']][i['x']] & self.RED else 0)

                display['display'].write_display()

    def update(self):
        self.wait_for_update.set()

    def stop(self):
        self.running = False
        self.update()

        self.join()

        for display in self.displays:
            display['display'].clear()
            display['display'].write_display()

    def set_brightness(self, brightness):
        self.brightness = min(max(brightness, 0), 0x0F)
        self.update()

    def get_brightness(self):
        return self.brightness

    def clear(self):
        for row in self.bitmap:
            for x, value in enumerate(row):
                row[x] = self.OFF

    def set_pixel(self, x, y, colour):
        self.bitmap[y][x] = colour

    def set_display_function(self, display_function):
        self.display_function = display_function
        self.update()


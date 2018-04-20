from time import localtime

from Nerdhome import Application
from Nerdman.Display_SevenSegment import Display_SevenSegment


class AlarmClock(Application):
    def __init__(self, *args, **kwargs):
        super(AlarmClock, self).__init__(loop_interval=0.1, *args, **kwargs)
        self.__display = None

    def initialize(self):
        self.__display = Display_SevenSegment(
            self.__display_handler,
            address=self.configuration.get('SevenSegment', 'i2c_address', default=0x77)
        )

        self.__display.start()
        self.__display.set_brightness(self.configuration.get('SevenSegment', 'brightness', default=0x00))

    def cleanup(self):
        if self.__display is not None:
            self.__display.set_display_function(None)
            self.__display.stop()

    def loop(self):
        self.__display.update()

    @staticmethod
    def __display_handler(display):
        display.clear()

        now = localtime()

        display.set_digit(0, int(now.tm_hour / 10))
        display.set_digit(1, int(now.tm_hour % 10))
        display.set_digit(2, int(now.tm_min / 10))
        display.set_digit(3, int(now.tm_min % 10))

        display.set_colon(now.tm_sec & 1)

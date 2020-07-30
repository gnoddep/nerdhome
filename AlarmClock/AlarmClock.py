from time import localtime
import signal
import threading

from Nerdman.Display_SevenSegment import Display_SevenSegment


class AlarmClock(object):
    def __init__(self):
        self.__config = {}
        self.__display = None

        self.__wait_mutex = threading.Event()
        signal.signal(signal.SIGINT, self.__signal_handler)

    def run(self):
        try:
            self.__display = Display_SevenSegment(
                self.__display_handler,
                address=self.__config.get('SevenSegment', {}).get('i2c_address', 0x77)
            )

            self.__display.start()
            self.__display.set_brightness(self.__config.get('SevenSegment', {}).get('brightness', 0x00))

            while self.__wait_mutex.wait(0.1):
                self.__display.update()
        except KeyboardInterrupt:
            pass
        finally:
            if self.__display is not None:
                self.__display.set_display_function(None)
                self.__display.stop()

    @staticmethod
    def __display_handler(display):
        display.clear()

        now = localtime()

        display.set_digit(0, int(now.tm_hour / 10))
        display.set_digit(1, int(now.tm_hour % 10))
        display.set_digit(2, int(now.tm_min / 10))
        display.set_digit(3, int(now.tm_min % 10))

        display.set_colon(now.tm_sec & 1)

    def __signal_handler(self, signal, frame):
        self.__wait_mutex.set()


if __name__ == '__main__':
    AlarmClock().run()

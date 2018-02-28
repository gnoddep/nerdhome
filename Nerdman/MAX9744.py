import threading

MAX9744_ADDRESS = 0x4B

class MAX9744(object):
    MAX_VOLUME = 0x3F

    def __init__(self, address=MAX9744_ADDRESS, i2c=None, **kwargs):
        if i2c is None:
            import Adafruit_GPIO.I2C as I2C
            i2c = I2C

        self._device = i2c.get_i2c_device(address, **kwargs)
        self._volume_lock = threading.Lock()
        self.set_volume(0)

    def set_volume(self, volume):
        if volume < 0:
            volume = 0
        elif volume > self.MAX_VOLUME:
            volume = self.MAX_VOLUME

        with self._volume_lock:
            self._device.writeRaw8(volume & self.MAX_VOLUME)
            self._volume = volume

    def get_volume(self):
        with self._volume_lock:
            return self._volume


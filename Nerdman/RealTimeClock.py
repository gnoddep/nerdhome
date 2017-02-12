import fcntl
import array

class RealTimeClock(object):
    DS1307_ENABLE_SQW = 0x40046400;
    DS1307_DISABLE_SQW = 0x00006401;
    DS1307_SQW_STATUS = 0x80046402;

    DS1307_BIT_SQWE = 0x10
    DS1307_FREQUENCIES = [
        1,
        4096,
        8092,
        32768
    ]

    DEFAULT_FREQUENCY = 1

    def __init__(self, device = '/dev/ds1307/sqw'):
        self._device = device

    def enable_interrupt(self, frequency = DEFAULT_FREQUENCY):
        with open(self._device, 'w') as rtc:
            fcntl.ioctl(rtc, self.DS1307_ENABLE_SQW, frequency)

    def disable_interrupt(self):
        with open(self._device, 'w') as rtc:
            fcntl.ioctl(rtc, self.DS1307_DISABLE_SQW)

    def sqw_status(self):
        with open(self._device, 'w') as rtc:
            buf = array.array('I', [0])
            fcntl.ioctl(rtc, self.DS1307_SQW_STATUS, buf, True)

            control = buf[0]

            return {
                'enabled': control & self.DS1307_BIT_SQWE == self.DS1307_BIT_SQWE,
                'frequency': self.DS1307_FREQUENCIES[control & 0x03]
            }


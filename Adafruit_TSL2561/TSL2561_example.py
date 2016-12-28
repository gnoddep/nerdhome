#!/usr/bin/python
#
# Copyright (c) 2015 Iain Colledge for Adafruit Industries
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
"""
Python library for the TSL2561 digital luminosity (light) sensors.

This library is heavily based on the Arduino library for the TSL2561 digital
luminosity (light) sensors. It is basically a simple translation from C++ to
Python.

The thread on the Adafruit forum helped a lot to do this.  Thanks to static,
huelke, pandring, adafruit_support_rick, scortier, bryand, csalty, lenos and
of course to Adafruit

Source for the Arduino library:
https://github.com/adafruit/TSL2561-Arduino-Library

Adafruit forum thread:
http://forums.adafruit.com/viewtopic.php?f=8&t=34922&sid=8336d566f2f03c25882aaf34c8a15a92

Original code posted here:
http://forums.adafruit.com/viewtopic.php?f=8&t=34922&start=75#p222877

This was checked against a 10 UKP lux meter from Amazon and was withing 10% up
and down the range, the meter had a stated accuracy of 5% but then again, 10
UKP meter.

Changelog:

1.3 - Make it work with the current Adafruit_GPIO library - Peter Gnodde
    Use Adafruit_GPIO.I2C
    Removed logging statements
1.2 - Additional clean-up - Chris Satterlee
    Added underscore back into class name
    Removed unnecessary inheritance from Adafruit_I2C
    Removed vestigial trailing */ from comments
    Removed (now unnecessary) autogain hack
    Fold (most) long lines to comply with col 80 limit
    Added BSD license header comment
1.1 - Fixes from
      https://forums.adafruit.com/viewtopic.php?f=8&t=34922&p=430795#p430782
      - Iain Colledge
    Bug #1: The class name has the middle two digits transposed -
            Adafruit_TSL2651 should be Adafruit_TSL2561
    Bug #2: The read8 and read16 methods (functions) call the I2C readS8 and
            readS16 methods respectively.  They should call the readU8 and
            readU16 (i.e. unsigned) methods.
    Minor fixes and changes due to Pycharm and SonarQube recommendations, it
      looks like Python more than C++ now
    Added Exception thrown on sensor saturation
1.0 - Initial release - Iain Colledge
    Removed commented out C++ code
    Added calculate_avg_lux
    Changed main method to use calculate_avg_lux and loop argument support
       added.
    Ported "Extended delays to take into account loose timing with 'delay'"
       update from CPP code
    Added hack so that with autogain every sample goes from 1x to 16x as going
       from 16x to 1x does not work
"""

from TSL2561 import TSL2561
import sys

if __name__ == "__main__":
    LightSensor = TSL2561()
    LightSensor.enable_auto_gain(True)

    # See if "loop" has been passed as an arg.
    try:
        arg = sys.argv[1]
        if arg == "loop":
            while True:
                try:
                    print(int(LightSensor.calculate_avg_lux()))
                except OverflowError as e:
                    print(e)
                except KeyboardInterrupt:
                    quit()
        else:
            print("Invalid arg(s):", sys.argv[1])
    except IndexError:
        print(int(LightSensor.calculate_avg_lux()))

from datetime import datetime
import json
from time import time

import RPi.GPIO as GPIO
from Nerdman.LedButton import LedButton
from Doorbell.Doorbell import Doorbell

import Nerdhome.Application


class Application(Nerdhome.Application):
    INTERCOM_BUTTON = 18
    DOOR_BUTTON = 15

    INTERCOM_RELAY = 40
    DOOR_RELAY = 38

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        self.doorbell = None
        self.verbose = False

    def initialize(self):
        self.verbose = self.configuration.get('verbose', default=False)

        GPIO.setmode(GPIO.BOARD)

        door = LedButton(self.DOOR_BUTTON, self.DOOR_RELAY, name='door')
        door.on_changed(self._handle_doorbell)

        intercom = LedButton(self.INTERCOM_BUTTON, self.INTERCOM_RELAY, name='intercom')
        intercom.on_changed(self._handle_doorbell)

        self.doorbell = Doorbell(self.verbose)
        self.doorbell.start()

        if self.verbose:
            print("Press CTRL+C to exit")

    def cleanup(self):
        if not self.doorbell is None:
            self.doorbell.stop()
        self.mqtt.publish('service/doorbell', 0, qos=1, retain=True)
        GPIO.cleanup()

    def _handle_doorbell(self, button):
        timestamp = time()
        state = 'ON' if button.button_state() == LedButton.PRESSED else 'OFF'
        self.mqtt.publish(
            'doorbell/' + button.name(),
            json.dumps({'state': state, 'timestamp': timestamp}),
            qos=1,
            retain=True
        )

        if state:
            self.doorbell.ring(button, 1 if button.name() == 'door' else 3)

        if self.verbose:
            print(
                datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S.%f'),
                'The', button.name(), 'doorbell is', 'pressed' if state else 'released'
            )

    def on_mqtt_connect(self, client, userdata, flags, rc):
        if self.verbose:
            print('Connected to MQTT:', str(rc))

        client.will_set('service/doorbell', 0, qos=1, retain=True)
        client.publish('service/doorbell', 1, qos=1, retain=True)

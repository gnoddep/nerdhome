#!/usr/bin/env python3

from datetime import datetime
from dateutil import tz
import gi
import json
import os
from paho.mqtt.client import Client as MqttClient
import re
import signal
from typing import Optional

gi.require_version('AppIndicator3', '0.1')
gi.require_version('Gtk', '3.0')
gi.require_version('GSound', '1.0')
gi.require_version('Notify', '0.7')

from gi.repository import AppIndicator3, Gtk, GSound, Notify

APP_NAME = 'Nerdhome'
WERKKAMER_LIGHTING_MAIN_TOPIC = 'zigbee2mqtt/werkkamer/lighting/main'


class NerdhomeNotify(object):
    doorbell_re = re.compile(r'^doorbell/(?P<name>.+)$')

    def __init__(self):
        with open(self.__path('notify.json'), 'r') as fd:
            self.__configuration = json.load(fd)

        self.__indicator = AppIndicator3.Indicator.new(
            APP_NAME,
            self.__path('icons/house-user.svg'),
            AppIndicator3.IndicatorCategory.OTHER
        )

        Notify.init(APP_NAME)
        self.__status_item = Gtk.MenuItem(label='Not connected')
        self.__status_item.set_sensitive(False)

        self.__werkkamer_lighting_state = None
        self.__werkkamer_lighting = Gtk.MenuItem(label='Lights Werkkamer (?)')
        self.__werkkamer_lighting.connect('activate', self.toggle_lights_werkkamer)

        self.__gsound = GSound.Context()

        self.__mqtt = MqttClient()

    def indicator(self):
        menu = Gtk.Menu()

        menu.append(self.__status_item)
        menu.append(Gtk.SeparatorMenuItem())

        menu.append(self.__werkkamer_lighting)
        menu.append(Gtk.SeparatorMenuItem())

        item_quit = Gtk.MenuItem(label='Quit')
        item_quit.connect('activate', self.quit)
        menu.append(item_quit)

        menu.show_all()

        self.__indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.__indicator.set_menu(menu)

    def notification(
            self,
            summary: str,
            body: Optional[str] = None,
            icon: Optional[str] = None,
            urgency: Optional[Notify.Urgency] = Notify.Urgency.NORMAL
    ):
        notification = Notify.Notification.new(summary, body, icon or self.__path('icons/house-user-inverted.svg'))
        notification.set_urgency(urgency)
        notification.show()

    def play_sound(self, path: str):
        self.__gsound.play_simple({'media.filename': self.__path(path)})

    def __mqtt_on_connect(self, client, userdata, flags, rc):
        self.__status_item.set_label(f'Connected to {client._host}')
        self.__status_item.set_sensitive(True)
        client.subscribe('doorbell/+', qos=0)

        client.subscribe(WERKKAMER_LIGHTING_MAIN_TOPIC, qos=0)
        client.publish(WERKKAMER_LIGHTING_MAIN_TOPIC + '/get')

    def __mqtt_on_disconnect(self, *args, **kwargs):
        self.__status_item.set_label(f'Not connected')
        self.__status_item.set_sensitive(False)

    def __mqtt_handle_doorbell(self, client, userdata, message):
        try:
            data = json.loads(message.payload.decode('utf-8'))
        except json.JSONDecodeError:
            return

        name = NerdhomeNotify.doorbell_re.match(message.topic).group('name')

        state = data['state'].lower() == 'on'
        utc = datetime.utcfromtimestamp(data['timestamp']).replace(tzinfo=tz.tzutc())
        timestamp = utc.astimezone(tz.tzlocal())

        if state:
            self.notification(
                '**tring** **tring** **TRING**',
                f'The {name} doorbell is ringing! ({timestamp})',
                urgency=Notify.Urgency.CRITICAL
            )
            if name == 'door':
                self.play_sound('bells/ringlong.ogg')
            elif name == 'intercom':
                self.play_sound('bells/ringrep3.ogg')
            elif name == 'test':
                self.play_sound('bells/3tone.ogg')

    def __mqtt_handle_lights_werkkamer(self, client, userdata, message):
        message = json.loads(message.payload.decode('utf-8'))
        self.__werkkamer_lighting_state = message['state'].lower()
        self.__werkkamer_lighting.set_label('Werkkamer Lighting (' + self.__werkkamer_lighting_state + ')')

    def toggle_lights_werkkamer(self, *args, **kwargs):
        if self.__werkkamer_lighting_state == 'on':
            self.__mqtt.publish(WERKKAMER_LIGHTING_MAIN_TOPIC + '/set/state', 'OFF')
        elif self.__werkkamer_lighting_state == 'off':
            self.__mqtt.publish(WERKKAMER_LIGHTING_MAIN_TOPIC + '/set/state', 'ON')

    def quit(self, *args, **kwargs):
        Notify.uninit()

        self.__mqtt.loop_stop()
        self.__mqtt.disconnect()

        Gtk.main_quit()

    def run(self):
        self.__mqtt.on_connect = self.__mqtt_on_connect
        self.__mqtt.on_disconnect = self.__mqtt_on_disconnect
        self.__mqtt.message_callback_add('doorbell/+', self.__mqtt_handle_doorbell)
        self.__mqtt.message_callback_add(WERKKAMER_LIGHTING_MAIN_TOPIC, self.__mqtt_handle_lights_werkkamer)
        self.__mqtt.connect(self.__configuration['mqtt']['hostname'])
        self.__mqtt.loop_start()

        self.__gsound.init()
        self.indicator()
        Gtk.main()

    def __path(self, path: str) -> str:
        return os.path.realpath(os.path.join(os.path.dirname(__file__), path))


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    NerdhomeNotify().run()

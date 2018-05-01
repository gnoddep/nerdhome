import smeterd.meter
from datetime import datetime

from Nerdhome import Application


class SmartMeter(Application):
    def __init__(self, *args, **kwargs):
        # Loop interval can be 0, because the smart meter itself will limit the rate
        super(SmartMeter, self).__init__(loop_interval=0, *args, **kwargs)
        self.verbose = False
        self.smeter = None

    def initialize(self):
        self.verbose = self.configuration.get('verbose', default=False)

        device = self.configuration.get('device', default='/dev/ttyUSB0')
        baudrate = self.configuration.get('baudrate', default=115200)

        if self.verbose:
            print('Starting SmartMeter', device, '@', baudrate)

        self.smeter = smeterd.meter.SmartMeter(device, baudrate=baudrate)

        hostname = self.configuration.get('influxdb.hostname', default='localhost')
        database = self.configuration.get('influxdb.database', default='smartmeter')

        if self.verbose:
            print('Connecting to influxdb', hostname, 'db', database)

    def cleanup(self):
        self.mqtt.publish('service/smartmeter', 0, qos=1, retain=True)

    def loop(self):
        self.smeter.connect()
        packet = self.smeter.read_one_packet()

        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        tariff = 'high' if packet['kwh']['tariff'] == 2 else 'low'

        data = [
            {
                'measurement': 'energy_kwh',
                'tags': {
                    'tariff': tariff,
                },
                'time': timestamp,
                'fields': {
                    'produced': packet['kwh'][tariff]['produced'],
                    'consumed': packet['kwh'][tariff]['consumed'],
                },
            },
            {
                'measurement': 'energy_current',
                'time': timestamp,
                'fields': {
                    'consumed': packet['kwh']['current_consumed'],
                    'produced': packet['kwh']['current_produced'],
                },
            },
            {
                'measurement': 'energy_gas',
                'time': timestamp,
                'fields': {
                    'consumed': packet['gas']['total'],
                },
            },
        ]

        if self.verbose:
            print(data)

        self.influxdb.write_points(data, time_precision='s')

    def on_mqtt_connect(self, client, userdata, flags, rc):
        if self.verbose:
            print('Connected to MQTT:', str(rc))

        client.will_set('service/smartmeter', 0, qos=1, retain=True)
        client.publish('service/smartmeter', 1, qos=1, retain=True)

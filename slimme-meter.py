from smeterd.meter import SmartMeter
from influxdb import InfluxDBClient
from socket import getfqdn
from time import sleep
from datetime import datetime
from argparse import ArgumentParser

parser = ArgumentParser(description='Read data from the smart meter and send it to influxdb')
parser.add_argument('-t', '--device', action='store', default='/dev/ttyUSB0', dest='device')
parser.add_argument('-b', '--baudrate', action='store', default=115200, dest='baudrate')
parser.add_argument('-i', '--hostname', action='store', default='localhost', dest='hostname')
parser.add_argument('-d', '--database', action='store', default='smartmeter', dest='database')
parser.add_argument('-v', '--verbose', action='store_true', default=False, dest='verbose')

argv = parser.parse_args()
verbose = argv.verbose

if verbose:
    print('Starting SmartMeter', argv.device, '@', argv.baudrate)

meter = SmartMeter(argv.device, baudrate=argv.baudrate)

if verbose:
    print('Connecting to influxdb', argv.hostname, 'db', argv.database)

influxdb = InfluxDBClient(argv.hostname, database=argv.database)
influxdb.create_database(argv.database)

fqdn = getfqdn()

try:
    while True:
        meter.connect()
        packet = meter.read_one_packet()

        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        data = [
            {
                'measurement': 'energy',
                'tags': {
                    'host': fqdn,
                },
                'time': timestamp,
                'fields': {
                    'high_produced': packet['kwh']['high']['produced'],
                    'high_consumed': packet['kwh']['high']['consumed'],
                    'low_produced': packet['kwh']['low']['produced'],
                    'low_consumed': packet['kwh']['low']['consumed'],
                    'tariff': packet['kwh']['tariff'],
                    'current_produced': packet['kwh']['current_produced'],
                    'current_consumed': packet['kwh']['current_consumed'],
                    'gas': packet['gas']['total'],
                },
            },
        ]

        if verbose:
            print(data)

        influxdb.write_points(data, time_precision='s')
except KeyboardInterrupt:
    pass

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

argv = parser.parse_args()

meter = SmartMeter(argv.device, baudrate=argv.baudrate)
packet = meter.read_one_packet()
timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
meter.disconnect()

data = [
    {
        'measurement': 'energy',
        'tags': {
            'host': getfqdn(),
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

client = InfluxDBClient(argv.hostname, database=argv.database)
client.create_database(argv.database)
client.write_points(data, time_precision='s')


import argparse
import serial
import datetime
from rm500u import *
from pymongo import MongoClient
from time import sleep
from signal import signal, SIGINT, SIGTERM

def handler(signal_received, frame):
    print('Closing MongoDB connection')
    client.close()
    exit(0)

parser = argparse.ArgumentParser(description='Monitoring RM500U 5G modem')
parser.add_argument('device', help='The device path')
parser.add_argument('-i', '--interval', type=int, default=60, help='Interval between each data request')
args = parser.parse_args()

print(f"Start: {datetime.datetime.now().isoformat()}")
# Connect to MongoDB
print("Connecting to MongoDB")
client = MongoClient('mongodb://localhost:27017/')
db = client['RM500U']
signal_strength = db['signal_strength']
serving_cell = db['serving_cell']
temperatures = db['temperatures']
data_counter = db['data_counter']
usbnet_ethernet_status = db['usbnet_ethernet_status']

signal(SIGINT, handler)
signal(SIGTERM, handler)

# Connect to the modem
print("Connecting to the modem")
serial = serial.Serial(args.device, 115200, timeout=1)

# Request data from the modem
while 1:
    print("Requesting data from the modem")
    signal_strength.insert_one({"time": datetime.datetime.now(datetime.timezone.utc), **request_signal_strength(serial).__dict__})
    serving_cell.insert_one({"time": datetime.datetime.now(datetime.timezone.utc), **request_servingcell(serial).__dict__})
    temperatures.insert_one({"time": datetime.datetime.now(datetime.timezone.utc), **request_temperatures(serial)})
    data_counter.insert_one({"time": datetime.datetime.now(datetime.timezone.utc), "data_counter": request_data_counter(serial)})
    usbnet_ethernet_status.insert_one({"time": datetime.datetime.now(datetime.timezone.utc), **request_usbnet_ethernet_status(serial, 2).__dict__})
    print("Data inserted")
    sleep(args.interval)
client.close()

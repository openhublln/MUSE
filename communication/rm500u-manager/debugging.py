import argparse
import serial
import time
from rm500u import *

parser = argparse.ArgumentParser(description='Debugging RM500U 5G modem')
parser.add_argument('device', help='The device path')
args = parser.parse_args()

serial = serial.Serial(args.device, 115200, timeout=1)

while 1:
    print(time.ctime())
    print(request_signal_strength(serial))
    print(request_servingcell(serial))
    print(request_temperatures(serial))
    print(request_data_counter(serial))
    print(request_usbnet_ethernet_status(serial, 2))
    print('-'*20)
    time.sleep(10)
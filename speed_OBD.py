import obd
import time
import csv
from datetime import datetime

# Config Bluetooth sur terminal Raspberry Pi: 
# MAC du device OBD : 66:1E:32:30:33:38
# sudo bluetoothctl
# scan on
# pair 66:1E:32:30:33:38
# trust 66:1E:32:30:33:38
# exit
# sudo rfcomm bind /dev/rfcomm0 66:1E:32:30:33:38

connection = obd.OBD('/dev/rfcomm0', fast=False) 
cmd = obd.commands.SPEED

def read_speed(connection):
    """Function to read and interpret speed from an OBD-II connection"""
    response = connection.query(cmd)
    if not response.is_null():
        speed_kmh = response.value.magnitude
        return speed_kmh
    return None

# Open the CSV file in write mode and create a csv writer object
with open('speed_test.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    # Write the header
    writer.writerow(["Time", "Speed (km/h)"])

    while connection.is_connected():
        speed = read_speed(connection)
        if speed is not None:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            speed_formatted = f"{speed:.3f}"
            writer.writerow([current_time, speed_formatted])
            print(f"Time: {current_time} - Car speed: {speed_formatted} km/h")
        time.sleep(0.1)

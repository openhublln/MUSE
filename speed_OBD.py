from obd import OBD, commands
import time
import csv
from datetime import datetime
import sys
import os

script_dir = sys.argv[1]
save_path = os.path.join(script_dir, "speed_test.csv")
# 
connection = OBD('/dev/rfcomm1', fast=False) 
cmd = commands.SPEED

def read_speed(connection):
    """Function to read and interpret speed from an OBD-II connection"""
    response = connection.query(cmd)
    if not response.is_null():
        speed_kmh = response.value.magnitude
        return speed_kmh
    return None

# Open the CSV file in write mode and create a csv writer object
with open(save_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    # Write the header
    writer.writerow(["Time", "Speed (km/h)"])

    while connection.is_connected():
        speed = read_speed(connection)
        if speed is not None:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            speed_formatted = f"{speed:.3f}"
            writer.writerow([current_time, speed_formatted])
            print(f"Time: {current_time} - Car speed: {speed_formatted} km/h")
        # time.sleep(0.1)

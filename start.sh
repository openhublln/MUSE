#!/bin/bash

DATA_DIR="/home/openhub/data"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
OUTPUT_DIR=$DATA_DIR/$TIMESTAMP

BT_ADDRESS="66:1E:32:30:33:38"

# create new directory with timestamp
mkdir -p $OUTPUT_DIR
chown openhub:openhub $DATA_DIR
chown openhub:openhub $OUTPUT_DIR

# launch services

# lidar
mkdir -p $OUTPUT_DIR/lidar
chown openhub:openhub $OUTPUT_DIR/lidar
systemctl start lidar@$OUTPUT_DIR/lidar

# camera
mkdir -p $OUTPUT_DIR/camera
chown openhub:openhub $OUTPUT_DIR/camera
systemctl start camera@$OUTPUT_DIR/camera

# obd
## Bluetooth pairing
rfcomm bind /dev/rfcomm1  $BT_ADDRESS

mkdir -p $OUTPUT_DIR/obd
chown openhub:openhub $OUTPUT_DIR/obd
systemctl start obd@$OUTPUT_DIR/obd

# communication
## gps
#systemctl start gpsd_exporter
## modem
systemctl start rm500u_logger
## performance measurement
systemctl start iperf_logger
systemctl start traceroute_loggerV4
systemctl start traceroute_loggerV6

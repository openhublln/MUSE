#!/bin/bash

DATA_DIR="/home/openhub/data"
TIMESTAMP=$(date +%Y_%m_%d_%H_%M_%S)
OUTPUT_DIR=$DATA_DIR/$TIMESTAMP

BT_ADDRESS="66:1E:32:30:33:38"
WIFI_INTERFACE="wlp0s20f3"

# if connected to wifi network, sync rsync DATA_DIR
if iw $WIFI_INTERFACE link  | grep Connected; then
    rsync -acz --remove-source-files --stats $DATA_DIR data_store:DATA/
    find $DATA_DIR -type d -empty -delete
    # power off as completed
    sleep 120
    # test if user is still logged in
    if who | grep openhub; then
        echo "User openhub is logged in, not powering off."
        exit 0
    fi
    poweroff
    exit 0
fi

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

# # radar
# mkdir -p $OUTPUT_DIR/radar
# chown openhub:openhub $OUTPUT_DIR/radar
# systemctl start radar@$OUTPUT_DIR/radar

# obd
## Bluetooth pairing
rfcomm bind /dev/rfcomm1  $BT_ADDRESS

mkdir -p $OUTPUT_DIR/obd
chown openhub:openhub $OUTPUT_DIR/obd
systemctl start obd@$OUTPUT_DIR/obd

# communication
## gps
systemctl start gpsd_exporter
## modem
systemctl start rm500u_logger
## performance measurement
systemctl start iperf_logger
systemctl start traceroute_loggerV4
systemctl start traceroute_loggerV6

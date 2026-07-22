#!/bin/bash

DATA_DIR="/DATA"
TIMESTAMP=$(date +%Y_%m_%d_%H_%M_%S)
OUTPUT_DIR=$DATA_DIR/$TIMESTAMP

BT_ADDRESS="66:1E:32:30:33:38"
WIFI_INTERFACE="wlp0s20f3"

# create new directory with timestamp
mkdir -p $OUTPUT_DIR
chown openhub:openhub $DATA_DIR
chown openhub:openhub $OUTPUT_DIR

cd /home/openhub/MUSE
./combined/main $OUTPUT_DIR

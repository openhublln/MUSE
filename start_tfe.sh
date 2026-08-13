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

# Start gPTP for Lidar acquisition 
echo "[INFO] Starting gPTP master..."

sudo ptp4l \
    -i enp1s0 \
    -S \
    -m \
    -l 6 \
    -f /usr/share/doc/linuxptp/configs/automotive-master.cfg \
    > ptp4l.log 2>&1 &

PTP_PID=$!

sleep 5

echo "[INFO] ptp4l PID = $PTP_PID"

if ! ps -p "$PTP_PID" > /dev/null ; then
    echo "[ERROR] ptp4l failed to start."
    cat ptp4l.log
    exit 1
fi
./combined_all_modal/main $OUTPUT_DIR

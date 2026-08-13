clear


# Start gPTP master


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

# Start acquisition

echo "compiling the script"
gcc -Wall -o main main.c utils.c camera.c radar.c lidar.c -lpthread && /
(echo "Executing..." ; ./main /DATA  2>&1 | tee acquisition.log)
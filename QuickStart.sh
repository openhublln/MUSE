#!/bin/bash

echo "QuickStart.sh ran at $(date)" >> /home/openhub/MUSE/quickstart_log.txt

# Start ssh-agent
eval "$(ssh-agent -s)"

# Wait for network - gives rsync time (max 30s) change to English or French accordingly
for i in {1..6}; do
    if nmcli -t -f active,ssid dev wifi | grep "^oui"; then
        echo "Wi-Fi connected."
        break
    fi
    echo "Waiting for Wi-Fi..."
    sleep 5
done

# Add your SSH key (will prompt for passphrase once)
ssh-add /home/openhub/MUSE/Keys/key

# Check current Wi-Fi network *****Checks for English and French
NETWORK_NAME=$(nmcli -t -f active,ssid dev wifi | grep -iE "^(yes|oui):" | cut -d':' -f2)

if [[ "$NETWORK_NAME" == "OpenHub_VR" ]]; then
    echo "Connected to OpenHub_VR network. Running data dump to remote..."

    # Run data dump script
    "/home/openhub/MUSE (Copie)/remote_dump.sh"

    echo "Data dump completed."
else
    echo "Not connected to OpenHub_VR network. Skipping data sync."
fi

# Kill ssh-agent
eval "$(ssh-agent -k)"

# setting the sudo password
SUDO_PASSWORD="openhub"

#Obd's Bluetooth
BT_ADDRESS="66:1E:32:30:33:38"
# BT_ADDRESS="C0:B5:D7:7D:D3:DE"
# BT_ADDRESS=E8:D5:2B:40:40:1C

# Root path
ROOT=~/MUSE
# Data root folder path
DATA_ROOT_PATH=$ROOT/DATA_$(date +%Y%m%d_%H%M%S)
mkdir $DATA_ROOT_PATH
# Data folder path
DATA_PATH=$DATA_ROOT_PATH/$(date +%Y%m%d_%H%M%S)
# DATA_PATH=/media/openhub/SAMSUNG/Muse/DATA
mkdir $DATA_PATH

################### SetUp #######################

#  master clock setting
start_master_clock() {
    cd ~/linuxptp/configs
    echo $SUDO_PASSWORD | sudo -S ptp4l -i enp1s0 -S -ml 6 -f automotive-master.cfg &
    MASTER_CLOCK_PID=$!
    echo $MASTER_CLOCK_PID > $ROOT/master_pid.txt
    echo "Master clock started with PID $MASTER_CLOCK_PID"
}

# Listen to Radar port
start_radar_tcpdump() {
    cd $DATA_PATH
    echo $SUDO_PASSWORD | sudo -S ip link set can0 up type can bitrate 500000
    echo $SUDO_PASSWORD | sudo -S tcpdump -i enp1s0 -tttt src host 192.168.11.11 and port 1000 -w "radar_eth_$(date +%Y%m%d_%H%M%S).pcapng" &
    RADAR_TCPDUMP_PID=$!
    echo $SUDO_PASSWORD | sudo -S tcpdump -i can0 -tttt -w "radar_can_$(date +%Y%m%d_%H%M%S).pcapng" &
    RADAR_CAN_TCPDUMP_PID=$!
    # echo $SUDO_PASSWORD | sudo -S dumpcap -i enp1s0 -f "src host 192.168.11.11 and udp and udp src port 1000" -n -g openhub -w "dumpcap/radar_$(date +%Y%m%d_%H%M%S).pcapng" &
    echo $RADAR_TCPDUMP_PID > $ROOT/RADAR_TCPDUMP_pid.txt
    echo $RADAR_CAN_TCPDUMP_PID > $ROOT/RADAR_CAN_TCPDUMP_pid.txt
    echo "Radar TCPDUMP started with PID $RADAR_TCPDUMP_PID and Can with $RADAR_CAN_TCPDUMP_PID"

}


#Start lidar reading - made for Copie path !!!
start_lidar_live_ply() {
    python3 "/home/openhub/MUSE (Copie)/lidar_live_ply.py" "$DATA_PATH" > "/home/openhub/MUSE (Copie)/log/lidar_live_ply.log" 2>&1 &
    LIDAR_PLY_PID=$!
    echo $LIDAR_PLY_PID > "/home/openhub/MUSE (Copie)/lidar_live_ply_pid.txt"
    echo "Live LiDAR PLY writing started with PID $LIDAR_PLY_PID"
}


# bluetooth setting
start_bluetooth() {
    cd $ROOT
    ./bluetooth.expect "$SUDO_PASSWORD" "$BT_ADDRESS" > $ROOT/log/bluetooth_connect.log 2>&1 &
    BT_PID=$!  
    echo $BT_PID > $ROOT/log/bluetooth_pid.txt

    wait $BT_PID 

    echo $SUDO_PASSWORD | sudo -S rfcomm release 1
    
  #  echo $SUDO_PASSWORD | chmod 666 /dev/rfcomm1 &
     

 #   Bluetooth bonding
    echo $SUDO_PASSWORD | sudo -S rfcomm bind /dev/rfcomm1 $BT_ADDRESS >> $ROOT/log/bluetooth_connect.log 2>&1
  
    echo "BLUETOOTH started with PID $BT_PID"
    

    echo "BLUETOOTH status is $(cat $ROOT/log/bluetooth_status.txt)"
}



################### Start #######################


# Activate the camera
start_camera() {
    cd $ROOT/
    python camera.py $DATA_PATH > $ROOT/log/camera_py.log 2>&1 &
    CAMERA_PID=$!
    echo $CAMERA_PID > $ROOT/camera_pid.txt
    echo "Camera script started with PID $CAMERA_PID"
}

# Activate the lidar
start_livox() {
    cd ~/Livox-SDK2/build/samples/livox_lidar_quick_start || exit
    ./livox_lidar_quick_start ../../../samples/livox_lidar_quick_start/hap_config.json > $ROOT/log/livox_output.log 2>&1 &
    LIVOX_PID=$!
    echo $LIVOX_PID > $ROOT/livox_pid.txt
    echo "Livox Lidar started with PID $LIVOX_PID"
}

#execute OBD's code 
start_obd() {

    cd $ROOT/
    python speed_OBD.py $DATA_PATH > $ROOT/log/speed_output.log 2>&1 &
    OBD_PID=$!
    echo $SUDO_PASSWORD | sudo -S chmod 666 /dev/rfcomm1 &

    echo $OBD_PID > $ROOT/obd_pid.txt
    echo "OBD started with PID $(cat $ROOT/obd_pid.txt)"

}


############################# stop func ################################

# stop listening to the lidar
stop_lidar_live_ply() {
    if [ -f $ROOT/LIDAR_LIVE_PLY_pid.txt ]; then
        LIDAR_LIVE_PLY_PID=$(cat $ROOT/LIDAR_LIVE_PLY_pid.txt)
        if [ -n "$LIDAR_LIVE_PLY_PID" ]; then
            echo "Stopping live lidar PLY process $LIDAR_LIVE_PLY_PID"
            kill -SIGINT $LIDAR_LIVE_PLY_PID
            sleep 2
            if kill -0 $LIDAR_LIVE_PLY_PID 2>/dev/null; then
                echo "Force killing process $LIDAR_LIVE_PLY_PID"
                kill -9 $LIDAR_LIVE_PLY_PID
            fi
            rm $ROOT/LIDAR_LIVE_PLY_pid.txt
        fi
    fi
}

# stop listening to the radar
stop_radar_tcpdump() {
    if [ -f $ROOT/RADAR_TCPDUMP_pid.txt ]; then
        RADAR_TCPDUMP_PID=$(cat $ROOT/RADAR_TCPDUMP_pid.txt)
        if [ -n "$RADAR_TCPDUMP_PID" ]; then
            echo "Attempting to kill TCPDump process $RADAR_TCPDUMP_PID"
            echo $SUDO_PASSWORD | sudo -S kill -SIGINT $RADAR_TCPDUMP_PID
            sleep 1  
            if sudo kill -0 $RADAR_TCPDUMP_PID 2>/dev/null; then
                echo "Process $RADAR_TCPDUMP_PID did not terminate, forcing kill"
                echo $SUDO_PASSWORD | sudo -S kill -9 $RADAR_TCPDUMP_PID
            else
                echo "Process $RADAR_TCPDUMP_PID terminated successfully"
            fi
            rm $ROOT/RADAR_TCPDUMP_pid.txt
        else
            echo "No valid PID found in the RADAR_TCPDUMP PID file"
        fi
    else
        echo "RADAR TCPDump PID file does not exist"
    fi
    if [ -f $ROOT/RADAR_CAN_TCPDUMP_pid.txt ]; then
        RADAR_CAN_TCPDUMP_PID=$(cat $ROOT/RADAR_CAN_TCPDUMP_pid.txt)
        if [ -n "$RADAR_CAN_TCPDUMP_PID" ]; then
            echo "Attempting to kill TCPDump process $RADAR_CAN_TCPDUMP_PID"
            echo $SUDO_PASSWORD | sudo -S kill -SIGINT $RADAR_CAN_TCPDUMP_PID
            sleep 1  
            if sudo kill -0 $RADAR_CAN_TCPDUMP_PID 2>/dev/null; then
                echo "Process $RADAR_CAN_TCPDUMP_PID did not terminate, forcing kill"
                echo $SUDO_PASSWORD | sudo -S kill -9 $RADAR_CAN_TCPDUMP_PID
            else
                echo "Process $RADAR_CAN_TCPDUMP_PID terminated successfully"
            fi
            rm $ROOT/RADAR_CAN_TCPDUMP_pid.txt
        else
            echo "No valid PID found in the RADAR_CAN_TCPDUMP PID file"
        fi
    else
        echo "RADAR CAN TCPDump PID file does not exist"
    fi
}


# close Master Clock
stop_master_clock() {
    if [ -f $ROOT/master_pid.txt ]; then
        MASTER_CLOCK_PID=$(cat $ROOT/master_pid.txt)
        if [ -n "$MASTER_CLOCK_PID" ]; then
            echo "Attempting to kill Master clock process $MASTER_CLOCK_PID"
            echo $SUDO_PASSWORD | sudo -S kill -SIGINT $MASTER_CLOCK_PID
            sleep 1  
            if sudo kill -0 $MASTER_CLOCK_PID 2>/dev/null; then
                echo "Process $MASTER_CLOCK_PID did not terminate, forcing kill"
                echo $SUDO_PASSWORD | sudo -S kill -9 $MASTER_CLOCK_PID
            else
                echo "Process $MASTER_CLOCK_PID terminated successfully"
            fi
            rm $ROOT/master_pid.txt
        else
            echo "No valid PID found in the master PID file"
        fi
    else
        echo "Master PID file does not exist"
    fi
}

# turn off the camera
stop_camera() {
    if [ -f $ROOT/camera_pid.txt ]; then
        CAMERA_PID=$(cat $ROOT/camera_pid.txt)
        if [ -n "$CAMERA_PID" ]; then
            echo "Attempting to kill Camera script process $CAMERA_PID"
            kill -SIGINT $CAMERA_PID
            sleep 1 
            if kill -0 $CAMERA_PID 2>/dev/null; then
                echo "Process $CAMERA_PID did not terminate, forcing kill"
                kill -9 $CAMERA_PID
            else
                echo "Process $CAMERA_PID terminated successfully"
            fi
            rm $ROOT/camera_pid.txt
        else
            echo "No valid PID found in the camera PID file"
        fi
    else
        echo "Camera PID file does not exist"
    fi
}

# stop the lidar process
stop_livox() {
    if [ -f $ROOT/livox_pid.txt ]; then
        LIVOX_PID=$(cat $ROOT/livox_pid.txt)
        if [ -n "$LIVOX_PID" ]; then
            echo "Attempting to kill Livox Lidar process $LIVOX_PID"
            kill -SIGINT $LIVOX_PID
            sleep 1  
            if kill -0 $LIVOX_PID 2>/dev/null; then
                echo "Process $LIVOX_PID did not terminate, forcing kill"
                kill -9 $LIVOX_PID
            else
                echo "Process $LIVOX_PID terminated successfully"
            fi
            rm $ROOT/livox_pid.txt
        else
            echo "No valid PID found in the Livox PID file"
        fi
    else
        echo "Livox PID file does not exist"
    fi
}


# interrupt bluetooth 
stop_bluetooth() {
    cd $ROOT
    ./bluetoothdisconnect.expect "$SUDO_PASSWORD" "$BT_ADDRESS" > $ROOT/log/bluetooth_disconnect.log 2>&1 &
    DISCONNECT_PID=$! 

    wait $DISCONNECT_PID

 
    echo "BLUETOOTH status is $(cat $ROOT/log/bluetoothdisconnect_status.txt)"
}

# stop the obd process
stop_obd() {
    if [ -f $ROOT/obd_pid.txt ]; then
        OBD_PID=$(cat $ROOT/obd_pid.txt)
        if [ -n "$OBD_PID" ]; then
            echo "Attempting to kill OBD process $OBD_PID"
            kill -SIGINT $OBD_PID
            sleep 1  

	    timestamp=$(date +"%Y%m%d_%H%M%S")
            base_name="speed_test.csv"
            dest_dir="$DATA_PATH"
            new_name="$dest_dir/speed_test_$timestamp.csv"

            mv "$base_name" "$new_name"
     
            if kill -0 $OBD_PID 2>/dev/null; then
                echo "Process $OBD_PID did not terminate, forcing kill"
                kill -9 $OBD_PID
            else
                echo "Process $OBD_PID terminated successfully"
            fi
            rm $ROOT/obd_pid.txt
        else
            echo "No valid PID found in the OBD PID file"
        fi
    else
        echo "OBD PID file does not exist"
    fi
}	


################################## MAIN CODE ###################################

# start to detect
start_all() { 

    start_livox &
    LIVOX_PID=$!

    #  start_obd &
    #  OBD_PID=$!
    
    start_camera &
    CAMERA_PID=$!
    
    wait $LIVOX_PID
    #  wait $OBD_PID
    wait $CAMERA_PID

    
    echo "All processes started"

}


# setup

setup_all() {
     echo $SUDO_PASSWORD | sudo -S mkdir $DATA_PATH/dumpcap

    #  start_bluetooth &
    #  BLUETOOTH_PID=$!
    
    start_master_clock &
    MASTER_CLOCK_PID=$!

    start_lidar_live_ply &
    LIDAR_TCPDUMP_PID=$!
    
    start_radar_tcpdump &
    RADAR_TCPDUMP_PID=$!


    #  wait $BLUETOOTH_PID
    wait $MASTER_CLOCK_PID
    wait $LIDAR_LIVE_PLY_PID
    wait $RADAR_TCPDUMP_PID

    echo "############### Setting OK"
}



# stop all process
stop_all() {
    stop_camera
    stop_lidar_live_ply
    stop_radar_tcpdump
    stop_livox
    stop_master_clock
    stop_obd
    stop_bluetooth
    echo "All processes stopped"
}

# restart
restart_all() {
    stop_camera
    stop_lidar_live_ply
    stop_radar_tcpdump
    stop_livox
    # stop_obd
    echo "******* Stopped ready to restart..."

    DATA_PATH=$DATA_ROOT_PATH/$(date +%Y%m%d_%H%M%S)
    mkdir $DATA_PATH

    start_lidar_live_ply &
    LIDAR_LIVE_PLY_PID=$!
    start_radar_tcpdump &
    RADAR_TCPDUMP_PID=$!
    wait $LIDAR_LIVE_PLY_PID
    wait $RADAR_TCPDUMP_PID
    echo "******* Setting OK"

    start_livox &
    LIVOX_PID=$!
    # start_obd &
    # OBD_PID=$!
    start_camera &
    CAMERA_PID=$!
    wait $LIVOX_PID
    # wait $OBD_PID
    wait $CAMERA_PID
    echo "******* Started"
}

# interrupt
trap ctrl_c INT

ctrl_c() {
    echo "** Trapped CTRL-C"
    stop_all
    exit 1
}


# main code
if [ "$1" == "start" ]; then
    setup_all
    wait
    start_all
elif [ "$1" == "stop" ]; then
    stop_all
    exit 1
else
    echo "Usage: $0 {start|stop}"
    exit 1
fi

# preventing shell exit
while :
do
    sleep 300
    restart_all
    echo "Restart"
done


#!/bin/bash

# setting the sudo password
SUDO_PASSWORD="openhub"

#Obd's Bluetooth
BT_ADDRESS="66:1E:32:30:33:38"
# BT_ADDRESS="E8:D5:2B:40:40:1C"

################### SetUp #######################



# bluetooth setting
start_bluetooth() {
    cd ~/Muse
    ./bluetooth.expect "$SUDO_PASSWORD" "$BT_ADDRESS" > log/bluetooth_connect.log 2>&1 &
    BT_PID=$!  
    echo $BT_PID > ~/Muse/log/bluetooth_pid.txt

    wait $BT_PID 

    echo $SUDO_PASSWORD | sudo -S rfcomm release 1
    
  #  echo $SUDO_PASSWORD | chmod 666 /dev/rfcomm1 &
     

 #   Bluetooth bonding
    echo $SUDO_PASSWORD | sudo -S rfcomm bind /dev/rfcomm1 $BT_ADDRESS >> log/bluetooth_connect.log 2>&1
  
    echo "BLUETOOTH started with PID $BT_PID"
    

    echo "BLUETOOTH status is $(cat ~/Muse/log/bluetooth_status.txt)"
}



################### Start #######################



#execute OBD's code 
start_obd() {

    cd ~/Muse/
    python speed_OBD.py &
    OBD_PID=$!
    echo $SUDO_PASSWORD | sudo -S chmod 666 /dev/rfcomm1 &

    echo $OBD_PID > ~/Muse/obd_pid.txt
    echo "OBD started with PID $(cat ~/Muse/obd_pid.txt)"

}




############################# stop func ################################



# interrupt bluetooth 
stop_bluetooth() {
    cd ~/Muse
    ./bluetoothdisconnect.expect "$SUDO_PASSWORD" "$BT_ADDRESS" > log/bluetooth_disconnect.log 2>&1 &
    DISCONNECT_PID=$! 

    wait $DISCONNECT_PID

 
    echo "BLUETOOTH status is $(cat ~/Muse/log/bluetoothdisconnect_status.txt)"
}

# stop the obd process
stop_obd() {
    if [ -f ~/Muse/obd_pid.txt ]; then
        OBD_PID=$(cat ~/Muse/obd_pid.txt)
        if [ -n "$OBD_PID" ]; then
            echo "Attempting to kill OBD process $OBD_PID"
            kill -SIGINT $OBD_PID
            sleep 1  

	    timestamp=$(date +"%Y%m%d_%H%M%S")
            base_name="speed_test.csv"
            dest_dir="$HOME/Desktop/Muse/DATA"
            new_name="$dest_dir/speed_test_$timestamp.csv"

            mv "$base_name" "$new_name"
     
            if kill -0 $OBD_PID 2>/dev/null; then
                echo "Process $OBD_PID did not terminate, forcing kill"
                kill -9 $OBD_PID
            else
                echo "Process $OBD_PID terminated successfully"
            fi
            rm ~/Muse/obd_pid.txt
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
    
   start_obd &
   OBD_PID=$!

   wait $OBD_PID

    
    echo "All processes started"

}


# setup

setup_all() {

    start_bluetooth &
    BLUETOOTH_PID=$!
    
    


    wait $BLUETOOTH_PID
   

    echo "############### Setting OK"
}



# stop all process
stop_all() {
    stop_bluetooth
   stop_obd
    echo "All processes stopped"
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
else
    echo "Usage: $0 {start|stop}"
    exit 1
fi

# preventing shell exit
while :
do
    sleep 1
done


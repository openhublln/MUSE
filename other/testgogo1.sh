#!/bin/bash

# Function to start Livox Lidar
start_livox() {
    cd ~/Documents/Livox-test/Livox-SDK2/build/samples/livox_lidar_quick_start || exit
    ./livox_lidar_quick_start ../../../samples/livox_lidar_quick_start/hap_config.json > ~/Desktop/Muse-main/livox_output.log 2>&1 &
    LIVOX_PID=$!
    echo $LIVOX_PID > ~/Desktop/Muse-main/livox_pid.txt
    echo "Livox Lidar started with PID $LIVOX_PID"
}

# Function to stop Livox Lidar
kill_livox() {
    if [ -f ~/Desktop/Muse-main/livox_pid.txt ]; then
        LIVOX_PID=$(cat ~/Desktop/Muse-main/livox_pid.txt)
        if [ -n "$LIVOX_PID" ]; then
            kill -SIGINT $LIVOX_PID  # Send SIGINT to Livox Lidar process
            echo "Sent SIGINT to Livox Lidar process $LIVOX_PID"
           rm ~/Desktop/Muse-main/livox_pid.txt
        else
            echo "No valid PID found in the file"
        fi
    else
        echo "PID file does not exist"
    fi
}

# Function to handle Ctrl+C signal
handle_ctrl_c() {
    echo "Ctrl+C pressed. Stopping all programs..."
    stop_all
    exit 0
}

# Function to start all programs
start_all() {
    start_livox
    echo "start"
}

# Function to stop all programs
stop_all() {
    kill_livox
    echo "stop"
}

# Trap Ctrl+C signal to invoke handle_ctrl_c function
trap handle_ctrl_c SIGINT

# Main script logic
case "$1" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        exit 1
        ;;
esac



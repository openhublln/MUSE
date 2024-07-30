#!/bin/bash

# 设置 sudo 密码
SUDO_PASSWORD="openhub"

# 切换到主目录
cd ~

# 提前设置 sudo 密码缓存
echo $SUDO_PASSWORD | sudo -S echo "Sudo password set"

# 定义全局变量来存储各进程的 PID
declare -g MASTER_CLOCK_PID
declare -g TCPDUMP_PID
declare -g LIVOX_PID
declare -g CAMERA_PID
declare -g OBD_PID

###################################### 函数定义 ########################################

# 开启 master clock
start_master_clock() {
    cd ~/Documents/linuxptp/configs
    echo $SUDO_PASSWORD | sudo -S ptp4l -i enp0s31f6 -S -ml 6 -f automotive-master.cfg &
    MASTER_CLOCK_PID=$!
    echo "Master clock started with PID $MASTER_CLOCK_PID"
}

# 接封包
start_tcpdump() {
    cd ~/Desktop/Off_Line_Processing/Lidar
    echo $SUDO_PASSWORD | sudo -S tcpdump -i any port 57000 -w capture.pcap &
    TCPDUMP_PID=$!
    echo "TCPDump started with PID $TCPDUMP_PID"
}


# 提前设置 sudo 密码缓存
echo $SUDO_PASSWORD | sudo -S echo "Sudo password set"
# Livox Quickstart
start_livox() {
    cd ~/Documents/Livox-SDK2/build/samples/livox_lidar_quick_start
    ./livox_lidar_quick_start ../../../samples/livox_lidar_quick_start/hap_config.json > ~/Desktop/Muse-main/livox_output.log 2>&1 &
    LIVOX_PID=$!
    echo "Livox Lidar started with PID $LIVOX_PID"
}

# 启动摄像头脚本
start_camera() {
    cd ~/Desktop/Muse-main/
    python testcamera.py &
    CAMERA_PID=$!
    echo "Camera script started with PID $CAMERA_PID"
}

# 启动OBD
start_obd() {
    cd ~/Desktop/Muse-main/
    python speed_OBD.py &
    OBD_PID=$!
    echo "OBD script started with PID $OBD_PID"
}

# 启动所有进程
start_all() {
    start_master_clock
    start_tcpdump
    start_livox
    start_camera
    start_obd
    echo "All processes started"
}

# 停止所有进程
stop_all() {
    [ -n "$MASTER_CLOCK_PID" ] && echo $SUDO_PASSWORD | sudo -S kill -9 $MASTER_CLOCK_PID
    [ -n "$TCPDUMP_PID" ] && echo $SUDO_PASSWORD | sudo -S kill -9 $TCPDUMP_PID
    [ -n "$LIVOX_PID" ] && echo $SUDO_PASSWORD | sudo -S kill -9 $LIVOX_PID
    [ -n "$CAMERA_PID" ] && echo $SUDO_PASSWORD | sudo -S kill -9 $CAMERA_PID
    [ -n "$OBD_PID" ] && echo $SUDO_PASSWORD | sudo -S kill -9 $OBD_PID
    echo "All processes stopped"
    echo "Bye~"
}

# 在收到 SIGINT 信号时执行停止所有进程的操作
trap "stop_all" SIGINT

###################################### 主程序 ########################################

if [ "$1" == "start" ]; then
    start_all
elif [ "$1" == "stop" ]; then
    stop_all
else
    echo "Usage: $0 {start|stop}"
fi


#!/bin/bash

# 设置 sudo 密码
SUDO_PASSWORD="openhub"

# 切换到主目录
cd ~

# 提前设置 sudo 密码缓存
echo $SUDO_PASSWORD | sudo -S echo "Sudo password set"

###################################### 函数定义 ########################################

# 开启 master clock
start_master_clock() {
    cd ~/Downloads/linuxptp-4.2/configs
    echo $SUDO_PASSWORD | sudo -S ptp4l -i enp3s0 -S -ml 6 -f automotive-master.cfg &
    MASTER_CLOCK_PID=$!
    echo "Master clock started with PID $MASTER_CLOCK_PID"
}

# 接封包
start_tcpdump() {
    cd ~/Desktop/Parse_UDP
    echo $SUDO_PASSWORD | sudo -S tcpdump -i any port 57000 -w capture.pcap &
    TCPDUMP_PID=$!
    echo "TCPDump started with PID $TCPDUMP_PID"
}

# Livox Quickstart
start_livox() {
    cd ~/Documents/thu/Livox-SDK2/build/samples/livox_lidar_quick_start
    ./livox_lidar_quick_start ../../../samples/livox_lidar_quick_start/hap_config.json > ~/Documents/thu/UDPpkg/livox_output.log 2>&1 &
    LIVOX_PID=$!
    echo "Livox Lidar started with PID $LIVOX_PID"
}

# 启动摄像头脚本
start_camera() {
    cd ~/Desktop
    python testcamera.py &
    CAMERA_PID=$!
    echo "Camera script started with PID $CAMERA_PID"
}

# 启动所有进程
start_all() {
    start_master_clock
    start_tcpdump
    start_livox
    start_camera
    echo "All processes start"
}

# 停止所有进程
stop_all() {
    echo $SUDO_PASSWORD | sudo -S kill $MASTER_CLOCK_PID
    echo $SUDO_PASSWORD | sudo -S kill $TCPDUMP_PID
    kill $LIVOX_PID
    kill $CAMERA_PID
    echo "All processes stopped"
    echo "bye~"
}

###################################### 主程序 ########################################

if [ "$1" == "start" ]; then
    start_all
elif [ "$1" == "stop" ]; then
    stop_all
else
    echo "Usage: $0 {start|stop}"
fi

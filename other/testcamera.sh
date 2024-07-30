#!/bin/bash

# 设置 sudo 密码
SUDO_PASSWORD="openhub"

# 切换到主目录
cd ~

# 提前设置 sudo 密码缓存
echo $SUDO_PASSWORD | sudo -S echo "Sudo password set"

# 启动摄像头脚本
start_camera() {
    cd ~/Desktop/Muse-main/
    python testcamera.py &
    CAMERA_PID=$!
    echo $CAMERA_PID > ~/Desktop/Muse-main/camera_pid.txt
    echo "Camera script started with PID $CAMERA_PID"
}

# 停止摄像头脚本
stop_camera() {
    if [ -f ~/Desktop/Muse-main/camera_pid.txt ]; then
        CAMERA_PID=$(cat ~/Desktop/Muse-main/camera_pid.txt)
        if [ -n "$CAMERA_PID"#!/bin/bash

 ]; then
            kill -SIGINT $CAMERA_PID
            echo "Sent SIGINT to Camera script process $CAMERA_PID"
            rm ~/Desktop/Muse-main/camera_pid.txt
        else
            echo "No valid PID found in the camera PID file"
        fi
    else
        echo "Camera PID file does not exist"
    fi
}

# 启动所有相关进程
start_all() {
    start_camera
    echo "All processes started"
}

# 停止所有相关进程
stop_all() {
    stop_camera
    echo "All processes stopped"
}

# 处理 Ctrl+C 中断信号
trap ctrl_c INT

ctrl_c() {
    echo "** Trapped CTRL-C"
    stop_all
    exit 1
}

# 主程序，根据命令行参数执行相应操作
if [ "$1" == "start" ]; then
    start_all
elif [ "$1" == "stop" ]; then
    stop_all
else
    echo "Usage: $0 {start|stop}"
    exit 1
fi

# 循环等待，防止脚本退出
while :
do
    sleep 1
done


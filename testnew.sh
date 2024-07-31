#!/bin/bash

# 设置 sudo 密码
SUDO_PASSWORD="openhub"
#BT_ADDRESS="66:1E:32:30:33:38"
BT_ADDRESS="C0:B5:D7:7D:D3:DE"
################### SetUp #######################

# 开启 master clock
start_master_clock() {
    cd ~/Documents/linuxptp/configs
    echo $SUDO_PASSWORD | sudo -S ptp4l -i enp0s31f6 -S -ml 6 -f automotive-master.cfg &
    MASTER_CLOCK_PID=$!
    echo $MASTER_CLOCK_PID > ~/Desktop/Muse/master_pid.txt
    echo "Master clock started with PID $MASTER_CLOCK_PID"
}

start_radar_tcpdump() {
    cd ~/Desktop/Muse/DATA
    echo $SUDO_PASSWORD | sudo -S tcpdump -i any -tttt src host 192.168.16.2 and port 6172 -w "radar_$(date +%Y%m%d_%H%M%S).pcap" &
    RADAR_TCPDUMP_PID=$!
    echo $RADAR_TCPDUMP_PID > ~/Desktop/Muse/RADAR_TCPDUMP_pid.txt
    echo "Radar TCPDUMP started with PID $RADAR_TCPDUMP_PID"

}

# 接封包
start_lidar_tcpdump() {
    cd ~/Desktop/Muse/DATA
    echo $SUDO_PASSWORD | sudo -S tcpdump -i any port 57000 -w "lidar_$(date +%Y%m%d_%H%M%S).pcap" &
    LIDAR_TCPDUMP_PID=$!
    echo $LIDAR_TCPDUMP_PID > ~/Desktop/Muse/LIDAR_TCPDUMP_pid.txt
    echo "LIDAR TCPDump started with PID $LIDAR_TCPDUMP_PID"
}

# bluetooth 
start_bluetooth() {
    cd ~/Desktop/Muse
    ./bluetooth.expect "$SUDO_PASSWORD" "$BT_ADDRESS" > log/bluetooth_connect.log 2>&1 &
    BT_PID=$!  # 获取bluetooth.expect命令的PID
    echo $BT_PID > ~/Desktop/Muse/log/bluetooth_pid.txt

    wait $BT_PID 

    echo $SUDO_PASSWORD | sudo -S rfcomm release 1 &
    
  #  echo $SUDO_PASSWORD | chmod 666 /dev/rfcomm1 &
     

 #   使用sudo执行rfcomm命令并获取其退出状态
    echo $SUDO_PASSWORD | sudo -S rfcomm bind /dev/rfcomm1 $BT_ADDRESS >> log/bluetooth_connect.log 2>&1
  
    echo "BLUETOOTH started with PID $BT_PID"
    
  # 输出bluetooth_status.txt的内容
    echo "BLUETOOTH status is $(cat ~/Desktop/Muse/log/bluetooth_status.txt)"
}



################### Start #######################


# 启动摄像头脚本
start_camera() {
    cd ~/Desktop/Muse/
    python testcamera.py &
    CAMERA_PID=$!
    echo $CAMERA_PID > ~/Desktop/Muse/camera_pid.txt
    echo "Camera script started with PID $CAMERA_PID"
}

# 启动 Livox Quickstart
start_livox() {
    cd ~/Documents/Livox-test/Livox-SDK2/build/samples/livox_lidar_quick_start || exit
    ./livox_lidar_quick_start ../../../samples/livox_lidar_quick_start/hap_config.json > ~/Desktop/Muse/log/loglivox_output.log 2>&1 &
    LIVOX_PID=$!
    echo $LIVOX_PID > ~/Desktop/Muse/livox_pid.txt
    echo "Livox Lidar started with PID $LIVOX_PID"
}

#OBD
start_obd() {

    cd ~/Desktop/Muse/
    python speed_OBD.py &
    OBD_PID=$!
    echo $SUDO_PASSWORD | sudo -S chmod 666 /dev/rfcomm1 &

    echo $OBD_PID > ~/Desktop/Muse/obd_pid.txt
    echo "OBD started with PID $(cat ~/Desktop/Muse/obd_pid.txt)"

}


#Radar 
start_radar() {

    cd ~/Desktop/Muse/
    python read_radar.py &
    radar_PID=$!
    echo $radar_PID > ~/Desktop/Muse/radar_pid.txt
    echo "Radar started with PID $(cat ~/Desktop/Muse/radar_pid)"

}

############################# 停止 ################################

#停止接封包
stop_lidar_tcpdump() {
    if [ -f ~/Desktop/Muse/LIDAR_TCPDUMP_pid.txt ]; then
        LIDAR_TCPDUMP_PID=$(cat ~/Desktop/Muse/LIDAR_TCPDUMP_pid.txt)
        if [ -n "$LIDAR_TCPDUMP_PID" ]; then
            echo "Attempting to kill TCPDump process $LIDAR_TCPDUMP_PID"
            echo $SUDO_PASSWORD | sudo -S kill -SIGINT $LIDAR_TCPDUMP_PID
            sleep 1  # 等待进程响应
	    if sudo kill -0 $LIDAR_TCPDUMP_PID 2>/dev/null; then
                echo "Process $LIDAR_TCPDUMP_PID did not terminate, forcing kill"
                echo $SUDO_PASSWORD | sudo -S kill -9 $LIDAR_TCPDUMP_PID
            else
                echo "Process $LIDAR_TCPDUMP_PID terminated successfully"
            fi
            rm ~/Desktop/Muse/LIDAR_TCPDUMP_pid.txt
        else
            echo "No valid PID found in the LIDAR_TCPDump PID file"
        fi
    else
        echo "LIDAR TCPDump PID file does not exist"
    fi
}

# 停止接封包
stop_radar_tcpdump() {
    if [ -f ~/Desktop/Muse/RADAR_TCPDUMP_pid.txt ]; then
        LIDAR_TCPDUMP_PID=$(cat ~/Desktop/Muse/RADAR_TCPDUMP_pid.txt)
        if [ -n "$RADAR_TCPDUMP_PID" ]; then
            echo "Attempting to kill TCPDump process $RADAR_TCPDUMP_PID"
            echo $SUDO_PASSWORD | sudo -S kill -SIGINT $RADAR_TCPDUMP_PID
            sleep 1  # 等待进程响应
            if sudo kill -0 $RADAR_TCPDUMP_PID 2>/dev/null; then
                echo "Process $RADAR_TCPDUMP_PID did not terminate, forcing kill"
                echo $SUDO_PASSWORD | sudo -S kill -9 $RADAR_TCPDUMP_PID
            else
                echo "Process $RADAR_TCPDUMP_PID terminated successfully"
            fi
            rm ~/Desktop/Muse/RADAR_TCPDUMP_pid.txt
        else
            echo "No valid PID found in the RADAR_TCPDUMP PID file"
        fi
    else
        echo "RADAR TCPDump PID file does not exist"
    fi
}


# 停止 Master Clock
stop_master_clock() {
    if [ -f ~/Desktop/Muse/master_pid.txt ]; then
        MASTER_CLOCK_PID=$(cat ~/Desktop/Muse/master_pid.txt)
        if [ -n "$MASTER_CLOCK_PID" ]; then
            echo "Attempting to kill Master clock process $MASTER_CLOCK_PID"
            echo $SUDO_PASSWORD | sudo -S kill -SIGINT $MASTER_CLOCK_PID
            sleep 1  # 等待进程响应
            if sudo kill -0 $MASTER_CLOCK_PID 2>/dev/null; then
                echo "Process $MASTER_CLOCK_PID did not terminate, forcing kill"
                echo $SUDO_PASSWORD | sudo -S kill -9 $MASTER_CLOCK_PID
            else
                echo "Process $MASTER_CLOCK_PID terminated successfully"
            fi
            rm ~/Desktop/Muse/master_pid.txt
        else
            echo "No valid PID found in the master PID file"
        fi
    else
        echo "Master PID file does not exist"
    fi
}

# 停止摄像头脚本
stop_camera() {
    if [ -f ~/Desktop/Muse/camera_pid.txt ]; then
        CAMERA_PID=$(cat ~/Desktop/Muse/camera_pid.txt)
        if [ -n "$CAMERA_PID" ]; then
            echo "Attempting to kill Camera script process $CAMERA_PID"
            kill -SIGINT $CAMERA_PID
            sleep 1  # 等待进程响应
            if kill -0 $CAMERA_PID 2>/dev/null; then
                echo "Process $CAMERA_PID did not terminate, forcing kill"
                kill -9 $CAMERA_PID
            else
                echo "Process $CAMERA_PID terminated successfully"
            fi
            rm ~/Desktop/Muse/camera_pid.txt
        else
            echo "No valid PID found in the camera PID file"
        fi
    else
        echo "Camera PID file does not exist"
    fi
}

# 停止 Livox Quickstart
stop_livox() {
    if [ -f ~/Desktop/Muse/livox_pid.txt ]; then
        LIVOX_PID=$(cat ~/Desktop/Muse/livox_pid.txt)
        if [ -n "$LIVOX_PID" ]; then
            echo "Attempting to kill Livox Lidar process $LIVOX_PID"
            kill -SIGINT $LIVOX_PID
            sleep 1  # 等待进程响应
            if kill -0 $LIVOX_PID 2>/dev/null; then
                echo "Process $LIVOX_PID did not terminate, forcing kill"
                kill -9 $LIVOX_PID
            else
                echo "Process $LIVOX_PID terminated successfully"
            fi
            rm ~/Desktop/Muse/livox_pid.txt
        else
            echo "No valid PID found in the Livox PID file"
        fi
    else
        echo "Livox PID file does not exist"
    fi
}

# 停止雷达进程
stop_radar() {
    if [ -f ~/Desktop/Muse/radar_pid.txt ]; then
        RADAR_PID=$(cat ~/Desktop/Muse/radar_pid.txt)
        if [ -n "$RADAR_PID" ]; then
            echo "Attempting to kill Radar process $RADAR_PID"
            kill -SIGINT $RADAR_PID
            sleep 1  # 等待进程响应
            if kill -0 $RADAR_PID 2>/dev/null; then
                echo "Process $RADAR_PID did not terminate, forcing kill"
                kill -9 $RADAR_PID
            else
                echo "Process $RADAR_PID terminated successfully"
            fi
            rm ~/Desktop/Muse/radar_pid.txt
        else
            echo "No valid PID found in the Radar PID file"
        fi
    else
        echo "Radar PID file does not exist"
    fi
}


# bluetooth 
stop_bluetooth() {
    cd ~/Desktop/Muse
    ./bluetoothdisconnect.expect "$SUDO_PASSWORD" "$BT_ADDRESS" > log/bluetooth_disconnect.log 2>&1 &
    DISCONNECT_PID=$!  # 获取 bluetoothdisconnect.expect 命令的 PID

    wait $DISCONNECT_PID

  # 输出bluetooth_status.txt的内容
    echo "BLUETOOTH status is $(cat ~/Desktop/Muse/log/bluetoothdisconnect_status.txt)"
}

# 停止 OBD
stop_obd() {
    if [ -f ~/Desktop/Muse/obd_pid.txt ]; then
        OBD_PID=$(cat ~/Desktop/Muse/obd_pid.txt)
        if [ -n "$OBD_PID" ]; then
            echo "Attempting to kill OBD process $OBD_PID"
            kill -SIGINT $OBD_PID
            sleep 1  # 等待进程响应
	    mv speed_test.csv ~/Desktop/Muse/DATA
            if kill -0 $OBD_PID 2>/dev/null; then
                echo "Process $OBD_PID did not terminate, forcing kill"
                kill -9 $OBD_PID
            else
                echo "Process $OBD_PID terminated successfully"
            fi
            rm ~/Desktop/Muse/obd_pid.txt
        else
            echo "No valid PID found in the OBD PID file"
        fi
    else
        echo "OBD PID file does not exist"
    fi
}	


################################## MAIN CODE ###################################

# 启动所有相关进程
start_all() { 

    start_livox &
    LIVOX_PID=$!
    
    start_radar &
    RADAR_PID=$!

 #   start_obd &
#    OBD_PID=$!
    
    start_camera &
    CAMERA_PID=$!
    
    wait $LIVOX_PID
    wait $RADAR_PID
#    wait $OBD_PID
    wait $CAMERA_PID

    
    echo "All processes started"

}

setup_all() {

    start_bluetooth &
    BLUETOOTH_PID=$!
    
    start_master_clock &
    MASTER_CLOCK_PID=$!

    start_lidar_tcpdump &
    LIDAR_TCPDUMP_PID=$!
    
    start_radar_tcpdump &
    RADAR_TCPDUMP_PID=$!


    wait $BLUETOOTH_PID
    wait $MASTER_CLOCK_PID
    wait $LIDAR_TCPDUMP_PID
    wait $RADAR_TCPDUMP_PID

    echo "############### Setting OK"
}



# 停止所有相关进程
stop_all() {
    stop_camera
    stop_lidar_tcpdump
    stop_radar_tcpdump
    stop_livox
    stop_radar
    stop_master_clock
    stop_bluetooth
#    stop_obd
    echo "All processes stopped"
}

# 处理 Ctrl+C 中断信号
trap ctrl_c INT

ctrl_c() {
    echo "** Trapped CTRL-C"
    stop_all
    exit 1
}

testfunc() {

         start_bluetooth &
	 BLUETOOTH_PID=$!

	 wait $BLUETOOTH_PID
	 start_obd &
	
}

# 主程序，根据命令行参数执行相应操作
if [ "$1" == "start" ]; then
    setup_all
    wait
    start_all
elif [ "$1" == "stop" ]; then
    stop_all
elif [ "$1" == "test" ]; then
    testfunc

else
    echo "Usage: $0 {start|stop}"
    exit 1
fi

# 循环等待，防止脚本退出
while :
do
    sleep 1
done


#!/bin/bash

SUDO_PASSWORD="openhub"

start_radar() {
	cd ~/Desktop/Muse-main/radar

	echo $SUDO_PASSWORD | sudo -S tcpdump -i any -tttt src host 192.168.16.2 and port 6172 -w "radar_$(date +%Y%m%d_%H%M%S).PCAP" &

	python read_radar.py &
	

}

start_radar


while :
do
	sleep 1
done 

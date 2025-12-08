#!/bin/bash

# lidar
cp ./lidar/lidar@.service /etc/systemd/system/lidar@.service

# camera
cp ./camera/camera@.service /etc/systemd/system/camera@.service

# # radar
# cp ./radar/radar@.service /etc/systemd/system/radar@.service

# obd
cp ./obd/obd@.service /etc/systemd/system/obd@.service

# communication
cp ./communication/gpsd_exporter/gpsd_exporter.service /etc/systemd/system/gpsd_exporter.service
cp ./communication/iperf/iperf_logger.service /etc/systemd/system/iperf_logger.service
cp ./communication/rm500u-manager/rm500u_logger.service /etc/systemd/system/rm500u_logger.service
cp ./communication/traceroute/traceroute_loggerV4.service /etc/systemd/system/traceroute_loggerV4.service
cp ./communication/traceroute/traceroute_loggerV6.service /etc/systemd/system/traceroute_loggerV6.service

# startup and poweroff service
cp ./muse_startup.service /etc/systemd/system/muse_startup.service
cp ./muse_shutdown.service /etc/systemd/system/muse_shutdown.service
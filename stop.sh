#!/bin/bash

systemctl stop lidar@*
systemctl stop camera@*
systemctl stop obd@*
# systemctl stop radar@*
systemctl stop gpsd_exporter
systemctl stop rm500u_logger
systemctl stop iperf_logger
systemctl stop traceroute_loggerV4
systemctl stop traceroute_loggerV6
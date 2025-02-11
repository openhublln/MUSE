#! /bin/bash

systemctl disable --now gpsd_exporter.service
systemctl disable --now iperf_logger.service
systemctl disable --now rm500u_logger.service
systemctl disable --now traceroute_loggerV4.service
systemctl disable --now traceroute_loggerV6.service


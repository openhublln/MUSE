#! /bin/bash

systemctl enable --now gpsd_exporter.service
systemctl enable --now iperf_logger.service
systemctl enable --now rm500u_logger.service
systemctl enable --now traceroute_loggerV4.service
systemctl enable --now traceroute_loggerV6.service


#! /bin/bash

python3 gpsd_exporter/initdatabase.py
python3 iperf/initdatabase.py
python3 rm500u-manager/initdatabase.py
python3 traceroute/initdatabase.py
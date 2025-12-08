MUSE Multi‑Sensor Capture Stack
===============================

This repository configures and runs the MUSE embedded multi‑sensor box (vehicle‑mounted). It orchestrates LiDAR, camera, OBD, GPS, modem diagnostics, network performance, and traceroute logging via systemd services. Radar capture is present but currently **WIP** and disabled by default.

## Accessing the device
- SSH: `ssh openhub@192.168.0.11`
- Code location: `/home/openhub/MUSE`
- Data location: `/home/openhub/data/<timestamp>/...`

## High‑level workflow
1. On boot, `muse_startup.service` runs `start.sh`.
2. `start.sh` creates a timestamped data directory under `/home/openhub/data/<TS>/`.
3. Services are started (LiDAR, camera, OBD, GPS exporter, modem monitor, iperf logger, traceroute V4/V6). Radar is commented out.
4. On shutdown, `muse_shutdown.service` runs `stop.sh` to stop all services.
5. When Wi‑Fi is connected, `start.sh` will rsync accumulated data to `data_store:DATA/`, prune emptied dirs, wait 120s, and power off if no user session is active.

## Services overview
- LiDAR (`lidar@<path>.service`)
  - Binaries: `/home/openhub/MUSE/lidar/build/control`, `/home/openhub/MUSE/lidar/build/acquisition`
  - Config: `/home/openhub/MUSE/lidar/config.json`
  - Output: `<run>/lidar/*.ply` (binary little‑endian PLY frames)
- Camera (`camera@<path>.service`)
  - Script: `/home/openhub/MUSE/camera/start_camera.sh %I`
  - Source: `/dev/video0`, MJPEG 2592x1944@20fps
  - Output: `<run>/camera/<timestamp>.mkv`
- OBD (`obd@<path>.service`)
  - Script: `/home/openhub/MUSE/obd/speed_OBD.py %I`
  - Input: `/dev/rfcomm1` (Bluetooth bound to vehicle OBD dongle)
  - Output: `<run>/obd/speed.csv` with timestamped speed samples
- GPS logger (`gpsd_exporter.service`)
  - Script: `/home/openhub/MUSE/communication/gpsd_exporter/gpsd_exporter.py`
  - Depends on gpsd; writes timeseries to MongoDB `gps.gps`
- Modem monitor (`rm500u_logger.service`)
  - Script: `/home/openhub/MUSE/communication/rm500u-manager/monitoring.py -i 30 /dev/ttyUSB2`
  - Writes signal/cell/temps/counters/USB net status to MongoDB `RM500U.*`
- Network performance (`iperf_logger.service`)
  - Script: `/home/openhub/MUSE/communication/iperf/iperf_logger.py -i 60 130.104.229.74`
  - Cycles UDP bitrates, stores raw iperf3 JSON to MongoDB `iperf.iperf`
- Traceroute (`traceroute_loggerV4.service`, `traceroute_loggerV6.service`)
  - Script: `/home/openhub/MUSE/communication/traceroute/traceroute_logger.py -i 30 <dest>`
  - Writes hops to MongoDB `traceroute.traceroute`
- Radar (**WIP**, services commented out)
  - Scripts: `/home/openhub/MUSE/radar/read_radar.py`, `kdm7.py`
  - Services exist but are not installed/started by default.

## Startup/shutdown hooks
- `muse_startup.service` (oneshot, WantedBy=basic.target) → `/home/openhub/MUSE/start.sh`
- `muse_shutdown.service` (oneshot, halt/reboot/shutdown targets) → `/home/openhub/MUSE/stop.sh`

## Data layout
`/home/openhub/data/<YYYY_MM_DD_HH_MM_SS>/`
- `lidar/` PLY frames
- `camera/` MKV recordings
- `obd/` `speed.csv`
- (Radar outputs would be under `radar/` if enabled)

MongoDB (local, default port 27017):
- `gps.gps` timeseries
- `RM500U.signal_strength`, `serving_cell`, `temperatures`, `data_counter`, `usbnet_ethernet_status`
- `iperf.iperf`
- `traceroute.traceroute`

## Installation / setup
Run on the device as root:
```bash
cd /home/openhub/MUSE
sudo ./install_services.sh
sudo systemctl daemon-reload
sudo systemctl enable muse_startup.service muse_shutdown.service
# Enable optional per-sensor services if you want them active at boot:
sudo systemctl enable lidar@ camera@ obd@ gpsd_exporter rm500u_logger iperf_logger traceroute_loggerV4 traceroute_loggerV6
```

Prereqs:
- MongoDB running locally.
- gpsd installed and configured for your GPS receiver.
- ffmpeg available.
- iperf3 and traceroute installed.
- Python venvs present at `/home/openhub/MUSE/.venv` or component venvs (gpsd_exporter has its own). Install `requirements.txt` there:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
- LiDAR: build Livox SDK2 targets (`lidar/build/control`, `lidar/build/acquisition`) per `lidar/Readme.md`.

## Operating services manually
- Start full stack: `sudo systemctl start muse_startup.service` (or reboot)
- Stop: `sudo systemctl start muse_shutdown.service` or `sudo systemctl stop lidar@* camera@* obd@* gpsd_exporter rm500u_logger iperf_logger traceroute_loggerV4 traceroute_loggerV6`
- Check status: `systemctl status <service>`
- Logs: `journalctl -u <service> -f`

### Running individual units with custom output paths
Example LiDAR:
```bash
sudo systemctl start lidar@/home/openhub/data/test/lidar
```
Camera:
```bash
sudo systemctl start camera@/home/openhub/data/test/camera
```
OBD (expects `/dev/rfcomm1` already bound):
```bash
sudo systemctl start obd@/home/openhub/data/test/obd
```

## Data sync / poweroff logic
In `start.sh`, if Wi‑Fi is connected on `wlp0s20f3`, data is rsynced to `data_store:DATA/` with `--remove-source-files`, empty directories are pruned, then after 120s the device powers off unless user `openhub` is logged in.

## Bluetooth / OBD pairing
- Address configured in `start.sh` (`BT_ADDRESS="66:1E:32:30:33:38"`).
- Bind: `rfcomm bind /dev/rfcomm1 $BT_ADDRESS`
- Expect scripts in `bluetooth/` can connect/disconnect via `bluetoothctl`.

## Database maintenance
- Initialize collections: `communication/init_db.sh`
- Clean all collections (destructive): `python3 communication/clean_db.py` (prompts for `yes`)

## Radar (WIP)
- Code: `radar/kdm7.py`, `radar/read_radar.py`
- Services exist (`radar@.service`) but are commented out in `install_services.sh` and `start.sh`. Enable only after completing and testing capture/storage paths.

## Editing the code remotely
1. SSH in: `ssh openhub@192.168.0.11`
2. Edit with your preferred editor (nano/vim) or use `scp`/`rsync` to sync changes.
3. After edits to services, run `sudo systemctl daemon-reload` and restart affected units.
4. Code lives in `/home/openhub/MUSE`; data in `/home/openhub/data`.

## Quick reference commands
- View running services: `systemctl --type=service | grep -E 'muse|lidar|camera|obd|gpsd_exporter|rm500u|iperf|traceroute|radar'`
- Tail logs: `journalctl -fu lidar@*`
- Check MongoDB contents (example): `mongosh --eval 'db.getSiblingDB("gps").gps.countDocuments()'`

## Requirements file
`requirements.txt` (pip):
- obd==0.7.3
- pymongo==4.15.3
- pyserial==3.4
- h5py==3.15.1

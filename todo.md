What to add to fully integrate radar:

1) Decide device path and map it into radar@.service (e.g., --port /dev/ttyUSB3), or pass via %I and consume it in the script.

2) Modify start.sh to create <run>/radar, chown it, and start radar@<run>/radar with the device arg.

3) Update read_radar.py to write into the provided output directory (parameterized) rather than a fixed filename; ideally create per-run files (e.g., timestamped HDF5) to avoid overwrite.

4) Ensure radar output lives under the run dir so rsync/poweroff picks it up.

6) Re-enable radar in install_services.sh and start.sh once the above is done.


#!/bin/bash

# setting the sudo password
SUDO_PASSWORD="openhub"

echo $SUDO_PASSWORD | sudo -S systemctl stop muse_camera.path
echo $SUDO_PASSWORD | sudo -S systemctl stop muse.service
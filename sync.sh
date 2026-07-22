#!/bin/bash

DATA_DIR="/DATA/"

rsync -acz --remove-source-files --stats $DATA_DIR data_store:/DATA/
find $DATA_DIR -type d -empty -delete
# power off as completed
sleep 120
# test if user is still logged in
if who | grep openhub; then
    echo "User openhub is logged in, not powering off."
    exit 0
fi
poweroff
exit 0

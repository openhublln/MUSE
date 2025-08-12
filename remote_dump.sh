#!/bin/bash

# Variables
LOCAL_DATA_DIR=~/MUSE
REMOTE_USER=openhub
REMOTE_IP=130.104.205.198
REMOTE_PORT=2222
REMOTE_PATH=/DATA
SSH_KEY=/home/openhub/MUSE/Keys/key

echo "Starting remote data sync..."

# Loop over all local DATA_* folders
for dir in "$LOCAL_DATA_DIR"/DATA_*; do
    if [ -d "$dir" ]; then
        FOLDER_NAME=$(basename "$dir")
        echo "Syncing $FOLDER_NAME to remote server..."

        # Rsync to remote server
        rsync -avz -e "ssh -p $REMOTE_PORT -i $SSH_KEY" \
            "$dir/" "$REMOTE_USER@$REMOTE_IP:$REMOTE_PATH/$FOLDER_NAME/"
    fi
done

echo "Remote data sync complete."
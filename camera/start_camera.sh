#!/bin/bash

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
OUTPUT=$1/${TIMESTAMP}.mkv

ffmpeg -f v4l2 -input_format mjpeg -framerate 20 -video_size 2592x1944 -i /dev/video0 -c:v copy ${OUTPUT}
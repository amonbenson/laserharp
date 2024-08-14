#!/bin/bash
set -eux

DEBIAN_FRONTEND=noninteractive

# Install the required packages
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-setuptools python3-pip python3-wheel

# Install libcamera2 and opencv
sudo apt-get install -y python3-picamera2 sudo python3-opencv --no-install-recommends

# Create a virtual environment
python3 -m venv --prompt laserharp --system-site-packages .venv
source .venv/bin/activate

# Install python dependencies
pip3 install -r requirements.txt

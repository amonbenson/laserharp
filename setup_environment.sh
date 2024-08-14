#!/bin/bash
set -eux

DEBIAN_FRONTEND=noninteractive
TZ=Europe/Berlin

# Install the required packages
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-setuptools python3-pip python3-wheel

# Install libcamera2 as a system package. This is the recommended way and avoids errors with missing headers.
#sudo apt-get install -y python3-libcamera python3-kms++
#sudo apt-get install -y qtbase5-dev qt5-qmake qtbase5-dev-tools python3-pyqt5 python3-prctl libatlas-base-dev ffmpeg libopenjp2-7 python3-pip libcap-dev

# Create a virtual environment
python3 -m venv --prompt laserharp .venv
source .venv/bin/activate

# Install numpy first. This is part of the libcamera2 installation instructions.
#pip3 install numpy --upgrade

# Install python dependencies
pip3 install --config-settings --confirm-license= --verbose -r requirements.txt

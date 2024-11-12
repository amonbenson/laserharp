#!/bin/bash
set -eux

DEBIAN_FRONTEND=noninteractive

# Install the required packages
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-setuptools python3-pip python3-wheel nginx

# Install libcamera2 and opencv
sudo apt-get install -y --no-install-recommends python3-picamera2 sudo python3-opencv

# Create a virtual environment
python3 -m venv --prompt laserharp --system-site-packages .venv
source .venv/bin/activate

# Install python requirements
pip3 install -r requirements.txt

# Install node, npm, and yarn via nvm (node version manager)
set +eux

curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

nvm install --lts
npm install -g yarn

set -eux

# Install frontend requirements
yarn --cwd frontend install

# allow user to run shutdown without password
sudo chmod u+s /sbin/poweroff /sbin/reboot /sbin/shutdown

set +eux
source ~/.bashrc

#!/bin/bash
set -eux

DEBIAN_FRONTEND=noninteractive

# stop related services
sudo systemctl stop nginx || true
sudo systemctl stop laserharp_ap || true
sudo systemctl stop laserharp || true

# build and install frontend
cd frontend
VITE_WS_HOST=http://laserharp.local yarn build
sudo rm -rf /var/www/html
sudo mkdir -p /var/www/html
sudo cp -r dist/* /var/www/html
cd ..

# install nginx config
sudo cp ./scripts/nginx.conf /etc/nginx/sites-available/laserharp.local

sudo rm -rf /etc/nginx/sites-enabled/*
sudo ln -s /etc/nginx/sites-available/laserharp.local /etc/nginx/sites-enabled/laserharp.local

# build and install laserharp service
sudo mkdir -p /etc/laserharp
sudo rm -rf /etc/laserharp/venv
sudo python3 -m venv /etc/laserharp/venv --system-site-packages # setup virtualenv
sudo /etc/laserharp/venv/bin/python3 -m pip install --upgrade pip
sudo /etc/laserharp/venv/bin/python3 -m pip install -r requirements.txt
sudo /etc/laserharp/venv/bin/python3 -m pip install gunicorn
sudo /etc/laserharp/venv/bin/python3 -m pip install -e .

sudo cp ./scripts/laserharp.service /etc/systemd/system/laserharp.service
sudo systemctl enable laserharp
sudo systemctl daemon-reload

# TODO: setup access point

# start services
sudo systemctl start nginx
sudo systemctl start laserharp

sudo systemctl enable nginx
sudo systemctl enable laserharp

# print service status
sudo systemctl status --no-pager nginx
sudo systemctl status --no-pager laserharp

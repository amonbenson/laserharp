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
pip3 install gunicorn git+https://github.com/amonbenson/perci.git --break-system-packages
pip3 install . --break-system-packages
sudo cp ./scripts/laserharp.service /etc/systemd/system/laserharp.service
sudo systemctl enable laserharp
sudo systemctl daemon-reload

# install access point service
sudo cp ./scripts/laserharp_ap.service /etc/systemd/system/laserharp_ap.service
sudo systemctl enable laserharp_ap
sudo systemctl daemon-reload

# start services
sudo systemctl start nginx
sudo systemctl start laserharp_ap
sudo systemctl start laserharp

sudo systemctl enable nginx
sudo systemctl enable laserharp_ap
sudo systemctl enable laserharp

# print service status
sudo systemctl status --no-pager nginx
sudo systemctl status --no-pager laserharp_ap
sudo systemctl status --no-pager laserharp

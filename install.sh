#!/bin/bash
set -eux

# stop related services
sudo systemctl stop nginx || true
sudo systemctl stop laserharp || true

# build and install frontend
cd frontend
VITE_WS_HOST=http://laserharp.local yarn build
sudo rm -rf /var/www/html
sudo mkdir -p /var/www/html
sudo cp -r dist/* /var/www/html
cd ..

# build and install laserharp service
pip3 install . --break-system-packages
sudo cp laserharp.service /etc/systemd/system/laserharp.service
sudo systemctl enable laserharp
sudo systemctl daemon-reload

# install nginx config
sudo cp nginx.conf /etc/nginx/sites-available/laserharp.local

sudo rm -rf /etc/nginx/sites-enabled/*
sudo ln -s /etc/nginx/sites-available/laserharp.local /etc/nginx/sites-enabled/laserharp.local

# start services
sudo systemctl start nginx
sudo systemctl start laserharp

sudo systemctl enable nginx
sudo systemctl enable laserharp

# print service status
sudo systemctl status nginx
sudo systemctl status laserharp

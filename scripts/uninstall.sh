#!/bin/bash
set -eux

# stop related services
sudo systemctl stop nginx
sudo systemctl stop laserharp

sudo systemctl disable nginx
sudo systemctl disable laserharp

# invoke kill script
./scripts/kill.sh

# remove frontend
sudo rm -rf /var/www/html

# remove nginx config
sudo rm -rf /etc/nginx/sites-available/laserharp.local
sudo rm -rf /etc/nginx/sites-enabled/laserharp.local

@list:
    just --list

[private]
setup_apt_packages:
    @echo "Updating and upgrading system packages..."
    sudo apt-get update
    sudo apt-get upgrade -y
    sudo apt-get dist-upgrade -y

    @echo "Installing required packages..."
    sudo apt-get install -y \
        build-essential \
        git \
        nginx \
        python3-pip \
        python3-venv \
        python3-opencv

    @echo "Cleaning up unused packages..."
    sudo apt-get autoremove -y
    sudo apt-get autoclean -y

[private]
setup_serial:
    @echo "Updating firmware..."
    sudo rpi-update

[private]
setup_venv:
    @echo "Setting up global python virtual environment..."
    python3 -m venv .venv --system-site-packages

    @echo "Installing pip dependencies..."
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt

[private]
setup_deno:
    @echo "Installing Deno..."
    curl -fsSL https://deno.land/x/install/install.sh | sh -s -- -y

setup: setup_apt_packages setup_serial setup_venv setup_deno
    @echo "Setup complete."

[private]
stop_services:
    @echo "Stopping all services..."
    sudo systemctl stop laserharp.service || true
    sudo systemctl stop nginx || true

    sudo systemctl disable laserharp.service || true
    sudo systemctl disable nginx || true

    sudo systemctl daemon-reload

[private]
start_services:
    @echo "Starting all services..."
    sudo systemctl enable laserharp.service
    sudo systemctl enable nginx

    sudo systemctl daemon-reload

    sudo systemctl start laserharp.service
    sudo systemctl start nginx

    sudo systemctl status --no-pager laserharp.service
    sudo systemctl status --no-pager nginx

[private]
install_nginx:
    @echo "Installing nginx config..."
    sudo cp ./scripts/nginx.conf /etc/nginx/sites-available/laserharp.local
    sudo rm -rf /etc/nginx/sites-enabled/*
    sudo ln -s /etc/nginx/sites-available/laserharp.local /etc/nginx/sites-enabled/laserharp.local

[private]
uninstall_nginx:
    @echo "Uninstalling nginx config..."
    sudo rm -f /etc/nginx/sites-available/laserharp.local
    sudo rm -f /etc/nginx/sites-enabled/laserharp.local

[private]
install_laserharp:
    @echo "Installing laserharp service..."
    sudo cp ./scripts/laserharp.service /etc/systemd/system/laserharp.service

[private]
uninstall_laserharp:
    @echo "Uninstalling laserharp service..."
    sudo rm -f /etc/systemd/system/laserharp.service

[private]
install_frontend:
    @echo "Building and installing frontend..."
    cd frontend && deno install
    cd frontend && VITE_WS_HOST=http://laserharp.local deno run build

    sudo rm -rf /var/www/html
    sudo mkdir -p /var/www/html
    sudo cp -r frontend/dist/* /var/www/html/

[private]
uninstall_frontend:
    @echo "Uninstalling frontend..."
    sudo rm -rf /var/www/html

install: stop_services install_laserharp install_frontend install_nginx start_services
    @echo "Installation complete."

uninstall: stop_services uninstall_laserharp uninstall_frontend uninstall_nginx
    @echo "Uninstallation complete."

log:
    @echo "Following laserharp service logs..."
    journalctl --follow -u laserharp.service

laserharp_dev:
    /home/pi/laserharp/.venv/bin/python3 -m laserharp.server --no-send-standby

frontend_dev:
    cd frontend && deno run dev --host

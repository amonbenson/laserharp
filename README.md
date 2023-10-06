### Install precompiled opencv
```bash
wget https://github.com/prepkg/opencv-raspberrypi/releases/download/4.8.0/opencv.deb
sudo apt install -y ./opencv.deb
```

### Bluetooth Midi Installation
see https://neuma.studio/raspberry-pi-as-usb-bluetooth-midi-host/

Recompile bluez stack to include midi support.

```bash
git clone https://github.com/oxesoft/bluez
sudo apt-get install -y autotools-dev libtool autoconf
sudo apt-get install -y libasound2-dev
sudo apt-get install -y libusb-dev libdbus-1-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev
cd bluez
./bootstrap
./configure --enable-midi --prefix=/usr --mandir=/usr/share/man --sysconfdir=/etc --localstatedir=/var
make
sudo make install
```

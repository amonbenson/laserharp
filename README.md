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

#### Alternative
https://scribles.net/updating-bluez-on-raspberry-pi-from-5-43-to-5-50/
(Note: Fix for error during compilation: https://github.com/LibtraceTeam/libtrace/issues/117#issuecomment-1024508895)
(Note: add `--enable-midi` to `./configure` command)

Enable `LE only` Mode
```bash
sudo btmgmt power off
sudo btmgmt le on
sudo btmgmt bredr off
sudo btmgmt power on
```


Use needs to be addded to the bluetooth group
```bash
sudo usermod -G bluetooth -a $USER
```


### Raspberry Pi Performance Improvements:

see https://wiki.linuxaudio.org/wiki/raspberrypi

```bash
for cpu in /sys/devices/system/cpu/cpu[0-9]*; do echo -n performance \
| sudo tee $cpu/cpufreq/scaling_governor; done
```

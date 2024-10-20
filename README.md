[![Backend Tests](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/backend.yaml/badge.svg)](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/backend.yaml)
[![Frontend Tests](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/frontend.yaml/badge.svg)](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/frontend.yaml)
[![Firmware Tests](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/firmware.yaml/badge.svg)](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/firmware.yaml)


## Development Setup

### Backend

Setup a virtual environment and install the dependencies:
```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements.txt
```

Run the server in development mode:
```bash
source .venv/bin/activate
python -m laserharp.server
```

### Frontend

Install node js and yarn:
```bash
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
nvm install --lts
nvm use --lts
npm install -g yarn
```

Install all dependencies:
```bash
cd frontend
yarn install
```

Run the development server:
```bash
yarn dev
```


## Raspberry Pi Performance Improvements:

see https://wiki.linuxaudio.org/wiki/raspberrypi

```bash
for cpu in /sys/devices/system/cpu/cpu[0-9]*; do echo -n performance \
| sudo tee $cpu/cpufreq/scaling_governor; done
```

## Raspberry Pi Reduce Power Consumption

see https://www.jeffgeerling.com/blog/2023/reducing-raspberry-pi-5s-power-consumption-140x

```bash
# sudo rpi-eeprom-config -e
[all]
BOOT_UART=1
WAKE_ON_GPIO=0
POWER_OFF_ON_HALT=1
```

## Midi uart
- do a `rpi-update` to get the latest kernel firmware
- add to `/boot/firmware/config.txt`:
```
dtoverlay=uart2-pi5
dtoverlay=midi-uart2-pi5
```

## Power via GPIO header
http://blog.dddac.com/wp-content/uploads/Flash-RPi5-and-adding-5000mA-Line-tutorial.pdf

## Diode to Note Mapping

- Root note: C3 (midi note 48, one octave below middle C)
- Global transpose setting

- Modes:
    - **Pedal Harp**: For each note, choose one of:
        - flat
        - natural
        - sharp
    - **Custom Scale**:
        - each diode can be assigned to a specific midi note

- The harp is divided into three horizontal sections resulting in 3 different octave ranges

## MIDI In Messages

:heavy_check_mark: &ndash; Implemented<br>
:x: &ndash; Not implemented

### Set Laser Brightness Directly (:x:)
```
Host -> Laserharp: 0x90 <note> <velocity>
```
Set the brightness of the laser corresponding to the note to the velocity value. Note that multiple notes may control the same laser diode depending on the section spacing. A note value of 127 will set the brightness of all lasers at once.

### Set Laser Brightness Directly (:x:)
```
Host -> Laserharp: 0x80 <note> <velocity>
```
Turn off the laser corresponding to the note. A note value of 127 will turn off all lasers at once.

### Set Unplucked Laser Brightness (:x:)
```
Host -> Laserharp: 0xb0 102 <brightness>
```
Set the brightness for unplucked lasers.

### Set Plucked Laser Brightness (:x:)
```
Host -> Laserharp: 0xb0 103 <brightness>
```
Set the brightness when a laser is plucked.



## IPC Protocol

:heavy_check_mark: &ndash; Implemented<br>
:x: &ndash; Not implemented

### USB Midi (RPi: :x:, STM: :heavy_check_mark:)
```
Bidirectional: 0x0N <byte0> <byte1> <byte2>
```

### Din Midi (RPi: :x:, STM: :heavy_check_mark:)
_Note: With the current version, Din Midi is handled directly by the Raspberry Pi, so this message won't be used._
```
Bidirectional: 0x1N <byte0> <byte1> <byte2>
```

### Set Brightness for Single Laser (:heavy_check_mark:)
```
RPi -> STM: 0x80 <diode_index> <brightness> 0x00
```

### Set Brightness for All Lasers (:heavy_check_mark:)
```
RPi -> STM: 0x81 <brightness> 0x00 0x00
```

### Firmware Version Inquiry (:x:)
```
RPi -> STM: 0xf0 0x00 0x00 0x00
STM -> RPi: 0xf0 <major> <minor> <patch>
```

### Reboot STM (:x:)
```
RPi -> STM: 0xf1 0x00 0x00 0x00
```

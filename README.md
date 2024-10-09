[![Backend Tests](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/rpi-backend.yaml/badge.svg)](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/rpi-backend.yaml)
[![Frontend Tests](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/rpi-frontend.yaml/badge.svg)](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/rpi-frontend.yaml.yaml)
[![Firmware Tests](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/stm.yaml/badge.svg)](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/stm.yaml.yaml)


## Development Setup

### Backend
```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ../perci

python -m laserharp.server
```

### Frontend
```bash
cd frontend
yarn install

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

### Set Laser Brightness Directly
```
Host -> Laserharp: 0x90 <note> <velocity>
```
Set the brightness of the laser corresponding to the note to the velocity value. Note that multiple notes may control the same laser diode depending on the section spacing. A note value of 127 will set the brightness of all lasers at once.

### Set Laser Brightness Directly
```
Host -> Laserharp: 0x80 <note> <velocity>
```
Turn off the laser corresponding to the note. A note value of 127 will turn off all lasers at once.

### Set Unplucked Laser Brightness
```
Host -> Laserharp: 0xb0 102 <brightness>
```
Set the brightness for unplucked lasers.

### Set Plucked Laser Brightness
```
Host -> Laserharp: 0xb0 103 <brightness>
```
Set the brightness when a laser is plucked.

## IPC Protocol

### USB Midi
```
Bidirectional: 0x0N <byte0> <byte1> <byte2>
```

### Din Midi (Unused)
```
Bidirectional: 0x1N <byte0> <byte1> <byte2>
```

### Set Brightness for Single Laser
```
RPi -> STM: 0x80 <diode_index> <brightness> 0x00
```

### Set Brightness for All Lasers
```
RPi -> STM: 0x81 <brightness> 0x00 0x00
```

### Firmware Version Inquiry
```
RPi -> STM: 0xf0 0x00 0x00 0x00
STM -> RPi: 0xf0 <major> <minor> <patch>
```

### Reboot STM
```
RPi -> STM: 0xf1 0x00 0x00 0x00
```

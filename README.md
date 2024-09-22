[![Backend Tests](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/rpi-backend.yaml/badge.svg)](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/rpi-backend.yaml)
[![Frontend Tests](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/rpi-frontend.yaml/badge.svg)](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/rpi-frontend.yaml.yaml)
[![Firmware Tests](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/stm.yaml/badge.svg)](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/stm.yaml.yaml)


## Raspberry Pi Performance Improvements:

see https://wiki.linuxaudio.org/wiki/raspberrypi

```bash
for cpu in /sys/devices/system/cpu/cpu[0-9]*; do echo -n performance \
| sudo tee $cpu/cpufreq/scaling_governor; done
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

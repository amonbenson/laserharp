[![Backend Tests](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/rpi-backend.yaml/badge.svg)](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/rpi-backend.yaml)
[![Frontend Tests](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/rpi-frontend.yaml/badge.svg)](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/rpi-frontend.yaml.yaml)
[![Firmware Tests](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/stm.yaml/badge.svg)](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/stm.yaml.yaml)


### Raspberry Pi Performance Improvements:

see https://wiki.linuxaudio.org/wiki/raspberrypi

```bash
for cpu in /sys/devices/system/cpu/cpu[0-9]*; do echo -n performance \
| sudo tee $cpu/cpufreq/scaling_governor; done
```

### Midi uart
- do a `rpi-update` to get the latest kernel firmware
- add to `/boot/firmware/config.txt`: `dtoverlay=midi-uart2-pi5`

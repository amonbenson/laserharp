[![Test](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/test.yaml/badge.svg)](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/test.yaml)
[![Lint](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/lint.yaml/badge.svg)](https://github.com/amonbenson/laserharp-rpi-py/actions/workflows/lint.yaml)


### Raspberry Pi Performance Improvements:

see https://wiki.linuxaudio.org/wiki/raspberrypi

```bash
for cpu in /sys/devices/system/cpu/cpu[0-9]*; do echo -n performance \
| sudo tee $cpu/cpufreq/scaling_governor; done
```

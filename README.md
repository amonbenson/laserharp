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

## Allow current user to shutdown
```bash
sudo chmod u+s /sbin/poweroff /sbin/reboot /sbin/shutdown
```

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

### Set Laser Brightness Directly :x:
```
Host -> Laserharp: 0x90 <note> <velocity>
```
Set the brightness of the laser corresponding to the note to the velocity value. Note that multiple notes may control the same laser diode depending on the section spacing. A note value of 127 will set the brightness of all lasers at once.

### Set Laser Brightness Directly :x:
```
Host -> Laserharp: 0x80 <note> <velocity>
```
Turn off the laser corresponding to the note. A note value of 127 will turn off all lasers at once.

### Set Unplucked Laser Brightness :x:
```
Host -> Laserharp: 0xb0 102 <brightness>
```
Set the brightness for unplucked lasers.

### Set Plucked Laser Brightness :x:
```
Host -> Laserharp: 0xb0 103 <brightness>
```
Set the brightness when a laser is plucked.



## IPC Protocol

:heavy_check_mark: &ndash; Implemented<br>
:x: &ndash; Not implemented

### USB Midi :x:

```
Bidirectional: 0x0N <byte0> <byte1> <byte2>
```

These packets are equivalent to the USB Midi Protocol with `CN = 1`.

### Din Midi :x:

```
Bidirectional: 0x1N <byte0> <byte1> <byte2>
```

_Note: With the current version, Din Midi is handled directly by the Raspberry Pi, so this message won't be used._

These packets are equivalent to the USB Midi Protocol with `CN = 1`.

### Set Brightness of a Single Laser :heavy_check_mark:

```
RPi -> STM: 0x80 <diode_index> <brightness> <fade_duration>
```

Set the brightness of a single laser diode. The fade duration is given in tenths of a second. E.g. a value of 20 will fade the laser to the new brightness over 2 seconds. A duration of 0 will set the brightness immediately.

### Set Brightness of All Lasers :heavy_check_mark:

```
RPi -> STM: 0x81 <brightness> <fade_duration> <unused>
```

Set the brightness of all laser diodes. The fade duration is given in tenths of a second. E.g. a value of 20 will fade the lasers to the new brightness over 2 seconds. A duration of 0 will set the brightness immediately.

### Get Brightness of a Single Laser :heavy_check_mark:

```
RPi -> STM: 0x82 <diode_index> <unused> <unused>
STM -> RPi: 0x82 <diode_index> <brightness> <unused>
```

### Play Animation :heavy_check_mark:

```
RPi -> STM: 0x83 <animation_id> <duration> <follow_action>
```

Play one of the predefined animations.

**Animation Ids**:<br>
0 &ndash; **Boot animation** &ndash; Played during powerup of the Raspberry Pi<br>
1 &ndash; **Flip animation** &ndash; Played when flipping the harp view<br>
2 &ndash; **Test animation** &ndash; Used for internal testing, alternates between diodes 4 and 5

**Duration**: Given in tenths of a second. E.g. a value of 20 will play the animation for 2 seconds.

**Follow Actions**:<br>
0 &ndash; **Loop** &ndash; Loop the animation indefinitely<br>
1 &ndash; **Freeze** &ndash; Play the animation once and stop on the last frame<br>
2 &ndash; **Off** &ndash; Play the animation once and stop with all lasers off<br>
3 &ndash; **Restore** &ndash; Play the animation once and restore the laser brightnesses

### Stop Animation :heavy_check_mark:

```
RPi -> STM: 0x84 <unused> <unused> <unused>
```

Stop the current animation from playing and execute the follow action immediately. If the follow action was set to 0 (loop indefinitely), the animation will stop and the lasers will remain in their current state.

### Calibration Button Pressed :heavy_check_mark:

```
STM -> RPi: 0x90 <state_0> <state_1> <state_2>
```

Sent when the calibration button is pressed. The states are given as follows:
0 &ndash; released<br>
1 &ndash; short press<br>
2 &ndash; long press

For example, if the button is short-pressed, then long-pressed, and then released, the states will be `0x01 0x02 0x00`.

### Get Voltage :heavy_check_mark:

```
RPi -> STM: 0x91 <00> <unused> <unused>
STM -> RPi: 0x91 <00> <voltage_int> <voltage_frac>
```

Returns the current voltage. Currently only the Laser Diode voltage (index 0) can be measured. The result is given as a decimal number with a resolution of 0.01V and can be calculated as follows:

```python
voltage = voltage_int + voltage_frac / 100
```

### Firmware Version Inquiry :heavy_check_mark:

```
RPi -> STM: 0xf0 <unused> <unused> <unused>
STM -> RPi: 0xf0 <major> <minor> <patch>
```

### Reboot STM :heavy_check_mark:

```
RPi -> STM: 0xf1 <unused> <unused> <unused>
```

### Enter Standby :heavy_check_mark:

```
RPi -> STM: 0xf2 <fade_delay> <fade_duration> <unused>
```

Starts by playing the boot animation, waits for the fade delay, and then fades the lasers to black over the fade duration. Both delay and duration are given in tenths of a second.

**Important: This is intended to be used when the harp is turned off. It will block any further IPC commands and the STM will not respond until it is power cycled.**

## TODO Software

### Pedal Mutes

- Each Pedal Switch should have a "mute" button. If a string is muted, its corresponding laser will be turned on very dimly and no sound will be produced for that string.

### Direct Laser Control

- The brightness of each laser should be directly controllable via Note On Messages.
- Velocity 1 will map to 0% brightness, velocity 127 will map to 100% brightness.
- Velocity 0 / Note Off will return to normal operation and use the internally calculated laser brightness
- If a laser is currently in "normal operation" mode, the color will be determined by the "unplucked", "plucked", and "muted" brightness settings.

### Section Mode / Section Transpose (formally Section Octave Spacing)

- Sections can be set to different modes.
    - Off &ndash; There are no different sections. Each laser will produce a single note.
    - Alterate &ndash; The upper section will play one semitone higher while the lower section will play one semitone lower.
    - Single Octave &ndash; The upper section will play one octave higher while the lower section will play one octave lower.
    - Double Octave &ndash; The upper section will play two octaves higher while the lower section will play two octaves lower.
- Internally, the section mode is stored as a number of semitones.
- This should also be controllable via a Control Change Message

### Global Transpose

- Instead of setting the root note, a fixed root note (e.g. C3) will be used and a global transpose setting will offset that root note.

### Direct Pedal/Mute Control

- Using Control Change Messages, the pedal position and mutes can be controlled.

### Predefined Scales

- Each predefined scale controls the pedal positions and mutes for each note.
- Can be selected using Bank Change Messages (CC 0).
- Additional custom scales can be defined and stored internally.

- For each scale, choose:
    - Pitch: `C C# D D# E F F# G G# A A# B`
    - Modes (see https://en.wikipedia.org/wiki/List_of_musical_scales_and_modes):
        - Lydian Dominant &ndash; `1 2 3 #4 5 6 b7`

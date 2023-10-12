import time
from . import BleMidi


if __name__ == '__main__':
    # start the btmidi-server background process
    ble_midi = BleMidi()
    ble_midi.start()

    # wait util Ctrl+C is pressed
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ble_midi.stop()

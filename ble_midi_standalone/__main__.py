from time import sleep
import mido
from . import BleMidi, BleMidiPacket


if __name__ == '__main__':
    # start the ble midi service
    ble_midi = BleMidi()
    ble_midi.start()

    # run until keyboard interrupt
    try:
        while True:
            ble_midi.send(BleMidiPacket.from_message(mido.Message('note_on', note=60, velocity=127)))
            sleep(0.5)

            ble_midi.send(BleMidiPacket.from_message(mido.Message('note_off', note=60)))
            sleep(0.5)
    except KeyboardInterrupt:
        ble_midi.stop()

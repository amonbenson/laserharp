import threading
from queue import Queue
import mido
import time
import numpy as np
import traceback
from .ipc import IPCController
from .camera import Camera, InterceptionEvent
from .midi import MidiEvent


NUM_LASERS = 24
LASER_MAX = 63

CAMERA_FRAMERATE = 60

IPC_CN_DIN = 0
IPC_CN_USB = 1
IPC_CN_BLE = 2
IPC_CN_LASER_BRIGHTNESS = 3


class LaserHarpApp:
    def __init__(self):
        self.running = False
        self.note_status = np.zeros(NUM_LASERS, dtype=np.uint8)

        # use hardware serial to interface with the STM
        self.ipc = IPCController('/dev/ttyS0', baudrate=115200)
        self.ipc_thread = threading.Thread(target=self._ipc_loop)
        self.ipc_thread.daemon = True

        # setup camera interface
        self.camera = Camera(framerate=CAMERA_FRAMERATE, N_beams=NUM_LASERS)
        self.interception_thread = threading.Thread(target=self._interception_loop)
        self.interception_thread.daemon = True

    def send_din_midi(self, message: mido.Message):
        self.ipc.send(MidiEvent(IPC_CN_DIN, message))

    def send_usb_midi(self, message: mido.Message):
        self.ipc.send(MidiEvent(IPC_CN_USB, message))

    def send_ble_midi(self, message: mido.Message):
        # TODO: implement BLE
        pass

    def set_laser(self, index: int, brightness: int):
        self.ipc.send(MidiEvent(IPC_CN_LASER_BRIGHTNESS, mido.Message('note_on', note=index, velocity=brightness)))

    def set_all_lasers(self, brightness: int):
        self.ipc.send(MidiEvent(IPC_CN_LASER_BRIGHTNESS, mido.Message('note_on', note=127, velocity=brightness)))

    def start(self):
        if self.running: return

        # start all threads
        self.running = True
        self.ipc_thread.start()
        self.interception_thread.start()

        # start the camera interface
        self.camera.start()

        # enable all lasers
        self.set_all_lasers(LASER_MAX)

    def stop(self):
        if not self.running: return

        # stop the camera interface
        self.camera.stop()

        # stop all threads
        self.running = False
        self.ipc_thread.join(timeout=0.1)
        self.interception_thread.join(timeout=0.1)

    def _interception_loop(self):
        while self.running:
            try:
                # handle any incoming events
                interception_event = self.camera.read()
                self._handle_interception_event(interception_event)

            except Exception as e:
                traceback.print_exc()
                print(f"Unhandled exception in camera event loop: {e}")

    def _ipc_loop(self):
        while self.running:
            try:
                for event in self.ipc.read_all():

                    # STM handles USB and DIN midi, so this is the only cable number we expect to receive
                    if event.cable_number in [IPC_CN_DIN, IPC_CN_USB]:
                        self._handle_midi_event(event)
                    else:
                        print(f"Received unknown IPC packet: {event.cable_number :02x} {event.message.bytes().hex(' ')}")

            except Exception as e:
                traceback.print_exc()
                print(f"Unhandled exception in IPC event loop: {e}")

    def _handle_midi_event(self, event: MidiEvent):
        # handle midi note on/off messages from any interface
        if event.message.type == 'note_on':
            index = event.message.note
            brightness = min(LASER_MAX, event.message.velocity)
        elif event.message.type == 'note_off':
            index = event.message.note
            brightness = 0
        else:
            print(f"Unhandled midi event: {event}")
            return

        # set the laser brightness (this will send an IPC packet to the STM)
        if index <= NUM_LASERS:
            self.set_laser(index, brightness)
        elif index == 127:
            self.set_all_lasers(brightness)
        else:
            print(f"Received midi note out of range: {index}")
            return

    def _handle_interception_event(self, event: InterceptionEvent):
        #print(event.beamlength)

        # set note status to 127 if the beamlength is not nan/inf
        new_note_status = np.where(np.isfinite(event.beamlength), 127, 0).astype(np.uint8)

        # send midi note on/off messages for each laser to all interfaces
        for i in range(NUM_LASERS):
            if new_note_status[i] != self.note_status[i]:
                cmd = 'note_on' if new_note_status[i] else 'note_off'
                note = i
                velocity = new_note_status[i]

                message = mido.Message(cmd, note=note, velocity=velocity)
                self.send_din_midi(message)
                self.send_usb_midi(message)
                self.send_ble_midi(message)

        # update note status
        np.copyto(self.note_status, new_note_status)

#import threading
#from queue import Queue
from multiprocessing import Process, Queue
import mido
import time
import numpy as np
import traceback
from .ipc import IPCController
from .camera import Camera, InterceptionEvent
from .midi import MidiEvent


NUM_LASERS = 24

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

        # setup camera interface
        self.camera = Camera(framerate=CAMERA_FRAMERATE, N_beams=NUM_LASERS)

        # setup processes
        self.ipc_proc = Process(target=self._ipc_loop)
        self.interception_proc = Process(target=self._interception_loop)

    def send_din_midi(self, message: mido.Message):
        self.ipc.send(MidiEvent(IPC_CN_DIN, message))

    def send_usb_midi(self, message: mido.Message):
        self.ipc.send(MidiEvent(IPC_CN_USB, message))

    def send_ble_midi(self, message: mido.Message):
        # TODO: implement BLE
        pass

    def set_laser(self, index: int, brightness: int):
        self.ipc.send(MidiEvent(IPC_CN_LASER_BRIGHTNESS, mido.Message('control_change', control=index, value=brightness)))

    def set_all_lasers(self, brightness: int):
        self.ipc.send(MidiEvent(IPC_CN_LASER_BRIGHTNESS, mido.Message('control_change', control=127, value=brightness)))

    def start(self):
        if self.running: return

        # start all threads
        self.running = True
        self.ipc_proc.start()
        self.interception_proc.start()

        # start the camera interface
        self.camera.start()

        # enable all lasers
        self.set_all_lasers(127)

        print("Running")

    def stop(self):
        if not self.running: return

        # stop all threads
        self.running = False
        self.ipc_proc.join()
        self.interception_proc.join()

        # stop the camera interface
        self.camera.stop()

        # stop IPC
        self.ipc.stop()

    def _interception_loop(self):
        while self.running:
            try:
                # handle any incoming events
                event = self.camera.read(timeout=0.1)
                if event is None:
                    continue

                self._handle_interception_event(event)

            except Exception as e:
                traceback.print_exc()
                print(f"Unhandled exception in camera event loop: {e}")

    def _ipc_loop(self):
        while self.running:
            try:
                event = self.ipc.read(timeout=0.1)
                if event is None:
                    continue

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
            brightness = event.message.velocity
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

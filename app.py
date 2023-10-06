import threading
from queue import Queue
import mido
import time
from .ipc import IPCController, IPCPacket
from .midi import MidiEvent, MidiInterface


NUM_LASERS = 24
LASER_MAX = 63


class LaserHarpApp:
    def __init__(self):
        # use hardware serial for IPC
        self.ipc = IPCController('/dev/ttyS0', baudrate=115200)
        self.ipc_thread = threading.Thread(target=self._ipc_loop)
        self.ipc_thread.daemon = True

        self.running = False
        self.midi_queue = Queue()
        self.midi_thread = threading.Thread(target=self._midi_loop)
        self.midi_thread.daemon = True

    def start(self):
        if self.running: return

        # start all threads
        self.running = True
        self.ipc_thread.start()
        self.midi_thread.start()

        # enable all lasers
        self.ipc.set_all_lasers(LASER_MAX)

    def stop(self):
        if not self.running: return

        self.running = False
        self.ipc_thread.join(timeout=0.1)
        self.midi_thread.join(timeout=0.1)

    def _ipc_loop(self):
        while self.running:
            packet = self.ipc.read()

            # STM handles USB midi messages, so this is the only command type we expect to receive
            if packet.cmd in [IPCPacket.Command.MIDI_DIN, IPCPacket.Command.MIDI_USB]:
                self.midi_queue.put(packet.midi())
            else:
                print(f"Received unknown IPC packet: {packet.bytes().hex(' ')}")

    def _midi_loop(self):
        while self.running:
            event = self.midi_queue.get()
            print(event)

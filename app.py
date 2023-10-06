import threading
from queue import Queue
import mido
from .ipc import IPCController, IPCPacket
from .midi import MidiEvent, MidiInterface


class LaserHarpApp:
    def __init__(self):
        # use hardware serial for IPC
        self.ipc = IPCController('/dev/ttyAMA0', baudrate=115200)
        self.ipc_thread = threading.Thread(target=self._ipc_loop)

        self.midi_queue = Queue()

        self._loop()

    def _ipc_loop(self):
        while True:
            packet = self.ipc.read()

            # STM handles USB midi messages, so this is the only command type we expect to receive
            if packet.cmd == IPCPacket.Command.MIDI_USB:
                self.midi_queue.put(MidiEvent(MidiInterface.USB, packet.midi()))
            else:
                print(f"Received unknown IPC packet: {packet.bytes()}")

    def _loop(self):
        self.ipc.send_midi(MidiEvent(MidiInterface.USB, mido.Message('note_on', note=60, velocity=64)))

        print("Start handling midi messages...")
        while True:
            event = self.midi_queue.get()
            print(event)

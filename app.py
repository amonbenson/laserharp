import threading
from queue import Queue
import mido
import time
from .ipc import IPCController, IPCPacket
from .camera import Camera
from .midi import MidiEvent, MidiInterface


NUM_LASERS = 24
LASER_MAX = 63

CAMERA_FRAMERATE = 60


class LaserHarpApp:
    def __init__(self):
        # use hardware serial to interface with the STM
        self.ipc = IPCController('/dev/ttyS0', baudrate=115200)
        self.ipc_thread = threading.Thread(target=self._ipc_loop)
        self.ipc_thread.daemon = True

        # setup camera interface
        self.camera = Camera(framerate=CAMERA_FRAMERATE)
        self.interception_thread = threading.Thread(target=self._interception_loop)
        self.interception_thread.daemon = True

        self.running = False
        self.event_queue = Queue()
        self.event_thread = threading.Thread(target=self._event_loop)
        self.event_thread.daemon = True

    def start(self):
        if self.running: return

        # start all threads
        self.running = True
        self.ipc_thread.start()
        self.interception_thread.start()
        self.event_thread.start()

        # start the camera interface
        self.camera.start()

        # enable all lasers
        self.ipc.set_all_lasers(LASER_MAX)

    def stop(self):
        if not self.running: return

        # stop the camera interface
        self.camera.stop()

        # stop all threads
        self.running = False
        self.ipc_thread.join(timeout=0.1)
        self.interception_thread.join(timeout=0.1)
        self.event_thread.join(timeout=0.1)

    def _interception_loop(self):
        while self.running:
            # queue any incoming events
            interception_event = self.camera.read()
            self.event_queue.put(interception_event)

    def _ipc_loop(self):
        while self.running:
            packet = self.ipc.read()

            # STM handles USB midi messages, so this is the only command type we expect to receive
            if packet.cmd in [IPCPacket.Command.MIDI_DIN, IPCPacket.Command.MIDI_USB]:
                self.event_queue.put(packet.midi())
            else:
                print(f"Received unknown IPC packet: {packet.bytes().hex(' ')}")

    def _event_loop(self):
        while self.running:
            event = self.event_queue.get()
            print(event)

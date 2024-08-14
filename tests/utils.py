import numpy as np
import cv2
import time
from laserharp.midi import MidiEvent
from laserharp.events import EventEmitter


def wait_until(condition: callable, timeout: float):
    start_time = time.time()

    while not condition():
        if time.time() - start_time > timeout:
            return False

        time.sleep(0.01)

    return True


class MockSerial:
    def __init__(self):
        self.txdata = bytearray()
        self.rxdata = bytearray()

    def clear(self):
        self.txdata = bytearray()
        self.rxdata = bytearray()

    @property
    def in_waiting(self):
        return len(self.rxdata)

    def read(self, n):
        data = self.rxdata[:n]
        self.rxdata = self.rxdata[n:]
        return data

    def read_all(self):
        data = self.rxdata
        self.rxdata = bytearray()
        return data

    def write(self, data):
        self.txdata += data

    def flush(self):
        pass


class MockIPC(EventEmitter):
    def __init__(self, config: dict):
        super().__init__()

        self.config = config
        self.event = None

    def send(self, event: MidiEvent):
        self.event = event
        self.emit('send', event)

class MockCamera:
    def __init__(self, config: dict):
        self.config = config

        # setup a test frame
        w, h = self.resolution
        self.frame = np.zeros((h, w), dtype=np.uint8)

    @property
    def resolution(self):
        return self.config['resolution']

    @property
    def framerate(self):
        return self.config['framerate']

    def clear(self):
        self.frame = np.zeros_like(self.frame)

    def draw_blob(self, x: int, y: int, radius: int, intensity: int):
        self.frame = cv2.circle(self.frame, (int(x), int(y)), int(radius), int(intensity), -1)

    def save(self, filename: str):
        cv2.imwrite(str(filename), self.frame)

    def capture(self):
        # simulate capture delay
        time.sleep(1 / self.framerate)

        return self.frame

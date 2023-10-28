import numpy as np
import cv2
from ..midi import MidiEvent


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


class MockIPC():
    def __init__(self, config: dict):
        self.config = config
        self.event = None

    def send(self, event: MidiEvent):
        self.event = event

class MockCamera():
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
        self.frame = cv2.circle(self.frame, (x, y), radius, intensity, -1)

    def capture(self):
        return self.frame

    def frame_to_yuv(self, frame: np.ndarray):
        # convert frame to yuv format
        w, h = self.resolution
        uv = np.zeros((h // 2, w), dtype=np.uint8)
        yuv = np.vstack((frame, uv))

        # convert to byte stream
        return yuv.tobytes()

    # TODO: use this function in the actual camera class
    def yuv_to_frame(self, yuv: bytes):
        # convert to numpy array
        frame = np.frombuffer(yuv, dtype=np.uint8)

        # extract the luminance component
        w, h = self.resolution
        frame = frame.reshape((h * 3 // 2, w))
        frame = frame[:h, :w]

        return frame

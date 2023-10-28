import numpy as np
import cv2
from ..midi import MidiEvent


class DummyIPCController():
    def __init__(self, config: dict):
        self.config = config
        self.event = None

    def send(self, event: MidiEvent):
        self.event = event

class DummyCamera():
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

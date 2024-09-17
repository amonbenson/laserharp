import time
from typing import Optional
import numpy as np
import cv2
from src.laserharp.ipc import IPCController
from src.laserharp.camera import Camera


# pylint: disable=duplicate-code
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


# pylint: disable=duplicate-code
class MockIPCController(IPCController):
    def __init__(self, name: str, global_state: dict):
        super().__init__(name, global_state, MockSerial())

        self.txdata = bytearray()
        self.rxdata = bytearray()

    def clear(self):
        self.txdata = bytearray()
        self.rxdata = bytearray()

    def start(self):
        pass

    def stop(self):
        pass

    def send_raw(self, data: bytes, _timeout=None):
        if len(data) != 4:
            raise ValueError(f"IPC Data must be 4 bytes long, got {len(data)}")

        self.txdata += data

    def read_raw(self, _timeout=None) -> bytes:
        if len(self.rxdata) < 4:
            return None

        data = self.rxdata[:4]
        self.rxdata = self.rxdata[4:]
        return data


# pylint: disable=duplicate-code
class MockCamera(Camera):
    def __init__(self, name: str, global_state: dict):
        super().__init__(name, global_state)

        # setup a test frame
        w, h = self.resolution
        self.frame = np.zeros((h, w), dtype=np.uint8)

    def clear(self):
        self.frame = np.zeros_like(self.frame)

    def start(self):
        pass

    def stop(self):
        pass

    def draw_blob(self, x: int, y: int, radius: int, intensity: int):
        self.frame = cv2.circle(self.frame, (int(x), int(y)), int(radius), int(intensity), -1)

    def save(self, filename: str):
        cv2.imwrite(str(filename), self.frame)

    def capture(self):
        # simulate capture delay
        time.sleep(1 / self.framerate)

        return self.frame

    def start_debug_stream(self):
        raise NotImplementedError("Debug stream not implemented for MockCamera")

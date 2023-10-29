import multiprocessing
import picamera
import time
import numpy as np
from threading import Thread, Lock
from enum import Enum
from .events import EventEmitter


def _is_main_process():
    return multiprocessing.parent_process() is None


class Camera(EventEmitter):
    class StreamTarget(EventEmitter):
        def __init__(self, camera: 'Camera', frame_callback: callable):
            self.camera = camera
            self.frame_callback = frame_callback

            w, h = self.camera.resolution
            self.frame = np.zeros((h, w), dtype=np.uint8)
            self.frame_lock = Lock()

        def write(self, yuv_buffer):
            # convert the yuv buffer to a numpy array
            # convert to numpy array
            yuv = np.frombuffer(yuv_buffer, dtype=np.uint8)

            # extract the luminance component
            w, h = self.camera.resolution
            yuv = yuv.reshape((h * 3 // 2, w))
            frame = yuv[:h, :w]

            # call the frame handler
            self.frame_callback(frame)

            # store the frame
            with self.frame_lock:
                np.copyto(self.frame, frame)

        def get_frame(self):
            # copy the frame buffer
            with self.frame_lock:
                frame = self.frame.copy()

            return frame

    class State(Enum):
        STOPPED = 0
        STARTING = 1
        RUNNING = 2
        STOPPING = 3

    def __init__(self, config: dict):
        super().__init__()

        self.config = config

        # setup camera
        self.picam = picamera.PiCamera()
        self.picam.resolution = self.config['resolution']
        self.picam.framerate = self.config['framerate']
        self.picam.rotation = self.config['rotation']

        # set manual exposure and white balance
        self.picam.shutter_speed = self.config['shutter_speed']
        self.picam.iso = self.config['iso']
        self.picam.exposure_mode = 'off'
        self.picam.awb_mode = 'off'
        self.picam.awb_gains = (1.5, 1.5)

        # image settings
        self.picam.brightness = self.config['brightness']
        self.picam.contrast = self.config['contrast']
        self.picam.saturation = self.config['saturation']
        self.picam.sharpness = self.config['sharpness']
        self.picam.exposure_compensation = 0
        self.picam.meter_mode = 'average'

        self.stream_target = self.StreamTarget(self, self._on_frame)

        self.capture_process = None
        self.state = self.State.STOPPED

    @property
    def resolution(self):
        return self.config['resolution']

    @property
    def framerate(self):
        return self.config['framerate']

    def _on_frame(self, frame):
        self.emit('frame', frame)

    def start(self):
        if self.state != self.State.STOPPED:
            raise RuntimeError("Camera is already running.")

        if not _is_main_process():
            raise RuntimeError("Camera can only be started in the main process.")

        self.state = self.State.STARTING
        self.process = Thread(target=self._capture_loop)
        self.process.start()

    def stop(self):
        if self.state not in (self.State.STARTING, self.State.RUNNING):
            raise RuntimeError("Camera is not running.")

        self.state = self.State.STOPPING
        self.process.join(timeout=2)
        self.state = self.State.STOPPED

    def _capture_loop(self):
        self.picam.start_recording(self.stream_target, format='yuv')

        # if the camera was stopped immediately after starting, do not overwrite the state
        if self.state == self.State.STARTING:
            self.state = self.State.RUNNING

        # start capturing. For each frame, the stream target's write() method is called
        try:
            while self.state == self.State.RUNNING:
                self.picam.wait_recording(1)
        finally:
            self.picam.stop_recording()

    def capture(self, *kargs, **kwargs) -> np.ndarray:
        return self.stream_target.get_frame(*kargs, **kwargs)

    def close(self):
        self.picam.close()


if __name__ == '__main__':
    camera = Camera(config={
        'resolution': (640, 480),
        'framerate': 60,
        'rotation': 180,
        'shutter_speed': 5000,
        'iso': 10,
        'brightness': 50,
        'contrast': 0,
        'saturation': 0,
        'sharpness': 0
    })

    camera.start()
    camera.on('frame', lambda frame: print(f"got frame of shape {frame.shape}"))

    while not camera.running:
        time.sleep(0.1)
    time.sleep(1)

    camera.stop()

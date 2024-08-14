import logging
import multiprocessing
import libcamera
import picamera2
import time
import numpy as np
from threading import Thread, Lock
from enum import Enum
from .events import EventEmitter


def _is_main_process():
    return multiprocessing.parent_process() is None


class Camera(EventEmitter):
    class State(Enum):
        STOPPED = 0
        STARTING = 1
        RUNNING = 2
        STOPPING = 3

    def __init__(self, config: dict):
        super().__init__()

        self.config = config

        # store the current frame in a buffer
        w, h = self.config['resolution']
        self.frame = np.zeros((h, w), dtype=np.uint8)
        self.frame_lock = Lock()

        # convert the rotation to a libcamera transform
        rotation = self.config.get('rotation', 0)
        if rotation == 0:
            transform = libcamera.Transform(hflip=True, vflip=True)
        elif rotation == 180:
            transform = libcamera.Transform(hflip=True, vflip=True)
        else:
            raise ValueError(f"Invalid rotation: {rotation}. With libcamera2, only 0 and 180 degree rotations are supported.")

        # setup camera
        self.picam = picamera2.Picamera2()

        config = self.picam.create_preview_configuration(
            main={
                'size': tuple(self.config['resolution']),
                'format': 'YUV420',
            },
            transform=transform,
            controls={
                'FrameRate': self.config['framerate'],
            },
            buffer_count=1
        )
        self.picam.align_configuration(config)
        self.picam.configure(config)
        logging.debug(f"Final camera configuration: {self.picam.stream_configuration('raw')}")

        """
        self.picam.set_controls({
            'AeEnable': False,
            'AeFlickerMode': libcamera.controls.AeFlickerMode.Off,
            'AfMode': libcamera.controls.AfMode.Off,
            'AwbEnable': False
        })
        """

        """
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
        """

        self.capture_process = None
        self.state = self.State.STOPPED

    @property
    def resolution(self):
        return self.config['resolution']

    @property
    def framerate(self):
        return self.config['framerate']

    def start(self):
        if self.state != self.State.STOPPED:
            raise RuntimeError("Camera is already running.")

        if not _is_main_process():
            raise RuntimeError("Camera can only be started in the main process.")

        self.state = self.State.STARTING
        self.capture_thread = Thread(target=self._capture_loop)
        self.capture_thread.start()

    def stop(self):
        if self.state not in (self.State.STARTING, self.State.RUNNING):
            raise RuntimeError("Camera is not running.")

        self.state = self.State.STOPPING
        self.capture_thread.join(timeout=2)
        self.state = self.State.STOPPED

    def _capture_loop(self):
        # check if the camera is still in starting state
        if self.state == self.State.STARTING:
            self.state = self.State.RUNNING
        else:
            return

        self.picam.start(show_preview=False)

        # start capturing. For each frame, the stream target's write() method is called
        while self.state == self.State.RUNNING:
            try:
                # capture a frame
                yuv: np.ndarray = self.picam.capture_array('main')

                # extract the luminance component
                w, h = self.config['resolution']
                yuv = yuv.reshape((h * 3 // 2, w))
                frame = yuv[:h, :w]

                # call the frame handler
                self.emit('frame', frame)

                # store the frame
                with self.frame_lock:
                    np.copyto(self.frame, frame)
            except Exception as e:
                logging.error(f"Error capturing frame: {e}")
                logging.exception(e)

        self.picam.stop()
        self.picam.close()

    def capture(self, *kargs, **kwargs) -> np.ndarray:
        # return a copy of the frame buffer
        with self.frame_lock:
            return self.frame.copy()


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

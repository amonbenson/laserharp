import io
import logging
import multiprocessing
import time
import numpy as np
from threading import Thread, Lock
from enum import Enum
from .events import EventEmitter

try:
    import libcamera
    import picamera2
    picamera2_available = True
except ImportError:
    picamera2_available = False


def _is_main_process():
    return multiprocessing.parent_process() is None


class Camera(EventEmitter):
    class CameraOutput(io.BufferedIOBase):
        def __init__(self, camera: 'Camera', frame_callback: callable):
            self._camera = camera
            self._frame_callback = frame_callback
            
            w, h = self._camera.resolution
            self._frame = np.zeros((h, w), dtype=np.uint8)
            self._frame_lock = Lock()

        def write(self, yuv_buffer):
            # convert to numpy array
            yuv = np.frombuffer(yuv_buffer, dtype=np.uint8)

            # extract the luminance component
            w, h = self._camera.resolution
            yuv = yuv.reshape((h * 3 // 2, w))
            frame = yuv[:h, :w]

            # call the frame handler
            self._frame_callback(frame)

            # store the frame
            with self._frame_lock:
                np.copyto(self._frame, frame)

        def get_frame(self):
            # copy the frame buffer
            with self._frame_lock:
                return self._frame.copy()

    class State(Enum):
        STOPPED = 0
        STARTING = 1
        RUNNING = 2
        STOPPING = 3

    def __init__(self, config: dict):
        super().__init__()

        self.config = config
        self._output = self.CameraOutput(self, self._on_frame)

        if picamera2_available:
            self._init_camera()

    def _init_camera(self):
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

    def _on_frame(self, frame: np.ndarray):
        self.emit('frame', frame)

    def start(self):
        if not picamera2_available:
            raise RuntimeError("libcamera2 is not available. Please install it using 'apt-get install python3-picamera2'.")

        if self.state != self.State.STOPPED:
            raise RuntimeError("Camera is already running.")

        if not _is_main_process():
            raise RuntimeError("Camera can only be started in the main process.")

        self.state = self.State.STARTING
        self.capture_thread = Thread(target=self._capture_loop)
        self.capture_thread.start()

    def stop(self):
        if not picamera2_available:
            raise RuntimeError("libcamera2 is not available. Please install it using 'apt-get install python3-picamera2'.")

        if self.state not in (self.State.STARTING, self.State.RUNNING):
            raise RuntimeError("Camera is not running.")

        self.state = self.State.STOPPING
        self.capture_thread.join(timeout=2)
        self.state = self.State.STOPPED

    def _capture_loop(self):
        # start continuous capture
        self.picam.start_recording(picamera2.encoders.Encoder(), picamera2.outputs.FileOutput(self._output))
        time.sleep(2)

        # check if the camera is still in starting state
        if self.state == self.State.STARTING:
            self.state = self.State.RUNNING
        else:
            return

        # start capturing. For each frame, the output's write() method is called
        while self.state == self.State.RUNNING:
            time.sleep(1)

        self.picam.stop_recording()
        self.picam.close()

    def capture(self) -> np.ndarray:
        if not picamera2_available:
            raise RuntimeError("libcamera2 is not available. Please install it using 'apt-get install python3-picamera2'.")

        # return a copy of the frame buffer
        return self._output.get_frame()


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

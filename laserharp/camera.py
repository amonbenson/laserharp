import io
import logging
import time
import threading
from enum import Enum
import numpy as np

try:
    import libcamera
    import picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False

class Camera:
    class State(Enum):
        STOPPED = 0
        STARTING = 1
        RUNNING = 2
        STOPPING = 3

    class StreamingOutput(io.BufferedIOBase):
        def __init__(self):
            self.frame = None
            self.condition = threading.Condition()

        def write(self, buf):
            with self.condition:
                self.frame = buf
                self.condition.notify_all()

    def __init__(self, config: dict):
        self.config = config

        self.state = self.State.STOPPED
        self._frame = None

        if PICAMERA2_AVAILABLE:
            self._init_camera()

        picamera2.Picamera2.set_logging(logging.INFO)

    def _init_camera(self):
        # convert the rotation to a libcamera transform
        rotation = self.config.get('rotation', 0)
        if rotation == 0:
            transform = libcamera.Transform(hflip=True, vflip=True)
        elif rotation == 180:
            transform = libcamera.Transform(hflip=True, vflip=True)
        else:
            raise ValueError(f"Invalid rotation: {rotation}. With libcamera2, only 0 and 180 degree rotations are supported.")

        # set camera controls
        controls = {
            'FrameRate': self.config['framerate'],
            'ExposureTime': self.config['shutter_speed'],
            'AnalogueGain': self.config['iso'] / 100,
            'AeEnable': False,
            'AeFlickerMode': libcamera.controls.AeFlickerModeEnum.Off,
            # 'AfMode': 'Off',
            'AwbEnable': False,
        }

        # setup camera
        self.picam = picamera2.Picamera2()

        config = self.picam.create_preview_configuration(
            main={ # use for internal processing
                'size': tuple(self.config['resolution']),
                'format': 'YUV420',
            }, # use for the webserver
            lores={
                'size': (320, 240),
                'format': 'RGB888',
            },
            transform=transform,
            controls=controls,
            buffer_count=1
        )
        self.picam.align_configuration(config)
        self.picam.configure(config)

        # for some reason, the framerate needs to be set again. While we're at it, let's set all controls again
        self.picam.set_controls(controls)

        logging.debug(f"Camera configuration: {self.picam.stream_configuration('main')}")

        self.state = self.State.STOPPED

    @property
    def resolution(self):
        return self.config['resolution']

    @property
    def framerate(self):
        return self.config['framerate']

    def start(self):
        if not PICAMERA2_AVAILABLE:
            raise RuntimeError("libcamera2 is not available. Please install it using 'apt-get install python3-picamera2'.")

        if self.state != self.State.STOPPED:
            raise RuntimeError("Camera is already running.")

        self.state = self.State.STARTING

        # start continuous capture
        self.picam.start()
        time.sleep(2)

        self.state = self.State.RUNNING

    def stop(self):
        if not PICAMERA2_AVAILABLE:
            raise RuntimeError("libcamera2 is not available. Please install it using 'apt-get install python3-picamera2'.")

        if self.state not in (self.State.STARTING, self.State.RUNNING):
            raise RuntimeError("Camera is not running.")

        self.state = self.State.STOPPING
        self.picam.stop_recording()
        self.picam.stop()
        self.picam.close()
        self.state = self.State.STOPPED

    def capture(self) -> np.ndarray:
        if not PICAMERA2_AVAILABLE:
            raise RuntimeError("libcamera2 is not available. Please install it using 'apt-get install python3-picamera2'.")
        if self.state != self.State.RUNNING:
            raise RuntimeError("Camera is not running.")

        w, h = self.config['resolution']

        # capture a single frame
        yuv = self.picam.capture_array("main")
        assert yuv.dtype == np.uint8
        assert yuv.shape[0] == h * 3 // 2
        assert yuv.shape[1] == w

        # extract the luminance component
        yuv = yuv.reshape((h * 3 // 2, w))
        self._frame = yuv[:h, :w]

        # call the frame handler
        return self._frame

    def start_debug_stream(self) -> "Camera.StreamingOutput":
        if not PICAMERA2_AVAILABLE:
            raise RuntimeError("libcamera2 is not available. Please install it using 'apt-get install python3-picamera2'.")
        if self.state != self.State.RUNNING:
            raise RuntimeError("Camera is not running.")

        output = self.StreamingOutput()
        self.picam.start_recording(
            picamera2.encoders.JpegEncoder(),
            picamera2.outputs.FileOutput(output),
            name="lores",
            quality=picamera2.encoders.Quality.VERY_HIGH
        )

        return output

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

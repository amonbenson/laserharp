import io
import logging
import time
import numpy as np
from enum import Enum

try:
    import libcamera
    import picamera2
    picamera2_available = True
except ImportError:
    picamera2_available = False

class Camera:
    class State(Enum):
        STOPPED = 0
        STARTING = 1
        RUNNING = 2
        STOPPING = 3

    def __init__(self, config: dict):
        self.config = config

        if picamera2_available:
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
            main={
                'size': tuple(self.config['resolution']),
                'format': 'YUV420',
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
        print(self.picam.stream_configuration('main'), self.picam.controls)

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
        if not picamera2_available:
            raise RuntimeError("libcamera2 is not available. Please install it using 'apt-get install python3-picamera2'.")

        if self.state != self.State.STOPPED:
            raise RuntimeError("Camera is already running.")

        self.state = self.State.STARTING

        # start continuous capture
        self.picam.start()
        time.sleep(2)

        self.state = self.State.RUNNING

    def stop(self):
        if not picamera2_available:
            raise RuntimeError("libcamera2 is not available. Please install it using 'apt-get install python3-picamera2'.")

        if self.state not in (self.State.STARTING, self.State.RUNNING):
            raise RuntimeError("Camera is not running.")

        self.state = self.State.STOPPING
        self.picam.stop_recording()
        self.picam.stop()
        self.picam.close()
        self.state = self.State.STOPPED

    def capture(self) -> np.ndarray:
        if not picamera2_available:
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

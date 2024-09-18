import io
import logging
import time
import threading
from enum import Enum
import numpy as np
from perci import ReactiveDictNode
from .component import Component
from .events import EventEmitter

try:
    import libcamera
    import picamera2

    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False


class FrameRateCounter(EventEmitter):
    def __init__(self, update_interval: float = 1.0):
        super().__init__()

        self._update_interval = update_interval

        self._last_time = time.time()
        self._frame_count = 0
        self._frame_rate = 0

        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._update, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._thread.join()
        self._thread = None

    def get_frame_rate(self):
        return self._frame_rate

    def count_frame(self):
        self._frame_count += 1

    def _update(self):
        self._last_time = time.time()

        while self._running:
            # wait for one update interval
            time.sleep(self._update_interval)

            # calculate delta time
            t_now = time.time()
            dt = t_now - self._last_time
            self._last_time = t_now

            # calculate the frame rate and reset the frame counter
            self._frame_rate = self._frame_count / dt
            self._frame_count = 0

            # emit an event
            self.emit("update", self._frame_rate)


class Camera(Component):
    class StreamingOutput(io.BufferedIOBase):
        def __init__(self):
            self.frame = None
            self.condition = threading.Condition()

        def write(self, buf):
            with self.condition:
                self.frame = buf
                self.condition.notify_all()

    def __init__(self, name: str, global_state: ReactiveDictNode):
        super().__init__(name, global_state)

        self.state["status"] = "stopped"
        self.state["frame_rate"] = 0

        self._frame_counter = FrameRateCounter(update_interval=1.0)
        self._frame_counter.on("update", self._on_frame_counter_update)

        self._frame = None

        if self.enabled and PICAMERA2_AVAILABLE:
            self._init_camera()

            picamera2.Picamera2.set_logging(logging.INFO)

    def _on_frame_counter_update(self, rate):
        # store the new frame rate in the state
        self.state["frame_rate"] = rate

    def _init_camera(self):
        # convert the rotation to a libcamera transform
        rotation = self.config.get("rotation", 0)
        if rotation == 0:
            transform = libcamera.Transform(hflip=True, vflip=True)
        elif rotation == 180:
            transform = libcamera.Transform(hflip=True, vflip=True)
        else:
            raise ValueError(f"Invalid rotation: {rotation}. With libcamera2, only 0 and 180 degree rotations are supported.")

        # set camera controls
        controls = {
            "FrameRate": self.config["framerate"],
            "ExposureTime": self.config["shutter_speed"],
            "AnalogueGain": self.config["iso"] / 100,
            "AeEnable": False,
            "AeFlickerMode": libcamera.controls.AeFlickerModeEnum.Off,
            # 'AfMode': 'Off',
            "AwbEnable": False,
        }

        # setup camera
        self._picam = picamera2.Picamera2()

        config = self._picam.create_preview_configuration(
            main={  # use for internal processing
                "size": tuple(self.config["resolution"]),
                "format": "YUV420",
            },  # use for the webserver
            lores={
                "size": (320, 240),
                "format": "RGB888",
            },
            transform=transform,
            controls=controls,
            buffer_count=1,
        )
        self._picam.align_configuration(config)
        self._picam.configure(config)

        # for some reason, the framerate needs to be set again. While we're at it, let's set all controls again
        self._picam.set_controls(controls)

        logging.debug(f"Camera configuration: {self._picam.stream_configuration('main')}")

        self.state["status"] = "stopped"

    @property
    def resolution(self):
        return self.config["resolution"]

    @property
    def framerate(self):
        return self.config["framerate"]

    def start(self):
        if self.state["status"] != "stopped":
            raise RuntimeError("Camera is already running.")

        if self.enabled:
            if not PICAMERA2_AVAILABLE:
                raise RuntimeError("libcamera2 is not available. Please install it using 'apt-get install python3-picamera2'.")

            self.state["status"] = "starting"

            # start continuous capture
            self._picam.start()
            time.sleep(2)
        else:
            logging.info("Camera interface is disabled")

        self._frame_counter.start()

        self.state["status"] = "running"

    def stop(self):
        if self.state["status"] not in ("starting", "running"):
            raise RuntimeError("Camera is not running.")

        if self.enabled:
            if not PICAMERA2_AVAILABLE:
                raise RuntimeError("libcamera2 is not available. Please install it using 'apt-get install python3-picamera2'.")

            self.state["status"] = "stopping"

            # stop continuous capture
            self._picam.stop_recording()
            self._picam.stop()
            self._picam.close()

        self._frame_counter.stop()

        self.state["status"] = "stopped"

    def capture(self) -> np.ndarray:
        if self.enabled:
            if not PICAMERA2_AVAILABLE:
                raise RuntimeError("libcamera2 is not available. Please install it using 'apt-get install python3-picamera2'.")
            if self.state["status"] != "running":
                raise RuntimeError("Camera is not running.")

            w, h = self.config["resolution"]

            # capture a single frame
            yuv: np.ndarray = self._picam.capture_array("main")
            assert yuv.dtype == np.uint8
            assert yuv.shape[0] == h * 3 // 2
            assert yuv.shape[1] == w

            # extract the luminance component
            yuv = yuv.reshape((h * 3 // 2, w))
            self._frame = yuv[:h, :w]

        else:
            # generate a "fake" empty frame
            time.sleep(1 / self.config["framerate"])
            self._frame = np.zeros((self.config["resolution"][1], self.config["resolution"][0]), dtype=np.uint8)

        # count the frame to calculate the frame rate
        self._frame_counter.count_frame()

        return self._frame

    def start_debug_stream(self) -> "Camera.StreamingOutput":
        if not self.enabled:
            # return an empty output
            return self.StreamingOutput()

        if not PICAMERA2_AVAILABLE:
            raise RuntimeError("libcamera2 is not available. Please install it using 'apt-get install python3-picamera2'.")
        if self.state["status"] != "running":
            raise RuntimeError("Camera is not running.")

        output = self.StreamingOutput()
        self._picam.start_recording(
            picamera2.encoders.JpegEncoder(),
            picamera2.outputs.FileOutput(output),
            name="lores",
            quality=picamera2.encoders.Quality.VERY_HIGH,
        )

        return output

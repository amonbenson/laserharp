import io
import logging
import time
import threading
import traceback
from enum import Enum
import numpy as np
import cv2
from perci import ReactiveDictNode, watch
from .component import Component
from .events import EventEmitter

try:
    import libcamera
    import picamera2

    PICAMERA2_AVAILABLE = True
except ImportError:
    traceback.print_exc()
    # on error "ImportError: /lib/aarch64-linux-gnu/libepoxy.so.0: undefined symbol: epoxy_\udce7lGetCom\udce2inerSta\udce7eParameterfvNV"
    # --> pip3 install pyav
    PICAMERA2_AVAILABLE = False


class FrameRateCounter(EventEmitter):
    def __init__(self, update_interval: float = 1.0):
        super().__init__()

        self._update_interval = update_interval

        self._last_time = time.time()
        self._last_count = 0
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

    def get_frame_count(self):
        return self._frame_count

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
            fc = self._frame_count
            self._frame_rate = (fc - self._last_count) / dt
            self._last_count = fc

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

    def __init__(self, name: str, global_state: ReactiveDictNode, skip_hardware_init: bool = False):
        super().__init__(name, global_state)

        self.state["status"] = "stopped"
        self.state["framerate"] = 0

        self._frame_counter = FrameRateCounter(update_interval=1.0)
        self._frame_counter.on("update", self._on_frame_counter_update)

        self._frame = None
        self._frame_available = threading.Condition()
        self._rgb_mode = False

        # create a blob detector
        params = cv2.SimpleBlobDetector_Params()
        params.filterByArea = True
        params.minArea = 10
        params.maxArea = 100

        params.filterByCircularity = True
        params.minCircularity = 0.85

        params.filterByConvexity = False
        params.filterByInertia = False
        params.filterByColor = False  # Not based on pixel value

        self._blob_detector = cv2.SimpleBlobDetector_create(params)

        if PICAMERA2_AVAILABLE and self.enabled and not skip_hardware_init:
            self._init_camera()

            picamera2.Picamera2.set_logging(logging.INFO)

        # update camera controls when settings change
        watch(self.settings.get_child("shutter_speed"), lambda _: self._update_camera_controls())
        watch(self.settings.get_child("iso"), lambda _: self._update_camera_controls())

    def _on_frame_counter_update(self, rate):
        # store the new frame rate in the state
        self.state["framerate"] = rate

    def _update_camera_controls(self):
        logging.debug("Updating camera settings...")

        if PICAMERA2_AVAILABLE and self.enabled:
            # update the camera controls
            controls = {
                "FrameRate": self.config["framerate"],
                "ExposureTime": self.settings["shutter_speed"],
                "AnalogueGain": self.settings["iso"] / 100,
                # "AeEnable": False,
                "AeFlickerMode": libcamera.controls.AeFlickerModeEnum.Off,
                # 'AfMode': 'Off',
                "AwbEnable": False,
            }
            self._picam.set_controls(controls)

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
            "ExposureTime": self.settings["shutter_speed"],
            "AnalogueGain": self.settings["iso"] / 100,
            # "AeEnable": False,
            "AeFlickerMode": libcamera.controls.AeFlickerModeEnum.Off,
            # 'AfMode': 'Off',
            "AwbEnable": False,
        }

        # setup camera
        self._picam = picamera2.Picamera2()

        config = self._picam.create_preview_configuration(
            main={
                "size": tuple(self.config["resolution"]),
                "format": "RGB888" if self._rgb_mode else "YUV420",
            },
            transform=transform,
            controls=controls,
            buffer_count=1,
        )
        self._picam.align_configuration(config)

        try:
            self._picam.configure(config)
        except RuntimeError as e:
            if "lores stream must be YUV" in str(e):
                # try again with a YUV lores stream
                config["lores"]["format"] = "YUV420"
                self._picam.align_configuration(config)
                self._picam.configure(config)
            else:
                raise e

        # for some reason, the framerate needs to be set again. While we're at it, let's set all controls again
        self._picam.set_controls(controls)

        logging.debug(f"Main configuration: {self._picam.stream_configuration('main')}")

        self.state["status"] = "stopped"

    @property
    def resolution(self):
        return self.config["resolution"]

    @property
    def framerate(self):
        return self.config["framerate"]

    @property
    def actual_framerate(self):
        return self._frame_counter.get_frame_rate()

    @property
    def frame_count(self):
        return self._frame_counter.get_frame_count()

    def start(self):
        if self.state["status"] != "stopped":
            raise RuntimeError("Camera is already running.")

        if self.enabled:
            if not PICAMERA2_AVAILABLE:
                raise RuntimeError("libcamera2 is not available or failed to import. Please install it using 'apt-get install python3-picamera2' (see errors above).")

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
                raise RuntimeError("libcamera2 is not available or failed to import. Please install it using 'apt-get install python3-picamera2' (see errors above).")

            self.state["status"] = "stopping"

            # stop continuous capture
            self._picam.stop_recording()
            self._picam.stop()
            self._picam.close()

        self._frame_counter.stop()

        self.state["status"] = "stopped"

    @staticmethod
    def _preprocess_frame(frame: np.ndarray) -> np.ndarray:
        # Convert to HSV for easier color segmentation
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 1. Threshold for white pixels
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 40, 255])
        white_mask = cv2.inRange(hsv, lower_white, upper_white)

        # 2. Threshold for red pixels (including both hue ends)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])

        red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)

        # 3. Dilate red to simulate red "glow" zone
        red_glow_zone = cv2.GaussianBlur(red_mask, (21, 21), 0)

        # 4. Keep white pixels surrounded by red glow
        white_in_red_glow = cv2.bitwise_and(white_mask, red_glow_zone)

        # 5. Combine white-with-red-glow + pure red blobs
        final_blob_mask = cv2.bitwise_or(white_in_red_glow, red_mask)

        # Optional: clean up noise
        final_blob_mask = cv2.morphologyEx(final_blob_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        final_blob_mask = cv2.GaussianBlur(final_blob_mask, (15, 15), 0)

        return final_blob_mask

    def capture(self) -> np.ndarray:
        if self.enabled:
            if not PICAMERA2_AVAILABLE:
                raise RuntimeError("libcamera2 is not available. Please install it using 'apt-get install python3-picamera2'.")
            if self.state["status"] != "running":
                raise RuntimeError("Camera is not running.")

            w, h = self.config["resolution"]
            frame_raw: np.ndarray = None

            if self._rgb_mode:
                # capture a single frame in RGB format
                rgb: np.ndarray = self._picam.capture_array("main")
                assert rgb.dtype == np.uint8
                assert rgb.shape[0] == h
                assert rgb.shape[1] == w
                assert rgb.shape[2] == 3

                # convert RGB to grayscale
                frame_raw = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            else:
                # capture a single frame in YUV format
                yuv: np.ndarray = self._picam.capture_array("main")
                assert yuv.dtype == np.uint8
                assert yuv.shape[0] == h * 3 // 2
                assert yuv.shape[1] == w

                # extract the luminance component
                yuv = yuv.reshape((h * 3 // 2, w))
                frame_raw = yuv[:h, :w]

            # find point-like blobs
            points = cv2.filter2D(frame_raw, -1, np.array([
                [0, -1, 0],
                [-1, 4, -1],
                [0, -1, 0]
            ], dtype=np.float32))
            points = cv2.GaussianBlur(points, (25, 25), 0)
            points = cv2.morphologyEx(points, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
            points = cv2.multiply(points, 10)

            self._frame = points

        else:
            # generate a "fake" empty frame
            time.sleep(1 / self.config["framerate"])
            self._frame = np.zeros((self.config["resolution"][1], self.config["resolution"][0]), dtype=np.uint8)

        # count the frame to calculate the frame rate
        self._frame_counter.count_frame()

        # notify all waiting threads that a new frame is available
        with self._frame_available:
            self._frame_available.notify_all()

        return self._frame

    def wait_for_frame(self, timeout: float = 1.0) -> np.ndarray:
        if not self.enabled:
            raise RuntimeError("Camera is not enabled.")

        if not PICAMERA2_AVAILABLE:
            raise RuntimeError("libcamera2 is not available or failed to import. Please install it using 'apt-get install python3-picamera2' (see errors above).")
        if self.state["status"] != "running":
            raise RuntimeError("Camera is not running.")

        # wait for a new frame to be available
        with self._frame_available:
            if not self._frame_available.wait(timeout):
                raise TimeoutError("No new frame available within the timeout period.")

        return self._frame

    def wait_for_frame_or_black(self, timeout: float = 1.0) -> np.ndarray:
        try:
            return self.wait_for_frame(timeout)
        except Exception as e:
            logging.warning(f"Error while waiting for a new frame: {e}")
            time.sleep(1)

            # return an empty frame
            return np.zeros((self.config["resolution"][1], self.config["resolution"][0]), dtype=np.uint8)

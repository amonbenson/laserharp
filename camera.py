import time
import threading
import multiprocessing
import picamera
import numpy as np
import cv2
from dataclasses import dataclass
from .config import CONFIG


@dataclass
class InterceptionEvent:
    beamlength: np.ndarray

class Camera:
    class ImageProcessor:
        def __init__(self, resolution: tuple, N_beams: int):
            self.resolution = resolution
            self.N_beams = N_beams

            self.beam_start = np.zeros((N_beams, 2), dtype=np.int32)
            self.beam_end = np.zeros((N_beams, 2), dtype=np.int32)

            self.beamlength_shared = multiprocessing.Array('f', N_beams)
            self.beamlength_event = multiprocessing.Event()

            # TODO: use a shared memory array instead of a lock
            self.frame = None
            self.frame_lock = multiprocessing.Lock()
            self.frame_event = multiprocessing.Event()

            # initial calibration
            self.calibrated = False
            self.ya = 0.0
            self.yb = 0.0
            self.x0 = np.zeros(N_beams, dtype=np.float32)
            self.m = np.zeros(N_beams, dtype=np.float32)

        def set_calibration(self, ya, yb, x0, m):
            # store the new calibration data
            self.ya = float(ya)
            self.yb = float(yb)
            np.copyto(self.x0, x0)
            np.copyto(self.m, m)

            # setup the points of interest
            y_lower = np.maximum(ya, 0)
            y_upper = np.minimum(yb, self.resolution[1] - 1)

            y = np.arange(y_lower, y_upper + 1)
            y_angle = (y - ya) / (yb - ya) * np.pi / 2 # map to range [0, pi/2]
            y_angle = np.clip(y_angle, 0, np.pi / 2 - 0.01) # clip to avoid infinite and negative values
            y_tan = np.tan(y_angle) # calculate the tangent of the angle
            self.y_metric = y_tan * CONFIG['camera']['mount_distance'] # covert to metric units

            # store each grid coordinate we need to check
            self.beam_yv = np.round(y[:, np.newaxis]).astype(np.int32)
            self.beam_xv = np.round(self.x0[np.newaxis, :] + self.m[np.newaxis, :] * y[:, np.newaxis]).astype(np.int32)

            self.beam_threshold = 255 * CONFIG['image_processor']['threshold']
            self.beamlength_min = CONFIG['image_processor']['beam_length_min']
            self.beamlength_max = CONFIG['image_processor']['beam_length_max']

            self.calibrated = True

        def write(self, buf):
            w, h = self.resolution

            # get a grayscale frame
            with self.frame_lock:
                # convert the YUV stream to a numpy array and extract the Y component
                self.frame = np.frombuffer(buf, dtype=np.uint8).reshape((h * 3 // 2, w))
                self.frame = self.frame[:h, :w]

                self.frame_event.set()

            # skip if not calibrated
            if not self.calibrated:
                return

            # blur the frame
            ksize = CONFIG['image_processor']['preblur']
            blurred = cv2.GaussianBlur(self.frame, (ksize, ksize), 0)

            # get the brightness for each point of interest
            brightness = blurred[self.beam_yv, self.beam_xv]

            # calculate the beamlengths (length is NaN if the beam is not intercepted)
            beam_strength = np.max(brightness, axis=0)
            beam_position = np.argmax(brightness, axis=0)

            # replace weak values by NaN
            beamlength = np.where(beam_strength > self.beam_threshold, self.y_metric[beam_position], np.nan)

            # replace out of bounds values by NaN
            beamlength = np.where(beamlength < self.beamlength_min, np.nan, beamlength)
            beamlength = np.where(beamlength > self.beamlength_max, np.nan, beamlength)

            # store the beamlengths
            with self.beamlength_shared.get_lock():
                np.copyto(np.frombuffer(self.beamlength_shared.get_obj(), dtype=np.float32), beamlength)

            self.beamlength_event.set()

        def flush(self):
            # clear the frame event
            self.frame_event.clear()

        def read(self, timeout=None):
            # wait for an interception event
            was_set = self.beamlength_event.wait(timeout=timeout)
            if not was_set:
                return None

            self.beamlength_event.clear()

            # return a copy of the current beamlengths
            with self.beamlength_shared.get_lock():
                beamlength = np.frombuffer(self.beamlength_shared.get_obj(), dtype=np.float32)
            return InterceptionEvent(beamlength)

        def get_frame(self, *, draw_calibration: bool = False, grayscale: bool = False):
            # wait for a frame to be available
            self.frame_event.wait()

            # return a copy of the current frame
            with self.frame_lock:
                frame = self.frame.copy()

            # convert grayscale to bgr
            if not grayscale:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

            # draw a line for each beam span
            if draw_calibration:
                for i in range(self.N_beams):
                    cv2.line(frame,
                        tuple(self.beam_start[i]),
                        tuple(self.beam_end[i]),
                        255 if grayscale else (0, 0, 255),
                        1)

            return frame

    def __init__(self):
        # setup camera
        self.camera = picamera.PiCamera()
        self.camera.resolution = CONFIG['camera']['resolution']
        self.camera.framerate = CONFIG['camera']['framerate']
        self.camera.rotation = CONFIG['camera']['rotation']

        # set manual exposure and white balance
        self.camera.shutter_speed = CONFIG['camera']['shutter_speed']
        self.camera.iso = CONFIG['camera']['iso']
        self.camera.exposure_mode = 'off'
        self.camera.awb_mode = 'off'
        self.camera.awb_gains = (1.5, 1.5)

        # image settings
        self.camera.brightness = CONFIG['camera']['brightness']
        self.camera.contrast = CONFIG['camera']['contrast']
        self.camera.saturation = CONFIG['camera']['saturation']
        self.camera.sharpness = CONFIG['camera']['sharpness']
        self.camera.exposure_compensation = 0
        self.camera.meter_mode = 'average'

        self.thread = None
        self.running = False

        self.image_processor = self.ImageProcessor(
            resolution=self.camera.resolution,
            N_beams=CONFIG['num_lasers'])

    @property
    def width(self):
        return self.camera.resolution[0]

    @property
    def height(self):
        return self.camera.resolution[1]

    def start(self):
        if self.running: return

        self.thread = threading.Thread(target=self._capture_loop)
        self.thread.start()
        self.running = True

    def stop(self):
        if not self.running: return

        self.running = False
        self.thread.join()

    def _capture_loop(self):
        self.camera.start_recording(self.image_processor, format='yuv')

        # start capturing. For each frame, the image processor's write() method is called
        try:
            while self.running:
                self.camera.wait_recording(1)
        finally:
            self.camera.stop_recording()

    def read(self, timeout=None):
        return self.image_processor.read(timeout=timeout)

    def capture(self, *kargs, **kwargs) -> np.ndarray:
        return self.image_processor.get_frame(*kargs, **kwargs)

    def set_calibration(self, **kwargs):
        self.image_processor.set_calibration(**kwargs)

    def close(self):
        self.camera.close()

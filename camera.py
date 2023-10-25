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
    beam_length: np.ndarray
    beam_vibrato: np.ndarray

class Camera:
    class ImageProcessor:
        FILTER_SIZE = 11

        def __init__(self, resolution: tuple, N_beams: int):
            self.resolution = resolution
            self.N_beams = N_beams

            self.beam_start = np.zeros((N_beams, 2), dtype=np.int32)
            self.beam_end = np.zeros((N_beams, 2), dtype=np.int32)

            # TODO: make coefficients configurable (see https://fiiir.com/)
            self.filter_taps = np.zeros((self.FILTER_SIZE, N_beams), dtype=np.float32)
            self.filter_coeff = np.array([
                -0.033953150079712217,
                0.009049772158682429,
                0.074180583436830330,
                0.144126409950432216,
                0.197712774636478017,
                0.217767219794578387,
                0.197712774636478017,
                0.144126409950432216,
                0.074180583436830330,
                0.009049772158682429,
                -0.033953150079712217
            ])

            self.nan_state = np.zeros(N_beams, dtype=bool)
            self.beam_length_shared = multiprocessing.Array('f', N_beams)
            self.beam_vibrato_shared = multiprocessing.Array('f', N_beams)
            self.beam_length_event = multiprocessing.Event()

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
            self.beam_length_min = CONFIG['image_processor']['beam_length_min']
            self.beam_length_max = CONFIG['image_processor']['beam_length_max']

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

            # lookup the beamlength and replace weak values by NaN
            beam_length_raw = self.y_metric[beam_position]
            beam_length_raw[beam_strength < self.beam_threshold] = np.nan

            # replace out of bounds values by NaN
            beam_length_raw[beam_length_raw < self.beam_length_min] = np.nan
            beam_length_raw[beam_length_raw > self.beam_length_max] = np.nan

            nan_state_new = np.isfinite(beam_length_raw)

            # low-pass filter the beamlengths over time
            # TODO: think about how to handle NaNs here:
            # NaNs should not propagate into the filter and the first value afterwards should be
            # set to all taps effectively "resetting" the filter.

            # shift the filter taps
            self.filter_taps[1:] = self.filter_taps[:-1]
            self.filter_taps[0] = beam_length_raw

            # set all taps to NaN if the beam was not intercepted
            self.filter_taps[:, ~nan_state_new] = np.nan

            # set all taps to the same value if the beam was just intercepted
            nan_state_rising = nan_state_new & ~self.nan_state
            self.filter_taps[:, nan_state_rising] = beam_length_raw[nan_state_rising]

            # split the beam length into low-frequency (beam_length) and high-frequency (beam_vibrato) components
            beam_length = np.nansum(self.filter_taps * self.filter_coeff[:, np.newaxis], axis=0)
            beam_length[np.isnan(beam_length_raw)] = np.nan # keep NaNs

            beam_vibrato = beam_length_raw - beam_length
            beam_vibrato = np.tanh(beam_vibrato * CONFIG['image_processor']['vibrato_gain'])
            #beam_vibrato[np.isnan(beam_length_raw)] = 0 # replace NaNs by 0

            self.nan_state = nan_state_new

            # store the beam lengths
            with self.beam_length_shared.get_lock():
                np.copyto(np.frombuffer(self.beam_length_shared.get_obj(), dtype=np.float32), beam_length)
                np.copyto(np.frombuffer(self.beam_vibrato_shared.get_obj(), dtype=np.float32), beam_vibrato)

            self.beam_length_event.set()

        def flush(self):
            # clear the frame event
            self.frame_event.clear()

        def read(self, timeout=None):
            # wait for an interception event
            was_set = self.beam_length_event.wait(timeout=timeout)
            if not was_set:
                return None

            self.beam_length_event.clear()

            # return a copy of the current beamlengths
            with self.beam_length_shared.get_lock():
                beam_length = np.frombuffer(self.beam_length_shared.get_obj(), dtype=np.float32)
                beam_vibrato = np.frombuffer(self.beam_vibrato_shared.get_obj(), dtype=np.float32)
            return InterceptionEvent(beam_length, beam_vibrato)

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

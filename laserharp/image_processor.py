from dataclasses import dataclass
import numpy as np
import cv2
from .image_calibrator import Calibration
from .laser_array import LaserArray
from .camera import Camera
from .events import Ref


class ImageProcessor():
    @dataclass
    class Result:
        active: np.ndarray
        length: np.ndarray
        modulation: np.ndarray

        def to_dict(self, replace_nan=False):
            return {
                'active': np.nan_to_num(self.active).tolist(),
                'length': np.nan_to_num(self.length).tolist() if replace_nan else self.length.tolist(),
                'modulation': np.nan_to_num(self.modulation).tolist()
            }

    def __init__(self, laser_array: LaserArray, camera: Camera, config: dict):
        self.config = config
        self.state = Ref({
            "result": None
        })

        self.laser_array = laser_array
        self.camera = camera

        self.calibration = None

        self.filter_coeff = self._calculate_coeff()
        self.filter_taps = np.zeros((len(self.filter_coeff), len(self.laser_array)), dtype=np.float32)

        self.beam_active = np.zeros(len(self.laser_array), dtype=bool)

        # values initialized by set_calibration()
        self.y_metric = None
        self.beam_yv = None
        self.beam_xv = None


    def _calculate_coeff(self) -> np.ndarray:
        # compute number of taps
        f_sampling = self.camera.framerate
        f_cutoff = self.config['filter_cutoff']
        n = self.config['filter_size']

        # compute sinc filter
        h = np.sinc(2 * f_cutoff / f_sampling * (np.arange(n) - (n - 1) / 2))

        # apply window
        h *= np.blackman(n)

        # normalize
        h /= np.sum(h)

        return h

    def set_calibration(self, calibration: Calibration):
        self.calibration = calibration

        # get all possible y coordinates
        height = self.camera.resolution[1]
        y_lower = np.maximum(0, calibration.ya)
        y_upper = np.minimum(height, calibration.yb)
        y = np.arange(y_lower, y_upper)

        # map each y coordinate to an angle and its corresponding metric height
        y_angle = (y - calibration.ya) / (calibration.yb - calibration.ya) * np.pi / 2
        y_angle = np.clip(y_angle, 0, np.pi / 2 - 0.01)
        y_tan = np.tan(y_angle)
        self.y_metric = y_tan * self.camera.config['mount_distance']

        # calculate the grid of beam interception points
        self.beam_yv = np.round(y[:, np.newaxis]).astype(np.int32)
        self.beam_xv = np.round(calibration.x0[np.newaxis, :] + calibration.m[np.newaxis, :] * y[:, np.newaxis]).astype(np.int32)

    @property
    def is_calibrated(self):
        return self.calibration is not None

    def _calculate_beam_length(self, frame: np.ndarray) -> np.ndarray:
        if not self.is_calibrated:
            raise RuntimeError('No calibration data available')

        # blur the frame
        ksize = self.config['preblur']
        frame = cv2.GaussianBlur(frame, (ksize, ksize), 0)

        # get the brightness for each beam
        brightness = frame[self.beam_yv, self.beam_xv]

        # find the strongest interception point for each beam
        strength = np.max(brightness, axis=0)
        position = np.argmax(brightness, axis=0)

        # lookup the metric length of each beam
        length = self.y_metric[position]

        # filter out invalid interception points
        length[strength < self.config['threshold']] = np.nan
        length[length < self.config['length_min']] = np.nan
        length[length > self.config['length_max']] = np.nan

        return length

    def _apply_filter(self, raw_length: np.ndarray):
        # store if any beam just became active
        active = np.isfinite(raw_length)
        rising = active & ~self.beam_active
        self.beam_active = active

        # apply a low pass filter to the beam length
        self.filter_taps[1:] = self.filter_taps[:-1]
        self.filter_taps[0] = raw_length

        # clear all taps for inactive beams
        self.filter_taps[:, ~active] = np.nan

        # set all taps for beams that just became active
        self.filter_taps[:, rising] = raw_length[rising]

        # store the low frequency content as the actual length
        length = np.nansum(self.filter_taps * self.filter_coeff[:, np.newaxis], axis=0)
        length[~active] = np.nan # keep NaNs

        # store the high frequency content as the modulation
        modulation = raw_length - length
        modulation = np.tanh(modulation * self.config['modulation_gain'])
        modulation[~active] = 0 # inactive beams have no modulation

        return self.Result(active, length, modulation)

    def process(self, frame) -> Result:
        # process the frame
        raw_length = self._calculate_beam_length(frame)
        result = self._apply_filter(raw_length)

        # perform state update
        self.state.update({
            "result": result.to_dict(replace_nan=True)
        })

        return result

from dataclasses import dataclass
import numpy as np
import cv2
from .image_calibrator import Calibration


class ImageProcessor():
    @dataclass
    class Result:
        active: np.ndarray
        length: np.ndarray
        modulation: np.ndarray

    def __init__(self, **config: dict):
        self.config = config
        self.calibration = None

        self.filter_coeff = self._calculate_coeff()
        self.filter_taps = np.zeros((len(self.filter_coeff), config['num_lasers']), dtype=np.float32)

        self.beam_active = np.zeros(config['num_lasers'], dtype=bool)

    def _calculate_coeff(self) -> np.ndarray:
        # compute number of taps
        f_S = self.config['camera_framerate']
        f_L = self.config['filter_cutoff']
        N = self.config['filter_size']

        # compute sinc filter
        h = np.sinc(2 * f_L / f_S * (np.arange(N) - (N - 1) / 2))

        # apply window
        h *= np.blackman(N)

        # normalize
        h /= np.sum(h)

        return h

    def set_calibration(self, calibration: Calibration):
        self.calibration = calibration

        # get all possible y coordinates
        w, h = self.config['camera_resolution']
        y_lower = np.maximum(0, calibration.ya)
        y_upper = np.minimum(h, calibration.yb)
        y = np.arange(y_lower, y_upper)

        # map each y coordinate to an angle and its corresponding metric height
        y_angle = (y - calibration.ya) / (calibration.yb - calibration.ya) * np.pi / 2
        y_angle = np.clip(y_angle, 0, np.pi / 2 - 0.01)
        y_tan = np.tan(y_angle)
        self.y_metric = y_tan * self.config['camera_mount_distance']

        # calculate the grid of beam interception points
        self.beam_yv = np.round(y[:, np.newaxis]).astype(np.int32)
        self.beam_xv = np.round(calibration.x0[np.newaxis, :] + calibration.m[np.newaxis, :] * y[:, np.newaxis]).astype(np.int32)

    def _calculate_beam_length(self, frame: np.ndarray) -> np.ndarray:
        if self.calibration is None:
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

        return self.Result(active, length, modulation)

    def process(self, buffer) -> Result:
        # convert the buffer to a numpy image array
        frame = np.frombuffer(buffer, dtype=np.uint8)

        # extract the luminance component
        w, h = self.config['camera_resolution']
        frame = frame.reshape((h * 3 // 2, w))
        frame = frame[:h, :w]

        # process the frame
        raw_length = self._calculate_beam_length(frame)
        result = self._apply_filter(raw_length)

        return result

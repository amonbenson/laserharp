from dataclasses import dataclass
import numpy as np
import cv2
from perci import ReactiveDictNode
from .image_calibrator import Calibration
from .laser_array import LaserArray
from .camera import Camera
from .component import Component


class KalmanFilter1D:
    def __init__(self, num_elements, process_variance=1e-5, measurement_variance=0.01):
        self.N = num_elements

        # State estimate (initial guess)
        self.x = np.zeros(self.N)

        # Error covariance
        self.P = np.ones(self.N)

        # Process noise
        self.Q = np.full(self.N, process_variance)

        # Measurement noise
        self.R = np.full(self.N, measurement_variance)

        # Track which filters have been activated before
        self.initialized = np.zeros(self.N, dtype=bool)

    def update(self, z, active):
        """
        z: observed measurements (shape: N,)
        active: boolean array (shape: N,), indicating if the filter is active
        """
        # Reset filters that are not active
        reset_indices = ~active
        self.x[reset_indices] = 0
        self.P[reset_indices] = 1
        self.initialized[reset_indices] = False

        # Only update active filters
        update_indices = active

        # For first-time activation, initialize the state estimate to the measurement
        first_active = update_indices & ~self.initialized
        self.x[first_active] = z[first_active]
        self.initialized[first_active] = True

        # Standard Kalman update for active indices
        if np.any(update_indices):
            # Predict
            self.P[update_indices] += self.Q[update_indices]

            # Compute Kalman gain
            K = self.P[update_indices] / (self.P[update_indices] + self.R[update_indices])

            # Update state
            self.x[update_indices] += K * (z[update_indices] - self.x[update_indices])

            # Update covariance
            self.P[update_indices] *= (1 - K)

        return self.x.copy()


class ImageProcessor(Component):
    @dataclass
    class Result:
        active: np.ndarray
        length: np.ndarray
        modulation: np.ndarray

    def __init__(self, name: str, global_state: ReactiveDictNode, laser_array: LaserArray, camera: Camera):
        super().__init__(name, global_state)

        self.laser_array = laser_array
        self.camera = camera

        self.calibration = None

        self.filter_coeff = self._calculate_coeff()
        self.filter_taps = np.zeros((len(self.filter_coeff), len(self.laser_array)), dtype=np.float32)

        self.beam_active = np.zeros(len(self.laser_array), dtype=bool)
        self.beam_active_duration = np.zeros(len(self.laser_array), dtype=np.float32)

        self.beam_kalman_filter = KalmanFilter1D(len(self.laser_array), process_variance=0.1, measurement_variance=1.0)

        # values initialized by set_calibration()
        self.y_metric = None
        self.beam_yv = None
        self.beam_xv = None

        self.state["result"] = None

    def start(self):
        self.state["result"] = {
            "active": [False] * len(self.laser_array),
            "length": [0.0] * len(self.laser_array),
            "modulation": [0.0] * len(self.laser_array),
        }

    def stop(self):
        self.state["result"] = None

    def _calculate_coeff(self) -> np.ndarray:
        # compute number of taps
        f_sampling = self.camera.framerate
        f_cutoff = self.config["filter_cutoff"]
        n = self.config["filter_size"]

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
        self.y_metric = y_tan * self.camera.config["mount_distance"]

        # calculate the grid of beam interception points
        # generate the x values using the stored polynom coefficients
        self.beam_yv = np.round(y[:, np.newaxis]).astype(np.int32)
        self.beam_xv = np.clip(np.round(
            calibration.a[np.newaxis, :] * y[:, np.newaxis] * y[:, np.newaxis] +
            calibration.b[np.newaxis, :] * y[:, np.newaxis] +
            calibration.c[np.newaxis, :]
        ).astype(np.int32), 0, self.camera.resolution[0] - 1)

    @property
    def is_calibrated(self):
        return self.calibration is not None

    def _calculate_beam_length(self, frame: np.ndarray) -> np.ndarray:
        if not self.is_calibrated:
            raise RuntimeError("No calibration data available")

        # get the brightness for each beam
        brightness = frame[self.beam_yv, self.beam_xv]

        # find the strongest interception point for each beam
        strength = np.max(brightness, axis=0)
        position = np.argmax(brightness, axis=0)

        # apply kalman filter to the position
        position = self.beam_kalman_filter.update(position, active=(strength > self.settings["threshold"]))

        # lookup the metric length of each beam
        # length = self.y_metric[position]

        # lookup the metric length of each beam (with linear interpoliation to allow float indices)
        xs = np.arange(len(self.y_metric))
        length = np.interp(position, xs, self.y_metric)

        # filter out invalid interception points
        length[strength < self.settings["threshold"]] = np.nan
        length[length < self.config["length_min"]] = np.nan
        length[length > self.config["length_max"]] = np.nan

        return length

    def _apply_filter(self, raw_length: np.ndarray):
        # store if any beam just became active
        active = np.isfinite(raw_length)
        rising = active & ~self.beam_active
        self.beam_active = active

        # update active duration (increment if active, reset otherwise)
        self.beam_active_duration = np.where(active, self.beam_active_duration + 1 / self.camera.framerate, 0)

        # apply a low pass filter to the beam length
        self.filter_taps[1:] = self.filter_taps[:-1]
        self.filter_taps[0] = raw_length

        # clear all taps for inactive beams
        self.filter_taps[:, ~active] = np.nan

        # set all taps for beams that just became active
        self.filter_taps[:, rising] = raw_length[rising]

        # store the low frequency content as the actual length
        length = np.nansum(self.filter_taps * self.filter_coeff[:, np.newaxis], axis=0)
        length[~active] = np.nan  # keep NaNs

        # store the high frequency content as the modulation
        modulation = raw_length - length
        modulation = np.tanh(modulation * self.config["modulation_gain"])
        modulation[~active] = 0  # inactive beams have no modulation

        # apply a factor to the modulation based on the intersection duration
        durationFactor = np.tanh((self.beam_active_duration - self.config["modulation_delay"]) * 10) * 0.5 + 0.5
        modulation *= durationFactor

        return self.Result(active, length, modulation)

    def process(self, frame) -> Result:
        # process the frame
        raw_length = self._calculate_beam_length(frame)
        result = self._apply_filter(raw_length)

        # store the new result values
        for i in range(len(self.laser_array)):
            self.state["result"]["active"][i] = bool(result.active[i])
            self.state["result"]["length"][i] = float(result.length[i]) if np.isfinite(result.length[i]) else 0.0
            self.state["result"]["modulation"][i] = float(result.modulation[i]) if np.isfinite(result.modulation[i]) else 0.0

        return result

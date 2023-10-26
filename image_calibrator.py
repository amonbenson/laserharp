from dataclasses import dataclass
import numpy as np
from .camera import Camera
from .laser_array import LaserArray

@dataclass
class Calibration:
    # y limits in pixels
    ya: float
    yb: float

    # beam line parameters in pixels
    x0: np.ndarray
    m: np.ndarray

    def __post_init__(self):
        # type casting
        self.ya = np.float32(self.ya)
        self.yb = np.float32(self.yb)
        self.x0 = np.array(self.x0, dtype=np.float32)
        self.m = np.array(self.m, dtype=np.float32)

        # sanity checks
        assert self.ya < self.yb
        assert len(self.x0) == len(self.m)


class ImageCalibrator:
    def __init__(self, camera: Camera, laser_array: LaserArray, **config):
        self.config = config

        self.camera = camera
        self.laser_array = laser_array

    def calibrate(self):
        pass

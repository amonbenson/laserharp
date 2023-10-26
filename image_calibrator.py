from dataclasses import dataclass
import numpy as np

@dataclass
class Calibration:
    # y limits in pixels
    ya: float
    yb: float

    # beam line parameters in pixels
    x0: np.ndarray
    m: np.ndarray

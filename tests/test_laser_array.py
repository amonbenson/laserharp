import unittest
import numpy as np
import cv2
from ..laser_array import LaserArray


class Test_LaserArray(unittest.TestCase):
    def setUp(self):
        config = {
            'num_lasers': 3
        }
        self.laser_array = LaserArray(**config)

    def tearDown(self):
        pass

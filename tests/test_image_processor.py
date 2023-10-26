import unittest
import numpy as np
import cv2
from ..image_processor import ImageProcessor
from ..image_calibrator import Calibration
from . import OUTPUT_DIRECTORY


class Test_ImageProcessor(unittest.TestCase):
    def setUp(self):
        config = {
            'num_lasers': 3,
            'camera_resolution': (640, 480),
            'camera_framerate': 60,
            'camera_mount_distance': 0.2,
            'preblur': 23,
            'threshold': 10,
            'length_min': 0.05,
            'length_max': 2.0,
            'filter_size': 23,
            'filter_cutoff': 6,
            'modulation_gain': 15
        }
        self.processor = ImageProcessor(**config)

        calibration = Calibration(
            ya=0,
            yb=480,
            x0=[200, 300, 400],
            m=[-0.1, 0, 0.1])
        self.processor.set_calibration(calibration)

    def tearDown(self):
        pass

    def _as_stream(self, frame: np.ndarray) -> np.ndarray:
        assert(len(frame.shape) == 2)
        assert(frame.dtype == np.uint8)
        #cv2.imwrite(str(OUTPUT_DIRECTORY / 'tmp_original.png'), frame)

        # append empty UV data
        h, w = frame.shape
        uv = np.zeros((h // 2, w), dtype=np.uint8)
        frame = np.vstack((frame, uv))
        #cv2.imwrite(str(OUTPUT_DIRECTORY / 'tmp_yuv_stream.png'), frame)

        # convert to byte stream
        return frame.tobytes()

    def test_calibration(self):
        # test if y coordinates are correct
        self.assertEqual(self.processor.beam_yv[0, 0], 0)
        self.assertEqual(self.processor.beam_yv[-1, 0], 479)

        # test if x coordinates are correct.
        self.assertEqual(self.processor.beam_xv[0].tolist(), [200, 300, 400])
        self.assertEqual(self.processor.beam_xv[100].tolist(), [190, 300, 410])

    def test_beam_length(self):
        frame = np.zeros((480, 640), dtype=np.uint8)

        # test an empty image. This should return all NaNs
        result = self.processor.process(self._as_stream(frame))
        self.assertTrue(np.all(np.isnan(result.length)))

        # test a single beam at the center.
        # As we set ya and yb to span the whole frame, y=240 should correspond to the center angle
        # at 45 degrees. This way, the metric distance should be equal to the camera mount distance.
        frame = cv2.circle(frame, (300, 240), 10, 255, -1)
        result = self.processor.process(self._as_stream(frame))
        self.assertAlmostEqual(result.length[1], 0.2, places=3)

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
            'camera': {
                'resolution': (640, 480),
                'framerate': 60,
                'mount_distance': 0.2
            },
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

        w, h = config['camera']['resolution']
        self.frame = np.zeros((h, w), dtype=np.uint8)

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

    def test_empty_frame(self):
        # test an empty image. This should return all NaNs
        result = self.processor.process(self._as_stream(self.frame))
        self.assertTrue(np.all(np.isnan(result.length)))
        self.assertEqual(result.modulation.tolist(), [0, 0, 0])

    def test_beam_length(self):
        # Add the first spot in the center.
        # As we set ya and yb to span the whole frame, y=240 should correspond to the center angle
        # at 45 degrees. This way, the metric distance should be equal to the camera mount distance.
        # Add another spot on the right. It will be at tan(100 / 480 * 90deg) * 0.2m ~= 0.06789m
        self.frame = cv2.circle(self.frame, (300, 240), 10, 255, -1)
        self.frame = cv2.circle(self.frame, (410, 100), 10, 255, -1)
        result = self.processor.process(self._as_stream(self.frame))

        # test for the correct length
        self.assertTrue(np.isnan(result.length[0])) # not intercepted
        self.assertAlmostEqual(result.length[1], 0.2, places=3)
        self.assertAlmostEqual(result.length[2], 0.06789, places=3)

        # as this is the first frame, no modulation should be applied
        self.assertAlmostEqual(result.modulation[0], 0, places=3)
        self.assertAlmostEqual(result.modulation[1], 0, places=3)
        self.assertAlmostEqual(result.modulation[2], 0, places=3)

    def test_beam_modulation(self):
        # process a few frames and move the spot up each frame
        for i in range(5):
            self.frame = np.zeros_like(self.frame)
            self.frame = cv2.circle(self.frame, (300, 240 + i * 10), 10, 255, -1)

            result = self.processor.process(self._as_stream(self.frame))

        self.assertAlmostEqual(result.modulation[0], 0.0, places=3)
        self.assertGreater(result.modulation[1], 0.1) # positive modulation
        self.assertAlmostEqual(result.modulation[2], 0.0, places=3)

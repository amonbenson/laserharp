import unittest
import numpy as np
from perci import reactive
from src.laserharp.laser_array import LaserArray
from src.laserharp.image_processor import ImageProcessor
from src.laserharp.image_calibrator import Calibration
from .mocks import MockIPCController, MockCamera


class TestImageProcessor(unittest.TestCase):
    def setUp(self):
        self.global_state = reactive(
            {
                "config": {
                    "ipc": {},
                    "laser_array": {
                        "size": 3,
                    },
                    "camera": {
                        "resolution": [640, 480],
                        "framerate": 60,
                        "mount_distance": 0.2,
                    },
                    "image_processor": {
                        "preblur": 23,
                        "threshold": 10,
                        "length_min": 0.05,
                        "length_max": 2.0,
                        "filter_size": 23,
                        "filter_cutoff": 6,
                        "modulation_gain": 15,
                    },
                },
                "settings": {
                    "ipc": {},
                    "laser_array": {},
                    "camera": {},
                    "image_processor": {},
                },
                "state": {
                    "ipc": {},
                    "laser_array": {},
                    "camera": {},
                    "image_processor": {},
                },
            }
        )

        self.ipc = MockIPCController("ipc", self.global_state)
        self.laser_array = LaserArray("laser_array", self.global_state, self.ipc)
        self.camera = MockCamera("camera", self.global_state)
        self.image_processor = ImageProcessor("image_processor", self.global_state, self.laser_array, self.camera)

        # set the calibration data
        calibration = Calibration(ya=0, yb=480, x0=[200, 300, 400], m=[-0.1, 0, 0.1])
        self.image_processor.set_calibration(calibration)

    def tearDown(self):
        pass

    def test_calibration(self):
        # test if y coordinates are correct
        self.assertEqual(self.image_processor.beam_yv[0, 0], 0)
        self.assertEqual(self.image_processor.beam_yv[-1, 0], 479)

        # test if x coordinates are correct.
        self.assertEqual(self.image_processor.beam_xv[0].tolist(), [200, 300, 400])
        self.assertEqual(self.image_processor.beam_xv[100].tolist(), [190, 300, 410])

    def test_empty_frame(self):
        # test an empty image. This should return all NaNs
        result = self.image_processor.process(self.camera.capture())
        self.assertTrue(np.all(np.isnan(result.length)))
        self.assertEqual(result.modulation.tolist(), [0, 0, 0])

    def test_beam_length(self):
        # Add the first spot in the center.
        # As we set ya and yb to span the whole frame, y=240 should correspond to the center angle
        # at 45 degrees. This way, the metric distance should be equal to the camera mount distance.
        # Add another spot on the right. It will be at tan(100 / 480 * 90deg) * 0.2m ~= 0.06789m
        self.camera.draw_blob(300, 240, 10, 255)
        self.camera.draw_blob(410, 100, 10, 255)
        result = self.image_processor.process(self.camera.capture())

        # test for the correct length
        self.assertTrue(np.isnan(result.length[0]))  # not intercepted
        self.assertAlmostEqual(result.length[1], 0.2, places=3)
        self.assertAlmostEqual(result.length[2], 0.06789, places=3)

        # as this is the first frame, no modulation should be applied
        self.assertAlmostEqual(result.modulation[0], 0, places=3)
        self.assertAlmostEqual(result.modulation[1], 0, places=3)
        self.assertAlmostEqual(result.modulation[2], 0, places=3)

    def test_beam_modulation(self):
        # process a few frames and move the spot up each frame
        for i in range(5):
            self.camera.clear()
            self.camera.draw_blob(300, 240 + i * 10, 10, 255)

            result = self.image_processor.process(self.camera.capture())

        self.assertAlmostEqual(result.modulation[0], 0.0, places=3)
        self.assertGreater(result.modulation[1], 0.1)  # positive modulation
        self.assertAlmostEqual(result.modulation[2], 0.0, places=3)


if __name__ == "__main__":
    unittest.main()

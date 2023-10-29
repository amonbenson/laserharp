import unittest
import time
import numpy as np
from threading import Thread
from .utils import MockIPC, MockCamera, wait_until
from ..laser_array import LaserArray
from ..image_calibrator import Calibration, ImageCalibrator
from . import OUTPUT_DIRECTORY


class Test_ImageCalibrator(unittest.TestCase):
    def setUp(self):
        self.ipc = MockIPC(config={
            'cables': {
                'laser_array': 3
            }
        })

        self.laser_array = LaserArray(self.ipc, config={
            'size': 3,
            'laser_translation_table': None
        })

        self.camera = MockCamera(config={
            'fov': (50, 45),
            'mount_angle': 45,
            'mount_distance': 0.135,
            'resolution': (640, 480),
            'framerate': 60,
            'mount_distance': 0.2
        })

        self.image_calibrator = ImageCalibrator(self.laser_array, self.camera, config={
            'preblur': 17,
            'threshold': 100,
            'min_coverage': 0.6
        })

        self.calibration = None

    def tearDown(self):
        pass

    def _do_calibration(self):
        self.calibration = self.image_calibrator.calibrate()

    def test_calibrate(self):
        x0 = np.array([200, 300, 400])
        m = np.array([-0.1, 0.0, 0.1])

        # turn on all lasers
        # use a value other than maximum to check if the calibration restores the original values correctly
        self.laser_array[:] = 100

        calibration_thread = Thread(target=self._do_calibration)
        calibration_thread.start()

        # wait until all lasers get turned off
        while all(self.laser_array):
            time.sleep(0.01)

        # present the base image
        self.camera.clear()

        # wait until laser 0 is turned on
        while not self.laser_array[0]:
            time.sleep(0.01)

        # draw only a few blobs
        for y in range(0, 480, 100):
            self.camera.draw_blob(x0[0] + m[0] * y, y, 5, 255)
        self.camera.save(OUTPUT_DIRECTORY / 'test_image_calibrator_0.0.png')

        # The number of blobs should be less than the required coverage.
        # Therefore, the calibration should not continue and laser 0 should still be active.
        time.sleep(2)
        self.assertTrue(self.laser_array[0])

        # draw the rest of the blobs. this should now trigger the calibration to continue
        for y in range(0, 480, 15):
            self.camera.draw_blob(x0[0] + m[0] * y, y, 5, 255)
        self.camera.save(OUTPUT_DIRECTORY / 'test_image_calibrator_0.1.png')

        # make sure the laser gets turned off within a second
        self.assertTrue(wait_until(lambda: not self.laser_array[0], timeout=2))

        # calibrate the other two lasers
        for i in range(1, 3):
            # wait until the next laser is turned on
            self.assertTrue(wait_until(lambda: self.laser_array[i], timeout=2))

            # prepare the blobs for that beam
            self.camera.clear()
            for y in range(0, 480, 15):
                self.camera.draw_blob(x0[i] + m[i] * y, y, 5, 255)
            self.camera.save(OUTPUT_DIRECTORY / f'test_image_calibrator_{i}.png')

            # wait until the laser is turned off
            self.assertTrue(wait_until(lambda: not self.laser_array[i], timeout=2))

        # wait for the calibration to finish
        calibration_thread.join()

        # check if the previous laser state was restored
        self.assertEqual(self.laser_array[0], 100)
        self.assertEqual(self.laser_array[1], 100)
        self.assertEqual(self.laser_array[2], 100)

        # check if the calibration is correct
        self.assertAlmostEqual(self.calibration.ya, -0.5 * 480, delta=0.5, msg='ya')
        self.assertAlmostEqual(self.calibration.yb, 1.5 * 480, delta=0.5, msg='yb')

        for i in range(3):
            self.assertAlmostEqual(self.calibration.x0[i], x0[i], delta=0.5, msg='x0[{}]'.format(i))
            self.assertAlmostEqual(self.calibration.m[i], m[i], delta=0.01, msg='m[{}]'.format(i))


if __name__ == '__main__':
    unittest.main()

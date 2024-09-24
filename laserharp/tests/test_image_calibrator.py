import os
import unittest
import time
from threading import Thread
import numpy as np
import yaml
from perci import reactive
from src.laserharp.laser_array import LaserArray
from src.laserharp.image_calibrator import Calibration, ImageCalibrator
from .mocks import MockIPCController, MockCamera
from .utils import wait_until
from . import OUTPUT_DIRECTORY


class TestImageCalibrator(unittest.TestCase):
    def setUp(self):
        self.global_state = reactive(
            {
                "ipc": {
                    "config": {},
                    "settings": {},
                    "state": {},
                },
                "laser_array": {
                    "config": {
                        "size": 3,
                    },
                    "settings": {},
                    "state": {},
                },
                "camera": {
                    "config": {
                        "fov": [50, 45],
                        "mount_angle": 45,
                        "mount_distance": 0.135,
                        "resolution": [640, 480],
                        "framerate": 60,
                        "rotation": 180,
                    },
                    "settings": {},
                    "state": {},
                },
                "image_calibrator": {
                    "config": {
                        "calibration_file": os.path.join(OUTPUT_DIRECTORY, "calibration.yaml"),
                        "preblur": 17,
                        "threshold": 100,
                        "min_coverage": 0.6,
                    },
                    "settings": {},
                    "state": {},
                },
            },
        )

        self.ipc = MockIPCController("ipc", self.global_state)
        self.laser_array = LaserArray("laser_array", self.global_state, self.ipc)
        self.camera = MockCamera("camera", self.global_state)
        self.image_calibrator = ImageCalibrator("image_calibrator", self.global_state, self.laser_array, self.camera)

        self.calibration = None

    def tearDown(self):
        pass

    def _do_calibration(self):
        self.calibration = self.image_calibrator.calibrate()

    def test_load_unknown_file(self):
        self.image_calibrator.filename = "unknown_something.yaml"
        self.assertFalse(self.image_calibrator.load())

    def test_load_incompatible(self):
        # write a sample config
        with open(self.image_calibrator.filename, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                {
                    "required_config": {
                        "laser_array": {
                            "size": 2,  # incompatible
                            "translation_table": None,
                        },
                        "camera": {
                            "fov": (50, 45),
                            "mount_angle": 45,
                            "resolution": (640, 480),
                            "rotation": 180,
                        },
                    },
                    "calibration": {
                        "ya": 0,
                        "yb": 480,
                        "x0": [200, 300],
                        "m": [-0.1, 0.1],
                    },
                },
                f,
            )

        self.assertFalse(self.image_calibrator.load())

    def test_load(self):
        # write a sample config
        with open(self.image_calibrator.filename, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                {
                    "required_config": self.image_calibrator.required_config(),
                    "calibration": {
                        "ya": -10,
                        "yb": 200,
                        "x0": [250, 350, 450],
                        "m": [-0.2, 0.0, 0.2],
                    },
                },
                f,
            )

        # load the config
        self.assertTrue(self.image_calibrator.load())

        # check the values
        self.assertAlmostEqual(self.image_calibrator.calibration.ya, -10, delta=0.01)
        self.assertAlmostEqual(self.image_calibrator.calibration.yb, 200, delta=0.01)
        self.assertAlmostEqual(self.image_calibrator.calibration.x0[0], 250, delta=0.01)
        self.assertAlmostEqual(self.image_calibrator.calibration.x0[1], 350, delta=0.01)
        self.assertAlmostEqual(self.image_calibrator.calibration.x0[2], 450, delta=0.01)
        self.assertAlmostEqual(self.image_calibrator.calibration.m[0], -0.2, delta=0.01)
        self.assertAlmostEqual(self.image_calibrator.calibration.m[1], 0.0, delta=0.01)
        self.assertAlmostEqual(self.image_calibrator.calibration.m[2], 0.2, delta=0.01)

    def test_save(self):
        # store the config
        self.image_calibrator.calibration = Calibration(ya=-20, yb=300, x0=[150, 250, 350], m=[-0.3, 0.0, 0.3])
        self.image_calibrator.save()

        # check the output file
        with open(self.image_calibrator.filename, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            calibration = config["calibration"]

            self.assertAlmostEqual(calibration["ya"], -20, delta=0.01)
            self.assertAlmostEqual(calibration["yb"], 300, delta=0.01)
            self.assertAlmostEqual(calibration["x0"][0], 150, delta=0.01)
            self.assertAlmostEqual(calibration["x0"][1], 250, delta=0.01)
            self.assertAlmostEqual(calibration["x0"][2], 350, delta=0.01)
            self.assertAlmostEqual(calibration["m"][0], -0.3, delta=0.01)
            self.assertAlmostEqual(calibration["m"][1], 0.0, delta=0.01)
            self.assertAlmostEqual(calibration["m"][2], 0.3, delta=0.01)

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
        self.camera.save(OUTPUT_DIRECTORY / "test_image_calibrator_0.0.png")

        # The number of blobs should be less than the required coverage.
        # Therefore, the calibration should not continue and laser 0 should still be active.
        time.sleep(2)
        self.assertTrue(self.laser_array[0])

        # draw the rest of the blobs. this should now trigger the calibration to continue
        for y in range(0, 480, 15):
            self.camera.draw_blob(x0[0] + m[0] * y, y, 5, 255)
        self.camera.save(OUTPUT_DIRECTORY / "test_image_calibrator_0.1.png")

        # make sure the laser gets turned off within a second
        self.assertTrue(wait_until(lambda: not self.laser_array[0], timeout=2))

        # calibrate the other two lasers
        for i in range(1, 3):
            # wait until the next laser is turned on
            self.assertTrue(wait_until(lambda _i=i: self.laser_array[_i], timeout=2))

            # prepare the blobs for that beam
            self.camera.clear()
            for y in range(0, 480, 15):
                self.camera.draw_blob(x0[i] + m[i] * y, y, 5, 255)
            self.camera.save(OUTPUT_DIRECTORY / f"test_image_calibrator_{i}.png")

            # wait until the laser is turned off
            self.assertTrue(wait_until(lambda _i=i: not self.laser_array[_i], timeout=2))

        # wait for the calibration to finish
        calibration_thread.join()

        # check if the previous laser state was restored
        self.assertEqual(self.laser_array[0], 100)
        self.assertEqual(self.laser_array[1], 100)
        self.assertEqual(self.laser_array[2], 100)

        # check if the calibration is correct
        self.assertAlmostEqual(self.calibration.ya, -0.5 * 480, delta=0.5, msg="ya")
        self.assertAlmostEqual(self.calibration.yb, 1.5 * 480, delta=0.5, msg="yb")

        for i in range(3):
            self.assertAlmostEqual(self.calibration.x0[i], x0[i], delta=0.5, msg=f"x0[{i}]")
            self.assertAlmostEqual(self.calibration.m[i], m[i], delta=0.01, msg=f"m[{i}]")


if __name__ == "__main__":
    unittest.main()

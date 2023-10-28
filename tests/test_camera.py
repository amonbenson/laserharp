import unittest
import time
import cv2
from ..camera import Camera
from . import OUTPUT_DIRECTORY


class Test_Camera(unittest.TestCase):
    def setUp(self):
        self.camera = Camera()
        self.camera.start()

    def tearDown(self):
        self.camera.stop()
        self.camera.close()

    def test_running(self):
        # wait until the camera is running
        while not self.camera.running:
            time.sleep(0.1)

    def test_capture(self):
        # capture a frame
        frame = self.camera.capture()

        # check the frame size and make sure it's not empty
        self.assertEqual(frame.shape, (480, 640, 3))
        self.assertTrue(frame.any())

        # save the frame to a file
        cv2.imwrite(str(OUTPUT_DIRECTORY / 'camera_capture.jpg'), frame)

    def test_calibration(self):
        frame = self.camera.capture(draw_calibration=True)
        cv2.imwrite(str(OUTPUT_DIRECTORY / 'camera_calibration.jpg'), frame)


if __name__ == '__main__':
    unittest.main()

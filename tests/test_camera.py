import unittest
import time
from PIL import Image
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

        # check the frame size
        self.assertEqual(frame.shape, (480, 640))

        # make sure the frame is not empty
        self.assertTrue(frame.any())

        # save the frame to a file
        image = Image.fromarray(frame)
        image.save(OUTPUT_DIRECTORY / 'test_camera_capture.jpg')

if __name__ == '__main__':
    unittest.main()

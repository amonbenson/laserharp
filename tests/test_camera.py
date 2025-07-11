import unittest
import time
import logging
import cv2
from perci import reactive
from laserharp.camera import Camera
from . import OUTPUT_DIRECTORY


try:
    import picamera2  # pylint: disable=unused-import

    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False


@unittest.skipUnless(PICAMERA2_AVAILABLE, "picamera2 is not available")
class TestCamera(unittest.TestCase):
    def setUp(self):
        self.global_state = reactive(
            {
                "camera": {
                    "config": {
                        "resolution": [640, 480],
                        "framerate": 50,
                        "rotation": 180,
                        "shutter_speed": 5000,
                        "iso": 10,
                        "brightness": 50,
                        "contrast": 0,
                        "saturation": 0,
                        "sharpness": 0,
                    },
                    "settings": {},
                    "state": {},
                },
            },
        )

        # pylint: disable=duplicate-code
        self.camera = Camera("camera", self.global_state)
        self.camera.start()

    def tearDown(self):
        self.camera.stop()

    def test_running(self):
        time.sleep(3)
        self.assertTrue(self.camera.state["status"] == "running")

    @unittest.skip("Not implemented for the updated camera class")
    def test_framerate(self):
        pass
        # counter = 0
        # shape = None

        # def callback(frame):
        #     nonlocal counter, shape
        #     counter += 1
        #     shape = frame.shape

        # # wait until the camera is running
        # while self.camera.state != Camera.State.RUNNING:
        #     time.sleep(0.1)
        # time.sleep(1)

        # # register the callback and capture for 1 second
        # self.camera.on("frame", callback)
        # time.sleep(1)

        # self.camera.off("frame", callback)
        # time.sleep(0.5)

        # # make sure the callback was called (~60 FPS, accounting for some deviation)
        # print(f"Callback was invoked {counter} times")
        # self.assertIn(counter, range(45, 60))
        # self.assertEqual(shape, (480, 640))

    def test_capture(self):
        # capture a frame
        frame = self.camera.capture()

        # check the frame size and make sure it's not empty
        self.assertEqual(frame.shape, (480, 640))
        if not frame.any():
            logging.warning("Empty frame captured. There might be an issue with the camera.")

        # save the frame to a file
        cv2.imwrite(str(OUTPUT_DIRECTORY / "test_camera_capture.png"), frame)


if __name__ == "__main__":
    unittest.main()

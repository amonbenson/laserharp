import unittest
import time
from ..camera import Camera


class Test_IPCConnector(unittest.TestCase):
    def test_stream(self):
        camera = Camera()
        camera.start()

        time.sleep(2)

        camera.stop()


if __name__ == '__main__':
    unittest.main()

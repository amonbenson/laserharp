import unittest
from src.laserharp.laser_array import LaserArray
from src.laserharp.ipc import IPCController
from perci import reactive
from .mocks import MockSerial


class TestLaserArray(unittest.TestCase):
    def setUp(self):
        self.global_state = reactive(
            {
                "ipc": {
                    "config": {
                        "port": "/dev/ttyUSB0",
                        "baudrate": 115200,
                    },
                    "settings": {},
                    "state": {},
                },
                "laser_array": {
                    "config": {
                        "size": 3,
                        "translation_table": [3, 4, 5],
                    },
                    "settings": {},
                    "state": {},
                },
            }
        )

        # pylint: disable=duplicate-code
        self.serial = MockSerial()
        self.ipc = IPCController("ipc", self.global_state, self.serial)
        self.laser_array = LaserArray("laser_array", self.global_state, self.ipc)

    def tearDown(self):
        pass

    def test_len(self):
        self.assertEqual(len(self.laser_array), 3)

    def test_set(self):
        self.laser_array.set(1, 64)

        # test if the state is correct
        self.assertEqual(self.laser_array[1], 64)

        # test if a message was sent
        self.assertEqual(
            self.serial.txdata,
            bytearray([0x80, 4, 64, 0x00]),
        )

    def test_set_all(self):
        self.laser_array.set_all(101)

        # test if the state is correct
        self.assertEqual(self.laser_array[0], 101)
        self.assertEqual(self.laser_array[1], 101)
        self.assertEqual(self.laser_array[2], 101)

        # test if a message was sent
        self.assertEqual(
            self.serial.txdata,
            bytearray([0x81, 101, 0x00, 0x00]),
        )

        # start a new capture
        self.serial.clear()

        # check if set all works with a slice
        self.laser_array[:] = 127
        self.assertEqual(
            self.serial.txdata,
            bytearray([0x81, 127, 0x00, 0x00]),
        )

    def test_stack(self):
        self.laser_array.set(0, 64)
        self.laser_array.push_state()

        self.laser_array.set(0, 127)
        self.assertEqual(self.laser_array[0], 127)
        self.assertEqual(
            self.serial.txdata,
            bytearray([0x80, 3, 64, 0x00]) + bytearray([0x80, 3, 127, 0x00]),
        )

        # start a new capture
        self.serial.clear()

        self.laser_array.pop_state()
        self.assertEqual(self.laser_array[0], 64)
        self.assertEqual(
            self.serial.txdata,
            bytearray([0x80, 3, 64, 0x00]),
        )


if __name__ == "__main__":
    unittest.main()

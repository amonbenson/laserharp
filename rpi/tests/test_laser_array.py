import unittest
from src.laserharp.laser_array import LaserArray
from src.laserharp.ipc import IPCController
from perci import reactive
from .utils import MockSerial


class TestLaserArray(unittest.TestCase):
    def setUp(self):
        global_state = reactive(
            {
                "config": {
                    "ipc": {
                        "port": "/dev/ttyUSB0",
                        "baudrate": 115200,
                    },
                    "laser_array": {
                        "size": 3,
                        "translation_table": [3, 4, 5],
                    },
                },
                "settings": {
                    "ipc": {},
                    "laser_array": {},
                },
                "state": {},
            }
        )

        self.serial = MockSerial()

        # pylint: disable=duplicate-code
        self.ipc = IPCController(
            name="ipc",
            global_state=global_state,
            custom_serial=self.serial,
        )

        self.laser_array = LaserArray(self.ipc, config=global_state["config"]["laser_array"])

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

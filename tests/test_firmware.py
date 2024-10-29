import unittest
import os
import time
from perci import reactive
from laserharp.ipc import IPCController

SERIAL_PORT = "/dev/ttyAMA0"
SERIAL_PORT_AVAILABLE = os.path.exists(SERIAL_PORT) and os.access(SERIAL_PORT, os.W_OK)


@unittest.skipUnless(SERIAL_PORT_AVAILABLE, f"IPC serial port {SERIAL_PORT} not available")
class TestFirmware(unittest.TestCase):
    def setUp(self):
        self.global_state = reactive(
            {
                "ipc": {
                    "config": {
                        "port": SERIAL_PORT,
                        "baudrate": 115200,
                    },
                    "settings": {},
                    "state": {},
                },
            },
        )

        self.ipc = IPCController("ipc", self.global_state)
        self.ipc.start()

        # turn off all lasers
        self.ipc.send_raw(b"\x81\x00\x00\x00")

    def tearDown(self):
        # stop animations and turn off all lasers
        self.ipc.send_raw(b"\x83\x00\x00\x00")
        self.ipc.send_raw(b"\x81\x00\x00\x00")

        self.ipc.stop()
        del self.ipc

    def test_set_brightness(self):
        # set all lasers to 100% brightness
        self.ipc.send_raw(b"\x81\x7f\x00\x00")

        # check if the brightness was set on diodes 4 and 5
        self.ipc.send_raw(b"\x82\x04\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x04\x7f\x00")

        self.ipc.send_raw(b"\x82\x05\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x05\x7f\x00")

        # set laser diod 5 to 0% brightness
        self.ipc.send_raw(b"\x80\x05\x00\x00")

        # now only diode 4 should be at 100% brightness and diode 5 at 0%
        self.ipc.send_raw(b"\x82\x04\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x04\x7f\x00")

        self.ipc.send_raw(b"\x82\x05\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x05\x00\x00")

    def test_fade_brightness(self):
        # fade diode 5 from 0% to 100% brightness in 1s
        self.ipc.send_raw(b"\x80\x05\x00\x00")
        self.ipc.send_raw(b"\x80\x05\x7f\x0a")

        # check if the brightness is somewhere between 0% and 100% after 0.5s
        time.sleep(0.5)
        self.ipc.send_raw(b"\x82\x05\x00\x00")
        response = self.ipc.read_raw()
        self.assertEqual(len(response), 4)
        self.assertIn(response[2], range(1, 127))

        # check if the brightness is 100% after 1s
        time.sleep(0.5)
        self.ipc.send_raw(b"\x82\x05\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x05\x7f\x00")

    def test_version_inquiry(self):
        self.ipc.send_raw(b"\xf0\x00\x00\x00")
        res = self.ipc.read_raw()

        self.assertEqual(res[0], 0xF0)
        self.assertTrue(res[1] > 0 or res[2] > 0)  # major or minor version should be greater than 0

    def test_reboot(self):
        # set all lasers to 100% brightness
        self.ipc.send_raw(b"\x81\x7f\x00\x00")

        # send the reboot command
        self.ipc.send_raw(b"\xf1\x00\x00\x00")

        # wait for the device to reboot
        time.sleep(0.2)

        # send any command to stop the boot animation (in this case a version inquiry)
        self.ipc.send_raw(b"\xf0\x00\x00\x00")
        self.assertEqual(len(self.ipc.read_raw()), 4)

        # get the brightness of diode 4. After a reboot it should be 0%
        self.ipc.send_raw(b"\x82\x04\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x04\x00\x00")

    def test_animation_loop(self):
        # start the test animation at 1s duration. This toggle between diodes 4 and 5 every 500ms
        self.ipc.send_raw(b"\x83\x02\x0a\x00")

        # check if the first frame is correct
        time.sleep(0.05)
        self.ipc.send_raw(b"\x82\x04\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x04\x7f\x00")

        self.ipc.send_raw(b"\x82\x05\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x05\x00\x00")

        # check if the second frame is correct
        time.sleep(0.5)
        self.ipc.send_raw(b"\x82\x04\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x04\x00\x00")

        self.ipc.send_raw(b"\x82\x05\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x05\x7f\x00")

        # check if the animation loops after one second
        time.sleep(0.5)
        self.ipc.send_raw(b"\x82\x04\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x04\x7f\x00")

        self.ipc.send_raw(b"\x82\x05\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x05\x00\x00")

    def test_animation_stop(self):
        # set all lasers to 100% brightness
        self.ipc.send_raw(b"\x81\x7f\x00\x00")  # turn on all lasers

        # start the test animation at 0.1s duration with follow action 1 (stop last frame)
        self.ipc.send_raw(b"\x83\x02\x01\x01")  # start the animation

        # check if the last frame is still displayed when the animation stops (diode 5 is on)
        time.sleep(0.2)
        self.ipc.send_raw(b"\x82\x04\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x04\x00\x00")

        self.ipc.send_raw(b"\x82\x05\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x05\x7f\x00")

        # now start the animation with follow action 2 (turn off all lasers)
        self.ipc.send_raw(b"\x81\x7f\x00\x00")  # turn on all lasers
        self.ipc.send_raw(b"\x83\x02\x01\x02")  # start the animation

        # check if all lasers are off
        time.sleep(0.2)
        self.ipc.send_raw(b"\x82\x04\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x04\x00\x00")

        self.ipc.send_raw(b"\x82\x05\x00\x00")
        self.assertEqual(self.ipc.read_raw(), b"\x82\x05\x00\x00")


if __name__ == "__main__":
    unittest.main()

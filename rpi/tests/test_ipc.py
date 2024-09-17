import unittest
from src.laserharp.ipc import IPCController
from .mocks import MockSerial


class TestIPCConnector(unittest.TestCase):
    def setUp(self):
        self.global_state = reactive(
            {
                "config": {
                    "ipc": {
                        "port": "/dev/ttyUSB0",
                        "baudrate": 115200,
                    },
                },
                "settings": {
                    "ipc": {},
                },
                "state": {
                    "ipc": {},
                },
            }
        )

        self.serial = MockSerial()
        self.ipc = IPCController("ipc", self.global_state, self.serial)

    def tearDown(self):
        self.serial.clear()

    @unittest.skip("Not implemented after refactoring")
    def test_send_midi(self):
        pass
        # self.ipc.send(MidiEvent("usb", "note_on", note=60, velocity=64))
        # self.assertEqual(self.serial.txdata, bytearray([0x19, 0x90, 60, 64]))

    @unittest.skip("Not implemented after refactoring")
    def test_read_midi(self):
        pass
        # self.serial.rxdata = bytearray([0x28, 0x80, 60, 64])

        # # validate packet midi conversion
        # event = self.ipc.read()
        # self.assertEqual(event.cable, "ble")
        # self.assertEqual(event.message, mido.Message("note_off", note=60, velocity=64))


if __name__ == "__main__":
    unittest.main()

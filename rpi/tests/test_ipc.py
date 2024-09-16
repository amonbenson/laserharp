import unittest
import mido
from src.laserharp.midi import MidiEvent
from src.laserharp.ipc import IPCController
from .utils import MockSerial


class Test_IPCConnector(unittest.TestCase):
    def setUp(self):
        self.serial = MockSerial()
        self.ipc = IPCController(
            config={
                "port": None,  # ignored when using custom_serial
                "baudrate": None,  # ignored when using custom_serial
            },
            custom_serial=self.serial,
        )

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

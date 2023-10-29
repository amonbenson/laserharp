import unittest
import mido
from ..midi import MidiEvent
from ..ipc import IPCController
from .mock import MockSerial

class Test_IPCConnector(unittest.TestCase):
    def setUp(self):
        self.serial = MockSerial()
        self.ipc = IPCController(config={
            'port': None,
            'baudrate': None,
            'cables': {
                'din': 0,
                'usb': 1,
                'ble': 3,
                'laser_array': 4
            }
        }, custom_serial=self.serial)

    def tearDown(self):
        self.serial.clear()

    def test_send_midi(self):
        self.ipc.send(MidiEvent('usb', 'note_on', note=60, velocity=64))
        self.assertEqual(self.serial.txdata, bytearray([0x19, 0x90, 60, 64]))

    def test_read_midi(self):
        self.serial.rxdata = bytearray([0x38, 0x80, 60, 64])

        # validate packet midi conversion
        event = self.ipc.read()
        self.assertEqual(event.cable, 'ble')
        self.assertEqual(event.message, mido.Message('note_off', note=60, velocity=64))


if __name__ == '__main__':
    unittest.main()

import unittest
import mido
from ..midi import MidiEvent
from ..ipc import IPCController
from .utils import MockSerial

class Test_IPCConnector(unittest.TestCase):
    def setUp(self):
        self.serial = MockSerial()
        self.ipc = IPCController(config={
            'port': None,
            'baudrate': None,
            'cables': {
                'din': 0,
                'usb': 1,
                'ble': 2,
                'laser_array': 3
            }
        }, custom_serial=self.serial)

    def tearDown(self):
        self.serial.clear()

    def test_send_midi(self):
        self.ipc.send(MidiEvent('usb', 'note_on', note=60, velocity=64))
        self.assertEqual(self.serial.txdata, bytearray([0x19, 0x90, 60, 64]))

    def test_read_midi(self):
        self.serial.rxdata = bytearray([0x28, 0x80, 60, 64])

        # validate packet midi conversion
        event = self.ipc.read()
        self.assertEqual(event.cable, 'ble')
        self.assertEqual(event.message, mido.Message('note_off', note=60, velocity=64))

    def test_invalid_cable(self):
        # invalid write
        with self.assertRaises(ValueError):
            self.ipc.send(MidiEvent('invalid', 'note_on', note=60, velocity=64))

        # invalid read
        with self.assertRaises(ValueError):
            self.serial.rxdata = bytearray([0x78, 0x80, 60, 64])
            self.ipc.read()


if __name__ == '__main__':
    unittest.main()

import unittest
import mido
from ..midi import MidiEvent
from ..ipc import IPCController

class MockSerial:
    def __init__(self):
        self.txdata = bytearray()
        self.rxdata = bytearray()

    def clear(self):
        self.txdata = bytearray()
        self.rxdata = bytearray()

    @property
    def in_waiting(self):
        return len(self.rxdata)

    def read(self, n):
        data = self.rxdata[:n]
        self.rxdata = self.rxdata[n:]
        return data

    def read_all(self):
        data = self.rxdata
        self.rxdata = bytearray()
        return data

    def write(self, data):
        self.txdata += data


class Test_IPCConnector(unittest.TestCase):
    def setUp(self):
        self.serial = MockSerial()
        self.ipc = IPCController('', custom_serial=self.serial)

    def tearDown(self):
        self.serial.clear()

    def test_send_midi(self):
        self.ipc.send(MidiEvent(1, mido.Message('note_on', note=60, velocity=64)))
        self.assertEqual(self.serial.txdata, bytearray([0x01, 0x90, 60, 64]))

    def test_read_midi(self):
        self.serial.rxdata = bytearray([0x01, 0x90, 60, 64])

        # validate packet midi conversion
        event = self.ipc.read()
        self.assertEqual(event.cable_number, 1)
        self.assertEqual(event.message, mido.Message('note_on', note=60, velocity=64))


if __name__ == '__main__':
    unittest.main()

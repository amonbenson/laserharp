import unittest
import mido
from ..midi import MidiEvent, MidiInterface
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
        self.ipc.send_midi(MidiEvent(MidiInterface.USB, mido.Message('note_on', note=60, velocity=64)))
        self.assertEqual(self.serial.txdata, bytearray([4, 0x01, 0x90, 60, 64]))

    def test_set_laser(self):
        self.ipc.set_laser(5, 234)
        self.assertEqual(self.serial.txdata, bytearray([3, 0x10, 5, 234]))

    def test_set_each_laser(self):
        self.ipc.set_each_laser([0, 255, 127, 63])
        self.assertEqual(self.serial.txdata, bytearray([5, 0x11, 0, 255, 127, 63]))

    def test_set_all_lasers(self):
        self.ipc.set_all_lasers(123)
        self.assertEqual(self.serial.txdata, bytearray([2, 0x12, 123]))

    def test_read_midi(self):
        self.serial.rxdata = bytearray([4, 0x01, 0x90, 60, 64])

        # validate packet binary
        packet = self.ipc.read()
        self.assertEqual(packet.cmd.value, 0x01)
        self.assertEqual(packet.data, bytearray([0x90, 60, 64]))

        # validate packet midi conversion
        event = packet.midi()
        self.assertEqual(event.interface, MidiInterface.USB)
        self.assertEqual(event.message, mido.Message('note_on', note=60, velocity=64))


if __name__ == '__main__':
    unittest.main()

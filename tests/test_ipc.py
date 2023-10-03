import unittest
import mido
from ..ipc import IPCConnector

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
        self.conn = IPCConnector('', custom_serial=self.serial)

    def tearDown(self):
        self.serial.clear()

    def test_send_midi(self):
        self.conn.send_midi(IPCConnector.MidiInterface.USB, mido.Message('note_on', note=60, velocity=64))
        self.assertEqual(self.serial.txdata, bytearray([0x01, 3, 0x90, 60, 64]))

    def test_set_laser(self):
        self.conn.set_laser(5, 234)
        self.assertEqual(self.serial.txdata, bytearray([0x10, 2, 5, 234]))

    def test_set_each_laser(self):
        self.conn.set_each_laser([0, 255, 127, 63])
        self.assertEqual(self.serial.txdata, bytearray([0x11, 4, 0, 255, 127, 63]))

    def test_set_all_lasers(self):
        self.conn.set_all_lasers(123)
        self.assertEqual(self.serial.txdata, bytearray([0x12, 1, 123]))

    def test_read(self):
        self.serial.rxdata = bytearray([0x01, 3, 0x90, 60, 64])
        packet = self.conn.read()
        self.assertEqual(packet.cmd.value, 0x01)
        self.assertEqual(packet.data, bytearray([0x90, 60, 64]))


if __name__ == '__main__':
    unittest.main()

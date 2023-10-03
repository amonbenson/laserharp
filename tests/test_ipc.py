import unittest
import mido
from ..ipc import Packet, MidiPacket, LaserPacket


class Test_Packet(unittest.TestCase):
    def test_empty_packet(self):
        packet = Packet(0x00)
        self.assertEqual(packet.bytes(), b'\x00\x00')

    def test_midi_packet(self):
        packet = MidiPacket.from_message(MidiPacket.Interface.USB, mido.Message('note_on', note=0x3c, velocity=0x40))
        self.assertEqual(packet.bytes(), b'\x01\x03\x90\x3c\x40')

    """
    def test_laser_packet(self):
        packet = LaserPacket.set_single(0x01, 0x80)
        self.assertEqual(packet.bytes(), b'\x10\x02\x01\x80')

        packet = LaserPacket.set_all(0x80)
        self.assertEqual(packet.bytes(), b'\x11\x01\x80')

        packet = LaserPacket.set_each([0x80, 0x40, 0x20, 0x10])
        self.assertEqual(packet.bytes(), b'\x12\x04\x80\x40\x20\x10')
    """


if __name__ == '__main__':
    unittest.main()

from enum import Enum
import mido


class Packet:
    def __init__(self, cmd, data = b''):
        self.cmd = int(cmd)
        self.data = bytearray(data)

    def bytes(self):
        header = bytearray([self.cmd, len(self.data)])
        return header + self.data

    """
    @staticmethod
    def from_bytes(self, bytes: bytearray):
        if len(bytes) < 2:
            raise ValueError("packet must be at least 2 bytes long")

        cmd = bytes[0]
        length = bytes[1]

        if len(bytes) != length + 2:
            raise ValueError(f"packet length mismatch: expected {length + 2}, got {len(bytes)}")

        return Packet(cmd, bytes[2:])
    """


class MidiPacket(Packet):
    class Interface(Enum):
        DIN = 0x00
        USB = 0x01
        BLE = 0x02

    def __init__(self, interface_id: int, data: bytearray = b''):
        cmd = 0x00 | interface_id & 0x0f
        super().__init__(cmd, data)

    @staticmethod
    def from_message(interface: Interface, message: mido.Message):
        return MidiPacket(interface.value, message.bytes())


class LaserPacket(Packet):
    class Command(Enum):
        SET_SINGLE = 0x00
        SET_ALL = 0x01
        SET_EACH = 0x02

    def __init__(self, cmd: Command, data: bytearray = b''):
        cmd = 0x01 | cmd & 0x0f
        super().__init__(cmd, data)

    @staticmethod
    def set_single(index: int, brightness: int):
        return LaserPacket(LaserPacket.Command.SET_SINGLE.value, [index, brightness])

    @staticmethod
    def set_all(brightness: int):
        return LaserPacket(LaserPacket.Command.SET_ALL.value, [brightness])

    @staticmethod
    def set_each(brightnesses: bytearray):
        return LaserPacket(LaserPacket.Command.SET_EACH.value, brightnesses)


class IPCConnector():
    def __init__(self):
        pass

    def send(self, cmd: int, data: bytearray):
        header = bytearray([cmd, len(data)])

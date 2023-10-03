from enum import Enum
from serial import Serial
import mido


class IPCPacket:
    class Command(Enum):
        MIDI_DIN = 0x00
        MIDI_USB = 0x01
        MIDI_BLE = 0x02

        SET_LASER_SINGLE = 0x10
        SET_LASER_EACH = 0x11
        SET_LASER_ALL = 0x12


    def __init__(self, cmd, data = b''):
        self.cmd = IPCPacket.Command(cmd)
        self.data = bytearray(data)

    @property
    def header(self) -> bytearray:
        return bytearray([self.cmd.value, len(self.data)])

    def bytes(self) -> bytearray:
        return self.header + self.data

    @staticmethod
    def from_bytes(data: bytearray):
        if len(data) < 2:
            raise ValueError("Packet too short")

        cmd = data[0]
        length = data[1]
        data = data[2:]

        if len(data) != length:
            raise ValueError(f"Packet length mismatch: expected {length}, got {len(data)}")

        return IPCPacket(IPCPacket.Command(cmd), data)


class IPCConnector():
    class MidiInterface(Enum):
        DIN = IPCPacket.Command.MIDI_DIN.value
        USB = IPCPacket.Command.MIDI_USB.value
        BLE = IPCPacket.Command.MIDI_BLE.value

    def __init__(self, port: str, baudrate: int = 115200, custom_serial = None):
        if custom_serial is not None:
            self._serial = custom_serial
        else:
            self._serial = Serial(port, baudrate)

        self.rx_packets = []

    def _send(self, packet: IPCPacket):
        self._serial.write(packet.bytes())

    def available(self) -> bool:
        return self._serial.in_waiting >= 2

    def read(self) -> IPCPacket:
        # TODO: might miss packets if they arrive too fast
        return IPCPacket.from_bytes(self._serial.read_all())

    def send_midi(self, interface: MidiInterface, message: mido.Message):
        self._send(IPCPacket(interface.value, message.bytes()))

    def set_laser(self, index: int, value: int):
        self._send(IPCPacket(IPCPacket.Command.SET_LASER_SINGLE, bytearray([index, value])))

    def set_each_laser(self, values: list):
        self._send(IPCPacket(IPCPacket.Command.SET_LASER_EACH, bytearray(values)))

    def set_all_lasers(self, value: int):
        self._send(IPCPacket(IPCPacket.Command.SET_LASER_ALL, bytearray([value])))

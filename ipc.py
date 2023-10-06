from enum import Enum
from serial import Serial
import mido
from .midi import MidiEvent, MidiInterface


class IPCPacket:
    class Command(Enum):
        MIDI_DIN = 0x00
        MIDI_USB = 0x01
        MIDI_BLE = 0x02

        SET_LASER_SINGLE = 0x10
        SET_LASER_EACH = 0x11
        SET_LASER_ALL = 0x12


    MIDI_INTERFACE_COMMANDS = {
        MidiInterface.DIN: Command.MIDI_DIN,
        MidiInterface.USB: Command.MIDI_USB,
        MidiInterface.BLE: Command.MIDI_BLE
    }

    MIDI_COMMAND_INTERFACES = {
        Command.MIDI_DIN: MidiInterface.DIN,
        Command.MIDI_USB: MidiInterface.USB,
        Command.MIDI_BLE: MidiInterface.BLE
    }


    def __init__(self, cmd, data = b''):
        self.cmd = IPCPacket.Command(cmd)
        self.data = bytearray(data)

    @property
    def header(self) -> bytearray:
        return bytearray([len(self.data) + 1, self.cmd.value])

    def bytes(self) -> bytearray:
        return self.header + self.data

    def midi(self) -> MidiEvent:
        if self.cmd not in IPCPacket.MIDI_COMMAND_INTERFACES:
            raise ValueError("Packet is not a MIDI message")

        # generate the midi event
        interface = IPCPacket.MIDI_COMMAND_INTERFACES[self.cmd]
        message = mido.Message.from_bytes(self.data)
        return MidiEvent(interface, message)

    @staticmethod
    def from_bytes(data: bytearray):
        if len(data) < 2:
            raise ValueError("Packet too short")

        size = data[0]
        cmd = data[1]
        data = data[2:]

        if len(data) + 1 != size:
            raise ValueError(f"Packet length mismatch: expected {size}, got {len(data)}")

        return IPCPacket(IPCPacket.Command(cmd), data)


class IPCController():
    def __init__(self, port: str, baudrate: int = 115200, custom_serial = None):
        if custom_serial is not None:
            self._serial = custom_serial
        else:
            self._serial = Serial(port, baudrate)

        self.rx_packets = []

    def _send(self, packet: IPCPacket):
        self._serial.write(packet.bytes())

    def read(self) -> IPCPacket:
        # read size
        size = self._serial.read(1)[0]

        # read remaining data
        self._serial.timeout = 0.1
        data = self._serial.read(size)
        self._serial.timeout = None

        if len(data) != size:
            raise TimeoutError("Timeout while reading packet")

        # return the packet
        return IPCPacket.from_bytes(bytearray([size, *data]))

    def send_midi(self, midi_event: MidiEvent):
        cmd = IPCPacket.MIDI_INTERFACE_COMMANDS[midi_event.interface]
        self._send(IPCPacket(cmd, midi_event.message.bytes()))

    def set_laser(self, index: int, value: int):
        self._send(IPCPacket(IPCPacket.Command.SET_LASER_SINGLE, bytearray([index, value])))

    def set_each_laser(self, values: list):
        self._send(IPCPacket(IPCPacket.Command.SET_LASER_EACH, bytearray(values)))

    def set_all_lasers(self, value: int):
        self._send(IPCPacket(IPCPacket.Command.SET_LASER_ALL, bytearray([value])))
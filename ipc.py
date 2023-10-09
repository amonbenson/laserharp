from enum import Enum
import serial
import mido
import numpy as np
from .midi import MidiEvent


class IPCController():
    def __init__(self, port: str, baudrate: int = 115200, custom_serial = None):
        if custom_serial is not None:
            self._serial = custom_serial
        else:
            self._serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS)

    def send(self, event: MidiEvent):
        # only short messages are supported
        message_data = event.message.bytes()
        if len(message_data) != 3:
            raise ValueError(f"Unsupported MIDI event: {event}")

        # construct and send the packet
        cn_cid = np.uint8(event.cable_number << 4 | message_data[0] >> 4)
        self._serial.write(bytearray([cn_cid, *message_data]))

    def read(self) -> MidiEvent:
        # read a packet
        data = self._serial.read(4)
        if len(data) != 4:
            raise ValueError(f"Invalid packet size: {len(data)}")
        #print(f"IPC read: {data.hex(' ')}")

        # parse the packet
        cn = data[0] >> 4
        cid = data[0] & 0x0F

        if (cid >= 0x8 and cid <= 0xE):
            return MidiEvent(cn, mido.Message.from_bytes(data[1:]))
        else:
            raise ValueError(f"Unsupported code index: {cid}")

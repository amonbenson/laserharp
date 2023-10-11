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
            #self._serial.timeout = 0.001

    def send(self, event: MidiEvent):
        # only short messages are supported
        message_data = event.message.bytes()
        if len(message_data) != 3:
            raise ValueError(f"Unsupported MIDI event: {event}")

        # construct and send the packet
        cn_cid = np.uint8(event.cable_number << 4 | message_data[0] >> 4)

        data = bytearray([cn_cid, *message_data])
        #print(f"RPI -> STM: {data.hex(' ')}")
        self._serial.write(data)

    def read(self) -> MidiEvent:
        # read the cable number and code index
        cn_cid = self._serial.read(1)[0]
        cn = cn_cid >> 4
        cid = cn_cid & 0x0F

        if not (cid >= 0x8 and cid <= 0xE):
            raise ValueError(f"Unsupported code index: {cid}")

        # read the remaining packet
        data = self._serial.read(3)
        #print(f"STM -> RPI: {cn_cid :02x} {data.hex(' ')}")
        return MidiEvent(cn, mido.Message.from_bytes(data))

    def read_all(self) -> list[MidiEvent]:
        # this code is faster than reading one byte at a time, but quite ugly.
        # should be refactored asap.

        events = []

        # read all available data
        n_packets = self._serial.in_waiting & ~0x03 # round down to nearest multiple of 4
        data = self._serial.read(n_packets)
        if len(data) == 0:
            return []

        # parse the data into packets
        i = 0
        while i < len(data):
            cn_cid = data[i]
            cn = cn_cid >> 4
            cid = cn_cid & 0x0F
            i += 1

            if not (cid >= 0x8 and cid <= 0xE):
                continue

            packet_data = data[i:i+3]
            i += 3

            #print(f"STM -> RPI: {cn_cid :02x} {packet_data.hex(' ')}")
            events.append(MidiEvent(cn, mido.Message.from_bytes(packet_data)))

        return events

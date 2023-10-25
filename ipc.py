import os
import logging
from enum import Enum
import serial
import mido
import numpy as np
from .midi import MidiEvent


class IPCController():
    BYTE_TIMEOUT = 0.01

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

    def stop(self):
        self._serial.close()

    def send(self, event: MidiEvent, timeout=None):
        # only short messages are supported
        message_data = event.message.bytes()
        if len(message_data) != 3:
            raise ValueError(f"Unsupported MIDI event: {event}")

        # construct and send the packet
        cn_cid = np.uint8(event.cable_number << 4 | message_data[0] >> 4)

        data = bytearray([cn_cid, *message_data])
        logging.debug(f"RPI -> STM: {data.hex(' ')}")

        self._serial.write_timeout = timeout
        self._serial.write(data)
        self._serial.flush()

    def read(self, timeout=None) -> MidiEvent:
        # read the cable number and code index
        self._serial.timeout = timeout
        data0 = self._serial.read(1)
        if len(data0) == 0:
            return None

        cn_cid = data0[0]
        cn = cn_cid >> 4
        cid = cn_cid & 0x0F

        if not (cid >= 0x8 and cid <= 0xE):
            raise ValueError(f"Unsupported code index: {cid}")

        # read the remaining packet
        self._serial.timeout = self.BYTE_TIMEOUT * 3
        data = self._serial.read(3)
        if len(data) != 3:
            raise ValueError(f"Read timeout")

        logging.debug(f"STM -> RPI: {cn_cid :02x} {data.hex(' ')}")
        return MidiEvent(cn, mido.Message.from_bytes(data))

import logging
import serial
import mido
import numpy as np
from .midi import MidiEvent
from .events import EventEmitter


class IPCController(EventEmitter):
    BYTE_TIMEOUT = 0.01

    def __init__(self, config: dict, custom_serial=None):
        super().__init__()

        self.config = config

        if custom_serial is not None:
            self._serial = custom_serial
        else:
            self._serial = serial.Serial(
                port=config["port"],
                baudrate=config["baudrate"],
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
            )

        self._cable_map = self.config["cables"]
        self._cn_map = {cn: cable for cable, cn in self._cable_map.items()}

    def start(self):
        if not self._serial.is_open:
            self._serial.open()

    def stop(self):
        self._serial.close()

    def send(self, event: MidiEvent, timeout=None):
        # only short messages are supported
        message_data = event.message.bytes()
        if len(message_data) != 3:
            raise ValueError(f"Unsupported MIDI event: {event}")

        if event.cable not in self._cable_map:
            raise ValueError(f"Unsupported cable: {event.cable}")

        # construct and send the packet
        cn = self._cable_map[event.cable]
        cn_cid = np.uint8(cn << 4 | message_data[0] >> 4)

        data = bytearray([cn_cid, *message_data])
        logging.debug(f"RPI -> STM: {data.hex(' ')}")

        self._serial.write_timeout = timeout
        self._serial.write(data)
        self._serial.flush()

    def read(self, timeout=None) -> MidiEvent:
        # read the cable number and code index
        self._serial.timeout = timeout
        try:
            data0 = self._serial.read(1)
        except KeyboardInterrupt:
            return None
        if len(data0) == 0:
            return None

        cn_cid = data0[0]
        cn = cn_cid >> 4
        cid = cn_cid & 0x0F

        if cn not in self._cn_map:
            raise ValueError(f"Unsupported cable number: {cn}")
        cable = self._cn_map[cn]

        if not (cid >= 0x8 and cid <= 0xE):
            raise ValueError(f"Unsupported code index: {cid}")

        # read the remaining packet
        self._serial.timeout = self.BYTE_TIMEOUT * 3
        data = self._serial.read(3)
        if len(data) != 3:
            raise ValueError("Read timeout")

        logging.debug(f"STM -> RPI: {cn_cid :02x} {data.hex(' ')}")
        return MidiEvent(cable, mido.Message.from_bytes(data))

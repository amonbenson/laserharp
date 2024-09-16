import logging
import serial
import mido
from .midi import MidiEvent
from .events import EventEmitter


class DinMidi(EventEmitter):
    BYTE_TIMEOUT = 0.01

    def __init__(self, config: dict):
        super().__init__()

        self.config = config

        self._serial = serial.Serial(
            port=config["port"],
            baudrate=config["baudrate"],
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
        )

    def start(self):
        if not self._serial.is_open:
            self._serial.open()

    def stop(self):
        self._serial.close()

    def send(self, event: MidiEvent, timeout=None):
        data = bytearray(event.message.bytes())
        logging.debug(f"RPI -> DIN: {data.hex(' ')}")

        self._serial.write_timeout = timeout
        self._serial.write(data)
        self._serial.flush()

    def read(self, timeout=None) -> MidiEvent:
        self._serial.timeout = timeout

        try:
            data0 = self._serial.read(1)
        except KeyboardInterrupt:
            return None
        if len(data0) != 1:
            return None

        status = data0[0]
        if status < 0x80 or status >= 0xF0:
            logging.warning(f"Invalid/Unsupported status byte: {status}")
            return None

        # construct a short message
        self._serial.timeout = self.BYTE_TIMEOUT * 3
        data = self._serial.read(2)
        if len(data) != 2:
            logging.warning("Timeout while reading MIDI message")
            return None

        logging.debug(f"DIN -> RPI: {status :02x} {data.hex(' ')}")
        return MidiEvent(0, mido.Message.from_bytes([status, *data]))

import mido
from enum import Enum
from dataclasses import dataclass


@dataclass
class MidiEvent:
    cable_number: int
    message: mido.Message

    def __init__(self, cable_number: int, message_type: str, **kwargs):
        self.cable_number = cable_number
        self.message = mido.Message(message_type, **kwargs)

    def __repr__(self):
        return f"MidiEvent(cable_number={self.cable_number :02x}, message={bytearray(self.message.bytes()).hex(' ')})"

import mido
from enum import Enum
from dataclasses import dataclass


@dataclass
class MidiEvent:
    cable_number: int
    message: mido.Message

    def __repr__(self):
        return f"MidiEvent(cable_number={self.cable_number :.02x}, message={self.message.bytes().hex(' ')})"

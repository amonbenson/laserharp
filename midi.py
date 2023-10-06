import mido
from enum import Enum
from dataclasses import dataclass


class MidiInterface(Enum):
    DIN = 0x00
    USB = 0x01
    BLE = 0x02

@dataclass
class MidiEvent:
    interface: MidiInterface
    message: mido.Message

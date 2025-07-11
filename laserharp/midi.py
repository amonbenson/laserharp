from typing import Union
import mido


class MidiEvent:
    def __init__(self, cable: int, message_type: Union[str, mido.Message], *args, **kwargs):
        self.cable = int(cable)

        if isinstance(message_type, mido.Message):
            self.message = message_type
        else:
            self.message = mido.Message(message_type, *args, **kwargs)

    def __eq__(self, other):
        return self.cable == other.cable and self.message == other.message

    def __repr__(self):
        return f"MidiEvent(cable={self.cable}, message={bytearray(self.message.bytes()).hex(' ')})"

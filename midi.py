import mido


class MidiEvent:
    def __init__(self, cable_number: int, message_type: str, **kwargs):
        self.cable_number = cable_number

        if isinstance(message_type, mido.Message):
            self.message = message_type
        else:
            self.message = mido.Message(message_type, **kwargs)

    def __eq__(self, other):
        return self.cable_number == other.cable_number and self.message == other.message

    def __repr__(self):
        return f"MidiEvent(cable_number={self.cable_number :02x}, message={bytearray(self.message.bytes()).hex(' ')})"

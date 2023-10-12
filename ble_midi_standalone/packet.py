from dataclasses import dataclass
import time
import mido


@dataclass
class BleMidiPacket:
    timestamp: int
    messages: list[mido.Message]

    def __repr__(self):
        return f"BleMidiPacket({self.timestamp}, {self.data})"

    def bytes(self):
        # construct the header as follows:
        # header[0]: | 1 | r |  timestampHigh |
        # header[1]: | 1 |    timestampLow    |
        header = bytearray(2)
        header[0] = 0x80 | (self.timestamp >> 7) & 0x3F
        header[1] = self.timestamp & 0x7F

        # concatenate all messages
        data = bytearray()
        for message in self.messages:
            data.extend(message.bytes())

        return header + data

    @staticmethod
    def from_bytes(data: bytearray):
        # parse the header
        timestamp = ((data[0] & 0x3F) << 7) | (data[1] & 0x7F)

        # parse all messages
        messages = mido.parse_all(data[2:])

        return BleMidiPacket(timestamp, messages)

    @staticmethod
    def from_message(message: mido.Message):
        return BleMidiPacket(int(time.time()), [message])

    @staticmethod
    def from_messages(messages: list[mido.Message]):
        return BleMidiPacket(int(time.time()), messages)

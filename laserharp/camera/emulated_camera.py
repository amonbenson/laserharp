import time
import trio
import logging
import numpy as np
from ..mqtt import get_mqtt


logger = logging.getLogger("lh:camera")


class EmulatedCamera:
    TOPIC = "lh/emulator/camera/stream"

    def __init__(self):
        self._frame_send_channel, self._frame_receive_channel = trio.open_memory_channel(0)

    @staticmethod
    async def _receive_mqtt(frame_send_channel: trio.MemorySendChannel):
        sub = get_mqtt().subscribe(EmulatedCamera.TOPIC)

        try:
            async with sub.receive_channel:
                async for message in sub.receive_channel:
                    frame = message
                    await frame_send_channel.send(frame)
        except trio.Cancelled:
            get_mqtt().unsubscribe(sub)

    async def run(self, nursery: trio.Nursery):
        nursery.start_soon(self._receive_mqtt, self._frame_send_channel)

    def frame_receive_channel(self) -> trio.MemoryReceiveChannel:
        return self._frame_receive_channel.clone()

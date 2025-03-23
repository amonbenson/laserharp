from itertools import count
import trio
from ..mqtt_component import SUBSCRIBE_ONLY_ACCESS
from .base import BaseCamera


class EmulatedCamera(BaseCamera):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.emulator_stream = self.add_endpoint(
            "emulator_stream",
            topic="lh/emulator/camera/stream",
            encoding="raw",
            qos=0,
            retain=False,
            access=SUBSCRIBE_ONLY_ACCESS,
        )
        self.add_worker(self._handle_emulator_stream)

    async def _handle_emulator_stream(self):
        while True:
            frame = await self.emulator_stream.wait_change()
            await self._frame_send_channel.send(frame)

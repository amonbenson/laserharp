from itertools import count
import trio
import base64
import cv2
import numpy as np
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
            # decode stream frame
            frame_b64 = await self.emulator_stream.wait_change()
            frame_jpg = np.frombuffer(base64.b64decode(frame_b64), dtype=np.uint8)
            if len(frame_jpg) == 0:
                continue

            frame = cv2.imdecode(frame_jpg, cv2.IMREAD_UNCHANGED)

            # send to the receiver channel
            await self._frame_send_channel.send(frame)

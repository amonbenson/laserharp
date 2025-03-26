from abc import ABC
import trio
import numpy as np
from ..mqtt_component import ConfigurableComponent, PUBLISH_ONLY_ACCESS


class BaseCamera(ConfigurableComponent, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_config(
            """
            type: object
            properties:
                width:
                    title: "Width"
                    type: integer
                    minimum: 240
                    maximum: 1440
                    default: 480
                height:
                    title: "Height"
                    type: integer
                    minimum: 160
                    maximum: 1080
                    default: 320
            required:
                - width
                - height
            """
        )

        self.stream = self.add_endpoint("stream", encoding="raw", qos=0, retain=False, access=PUBLISH_ONLY_ACCESS)
        self._frame_send_channel, self._frame_receive_channel = trio.open_memory_channel(0)

    async def _broadcast_stream(self):
        async for frame in self._frame_receive_channel.clone():
            self.stream.value = frame

    async def capture(self) -> np.ndarray:
        return await self._frame_receive_channel.receive()

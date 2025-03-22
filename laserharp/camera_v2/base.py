from abc import ABC
import trio
from ..mqtt_component import ConfigurableComponent, PUBLISH_ONLY_ACCESS


class BaseCamera(ConfigurableComponent, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_config(
            {
                "width": 480,
                "height": 320,
            },
            {
                "type": "object",
                "properties": {
                    "width": {"type": "number", "minimum": 240, "maximum": 1440, "default": "480"},
                    "height": {"type": "number", "minimum": 160, "maximum": 1080},
                },
                "required": ["width", "height"],
            },
        )

        self.stream = self.add_endpoint("stream", encoding="raw", retain=False, access=PUBLISH_ONLY_ACCESS)
        self._frame_send_channel, self._frame_receive_channel = trio.open_memory_channel(0)

    def receive_frame_channel(self):
        return self._frame_receive_channel

    async def _broadcast_stream(self):
        async for frame in self.receive_frame_channel().clone():
            self.stream.value = frame

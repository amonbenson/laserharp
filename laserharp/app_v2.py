from itertools import count
import trio
from .mqtt_component import MQTTRootComponent, ConfigurableComponent, PUBLISH_ONLY_ACCESS


class Camera(ConfigurableComponent):
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

        self.stream = self.add_pubsub("stream", encoding="raw", access=PUBLISH_ONLY_ACCESS)
        self.add_worker(self._test_pubsub)

    async def handle_config_change(self, config: dict):
        print("CONFIG!", config)

    async def _test_pubsub(self):
        for i in count():
            await trio.sleep(1.0)
            # self.fov_x.value = i
            # self.fov_y.value = -i
            self.stream.value = b"test123"


class App(MQTTRootComponent):
    def __init__(self):
        super().__init__("lh")

        self.add_child("camera", Camera)

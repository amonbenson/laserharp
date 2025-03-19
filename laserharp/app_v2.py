from itertools import count
import trio
from .component_v2 import RootComponent
from .mqtt import MQTTClient, PubSub
from .mqtt_component import MQTTRootComponent, MQTTComponent
from .settings_v2 import Settings


class Camera(MQTTComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_worker(self._test_pubsub)
        self.add_worker(self._test_change_handler)

        self.test: PubSub[int]
        self.test2: PubSub[int]

    async def setup(self):
        self.test = await self.pubsub("test")
        self.test2 = await self.pubsub("test2")

    async def _test_change_handler(self):
        while True:
            await PubSub.wait_any_change(self.test, self.test2)
            print("UPDATE!", self.test.value, self.test2.value)

    async def _test_pubsub(self):
        for i in count():
            await trio.sleep(1.0)
            self.test.value = i
            self.test2.value = -i


class App(MQTTRootComponent):
    def __init__(self):
        super().__init__("lh")

        self.add_child("camera", Camera)

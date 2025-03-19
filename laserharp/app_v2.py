from itertools import count
import trio
from .mqtt_component import MQTTRootComponent, MQTTComponent, PubSubComponent
from .settings_v2 import Settings


class Camera(MQTTComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_worker(self._test_pubsub)
        self.add_worker(self._test_change_handler)

        self.test: PubSubComponent[int] = self.add_pubsub("test")
        self.test2: PubSubComponent[int] = self.add_pubsub("test2")

    async def _test_change_handler(self):
        while True:
            await PubSubComponent.wait_any_change(self.test, self.test2)
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

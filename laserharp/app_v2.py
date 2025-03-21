from itertools import count
import trio
from .mqtt_component import MQTTRootComponent, MQTTBaseComponent, PUBLISH_ONLY_ACCESS


class Camera(MQTTBaseComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_worker(self._test_pubsub)
        self.add_worker(self._test_change_handler)

        self.stream = self.add_pubsub("stream", type="raw", access=PUBLISH_ONLY_ACCESS)

    async def _test_change_handler(self):
        while True:
            # await PubSubComponent.wait_any_change(self.fov_x, self.fov_y)
            # print("UPDATE!", self.fov_x.value, self.fov_y.value)

            # await PubSubComponent.wait_any_change(self.stream)
            # print("STREAM UPDATE", self.stream.value)
            await trio.sleep(1)

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

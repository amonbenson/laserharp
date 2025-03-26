from itertools import count
import trio
from .component_v2 import Component
from .mqtt import MQTTClient
from .camera_v2 import Camera


class App(Component):
    def __init__(self):
        super().__init__("lh")

        self.add_global_child("mqtt", MQTTClient)
        self.camera = self.add_child("camera", Camera)

        self.add_worker(self._process)

    async def _process(self):
        while True:
            # get camera frame
            frame = await self.camera.capture()
            print("capture", frame.shape)

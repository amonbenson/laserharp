from itertools import count
import trio
from .mqtt_component import TopicComponent
from .camera_v2 import Camera


class App(TopicComponent):
    def __init__(self):
        super().__init__("lh")

        self.camera = self.add_child("camera", Camera)

        self.add_worker(self._process)

    async def _process(self):
        while True:
            # get camera frame
            frame = await self.camera.capture()
            print("capture", frame)

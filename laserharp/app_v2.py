from itertools import count
import trio
from .mqtt_component import MQTTRootComponent
from .camera_v2 import Camera


class App(MQTTRootComponent):
    def __init__(self):
        super().__init__("lh")

        self.add_child("camera", Camera)

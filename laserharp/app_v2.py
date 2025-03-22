from itertools import count
import trio
from .mqtt_component import TopicComponent
from .camera_v2 import Camera


class App(TopicComponent):
    def __init__(self):
        super().__init__("lh")

        self.add_child("camera", Camera)

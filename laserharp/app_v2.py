from .component_v2 import RootComponent
from .mqtt import MQTTClient


class App(RootComponent):
    def __init__(self):
        super().__init__("laserharp")

    def setup(self):
        self.add_child("mqtt", MQTTClient)

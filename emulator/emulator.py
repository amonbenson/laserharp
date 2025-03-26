from laserharp.component_v2 import Component
from laserharp.mqtt import MQTTClient
from .camera import Camera
from .stm import STMBoard


class _EmulatorImpl(Component):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_global_child("mqtt", MQTTClient)

        self.camera = self.add_child("camera", Camera)
        self.stm = self.add_child("stm", STMBoard)


class Emulator(Component):
    def __init__(self):
        # wrap the actual emulator class to get the correct topic naming (lh/emulator)
        super().__init__("lh")
        self.add_child("emulator", _EmulatorImpl)

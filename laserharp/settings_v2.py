from .component_v2 import Component
from .mqtt import MQTTClient


class Settings(Component):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._mqtt: MQTTClient = self.get_global_singleton("mqtt")

    async def setup(self):
        # test = await self._mqtt.read("lh/test")
        # print(f"SETTINGS GOT TEST VALUE: {test}")

        pass

import trio
from .component_v2 import RootComponent
from .mqtt import MQTTClient


MQTT: MQTTClient = None


class App(RootComponent):
    def __init__(self):
        global MQTT  # pylint: disable=global-statement

        super().__init__("laserharp")

        MQTT = self.add_child("mqtt", MQTTClient)
        self.add_worker("test_pubsub", self._test_pubsub)

        self.test = MQTT.pubsub("lh/test")

    async def _test_pubsub(self):
        await trio.sleep(1.0)

        self.test.value = {"hello": "world"}

from itertools import count
import trio
from .component_v2 import RootComponent
from .mqtt import MQTTClient, PubSub


MQTT: MQTTClient = None


class App(RootComponent):
    def __init__(self):
        global MQTT  # pylint: disable=global-statement

        super().__init__("laserharp")

        MQTT = self.add_child("mqtt", MQTTClient)
        self.add_worker(self._test_pubsub)
        self.add_worker(self._test_change_handler)

        self.test: PubSub[int] = MQTT.pubsub("lh/test")
        self.test2: PubSub[int] = MQTT.pubsub("lh/test2")

    async def _test_change_handler(self):
        while True:
            await PubSub.wait_any_change(self.test, self.test2)
            print("UPDATE!", self.test.value, self.test2.value)

    async def _test_pubsub(self):
        for i in count():
            await trio.sleep(1.0)
            self.test.value = i
            self.test2.value = -i

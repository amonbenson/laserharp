from .component_v2 import RootComponent, Component
from .mqtt import MQTTClient, Subscription, PubSub, PayloadType, PayloadEncoding


class MQTTRootComponent(RootComponent):
    def __init__(self, name):
        super().__init__(name)

        self._mqtt = self.add_global_child("mqtt", MQTTClient)


class MQTTComponent(Component):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._mqtt: MQTTClient = self.get_global_child("mqtt")
        self._root_topic = self._full_name.replace(":", "/")

    async def subscribe[T: PayloadType](self, topic: str, **kwargs) -> Subscription[T]:
        return await self._mqtt.subscribe(f"{self._root_topic}/{topic}", **kwargs)

    async def unsubscribe(self, sub: Subscription):
        await self._mqtt.unsubscribe(sub)

    async def publish[T: PayloadType](self, topic: str, payload: T, **kwargs):
        await self._mqtt.publish(f"{self._root_topic}/{topic}", payload, **kwargs)

    async def read[T: PayloadType](self, topic: str, **kwargs) -> T:
        return await self._mqtt.read(f"{self._root_topic}/{topic}", **kwargs)

    async def pubsub[T: PayloadType](self, topic: str, **kwargs) -> PubSub[T]:
        return await self._mqtt.pubsub(f"{self._root_topic}/{topic}", **kwargs)

    async def setup(self):
        pass

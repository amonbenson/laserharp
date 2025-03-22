from typing import Optional, TYPE_CHECKING, overload, Literal
from ..component_v2 import RootComponent, Component
from ..mqtt import MQTTClient, Subscription, PayloadType

# avoiding circular imports
if TYPE_CHECKING:
    from .endpoint import EndpointComponent, RawEndpointComponent


class MQTTRootComponent(RootComponent):
    def __init__(self, name):
        super().__init__(name)

        self._mqtt = self.add_global_child("mqtt", MQTTClient)

    @overload
    def add_endpoint[T: PayloadType](self, name: str, **kwargs) -> "EndpointComponent[T]": ...


class TopicComponent(Component):
    def __init__(self, name: str, parent: Component, *, topic: Optional[str] = None):
        super().__init__(name, parent)

        self._mqtt: MQTTClient = self.get_global_child("mqtt")
        self._topic = topic if topic is not None else self._full_name.replace(":", "/")

    async def subscribe[T: PayloadType](self, **kwargs) -> Subscription[T]:
        return await self._mqtt.subscribe(self._topic, **kwargs)

    async def unsubscribe(self, sub: Subscription):
        await self._mqtt.unsubscribe(sub)

    async def publish[T: PayloadType](self, payload: T, **kwargs):
        await self._mqtt.publish(self._topic, payload, **kwargs)

    async def read[T: PayloadType](self, **kwargs) -> T:
        return await self._mqtt.read(self._topic, **kwargs)

    @overload
    def add_endpoint[T: PayloadType](self, name: str, **kwargs) -> "EndpointComponent[T]": ...

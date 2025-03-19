from typing import Optional, TYPE_CHECKING, overload
from ..component_v2 import RootComponent, Component
from ..mqtt import MQTTClient, Subscription, PayloadType

# avoiding circular imports
if TYPE_CHECKING:
    from .pubsub import PubSubComponent
    from .setting import SettingComponent


class MQTTRootComponent(RootComponent):
    def __init__(self, name):
        super().__init__(name)

        self._mqtt = self.add_global_child("mqtt", MQTTClient)


class MQTTBaseComponent(Component):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._mqtt: MQTTClient = self.get_global_child("mqtt")
        self._topic = self._full_name.replace(":", "/")

    def full_topic(self, endpoint: Optional[str] = None):
        if endpoint is None:
            return self._topic

        return f"{self._topic}/{endpoint}"

    async def subscribe[T: PayloadType](self, endpoint: Optional[str], **kwargs) -> Subscription[T]:
        return await self._mqtt.subscribe(self.full_topic(endpoint), **kwargs)

    async def unsubscribe(self, sub: Subscription):
        await self._mqtt.unsubscribe(sub)

    async def publish[T: PayloadType](self, endpoint: Optional[str], payload: T, **kwargs):
        await self._mqtt.publish(self.full_topic(endpoint), payload, **kwargs)

    async def read[T: PayloadType](self, endpoint: Optional[str], **kwargs) -> T:
        return await self._mqtt.read(self.full_topic(endpoint), **kwargs)

    @overload
    def add_pubsub[T: PayloadType](self, name: str, **kwargs) -> "PubSubComponent[T]": ...

    @overload
    def add_setting[T: PayloadType](self, name: str, **kwargs) -> "SettingComponent[T]": ...

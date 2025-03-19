from .base import MQTTBaseComponent
from .pubsub import PubSubComponent
from ..mqtt import PayloadType


def add_pubsub[T: PayloadType](self: MQTTBaseComponent, name: str, **kwargs) -> PubSubComponent[T]:
    return self.add_child(name, PubSubComponent, **kwargs)


MQTTBaseComponent.add_pubsub = add_pubsub

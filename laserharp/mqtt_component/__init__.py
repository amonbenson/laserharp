from typing import Optional
from ..mqtt import PayloadType, JsonPayloadType
from .base import MQTTRootComponent, MQTTBaseComponent
from .pubsub import PubSubComponent
from .configurable import ConfigurableComponent


MQTTBaseComponent.add_pubsub = lambda self, name, **kwargs: self.add_child(name, PubSubComponent, **kwargs)


FULL_ACCESS = PubSubComponent.Access.full()
PUBLISH_ONLY_ACCESS = PubSubComponent.Access(client="w", broker="r")
SUBSCRIBE_ONLY_ACCESS = PubSubComponent.Access(client="r", broker="w")

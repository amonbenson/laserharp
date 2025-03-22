from typing import Optional
from ..mqtt import PayloadType, JsonPayloadType
from .base import MQTTRootComponent, TopicComponent
from .endpoint import EndpointComponent
from .configurable import ConfigurableComponent


MQTTRootComponent.add_endpoint = lambda self, name, **kwargs: self.add_child(name, EndpointComponent, **kwargs)
TopicComponent.add_endpoint = lambda self, name, **kwargs: self.add_child(name, EndpointComponent, **kwargs)


FULL_ACCESS = EndpointComponent.Access.full()
PUBLISH_ONLY_ACCESS = EndpointComponent.Access(client="w", broker="r")
SUBSCRIBE_ONLY_ACCESS = EndpointComponent.Access(client="r", broker="w")

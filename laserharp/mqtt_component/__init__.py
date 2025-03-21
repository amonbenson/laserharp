from typing import Optional
from ..mqtt import PayloadType, JsonPayloadType
from .base import MQTTRootComponent, MQTTBaseComponent
from .pubsub import PubSubComponent, RawPubSubComponent


def add_pubsub[T: PayloadType](self: MQTTBaseComponent, name: str, type: Optional[str] = None, **kwargs) -> PubSubComponent[T]:
    if type is None:
        # create a custom pubsub child
        return self.add_child(name, PubSubComponent, **kwargs)

    # encoding and validator must not be set explicitly (only supported on custom pubsub components)
    if "encoding" in kwargs or "validator" in kwargs:
        raise ValueError("Cannot combine parameter 'type' with 'encoding' or 'validator'")

    match type:
        case "raw":
            return self.add_child(name, RawPubSubComponent, **kwargs)
        case _:
            raise ValueError(f"Invalid type: {type}")



MQTTBaseComponent.add_pubsub = add_pubsub


FULL_ACCESS = PubSubComponent.Access.full()
PUBLISH_ONLY_ACCESS = PubSubComponent.Access(client="w", broker="r")
SUBSCRIBE_ONLY_ACCESS = PubSubComponent.Access(client="r", broker="w")

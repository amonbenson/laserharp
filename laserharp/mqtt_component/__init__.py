from ..mqtt import PayloadType, JsonPayloadType
from .base import MQTTRootComponent, MQTTBaseComponent
from .pubsub import PubSubComponent
from .setting import SettingComponent


def add_pubsub[T: PayloadType](self: MQTTBaseComponent, name: str, **kwargs) -> PubSubComponent[T]:
    return self.add_child(name, PubSubComponent, **kwargs)


def add_setting[T: JsonPayloadType](self: MQTTBaseComponent, name: str, **kwargs) -> SettingComponent[T]:
    return self.add_child(name, SettingComponent, **kwargs)


MQTTBaseComponent.add_pubsub = add_pubsub
MQTTBaseComponent.add_setting = add_setting

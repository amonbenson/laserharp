from ..mqtt import JsonPayloadType
from .pubsub import PubSubComponent


class SettingComponent[T: JsonPayloadType](PubSubComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

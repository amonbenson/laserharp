import os
import threading
import paho.mqtt.client as mqtt
from perci import ReactiveDictNode
from .component import Component

MQTT_BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")


class MQTT(Component):
    def __init__(self, name: str, global_state: ReactiveDictNode):
        super().__init__(name, global_state)
        self._connect_lock = threading.Lock()

        self._mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._mqtt.on_connect = self._on_connect
        self._mqtt.on_message = self._on_message

    def _on_connect(self):
        pass

    def _on_message(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

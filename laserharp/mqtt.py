import os
import trio
import json
from collections import defaultdict
from typing import Any, Optional
from dataclasses import dataclass
import paho.mqtt.client as mqtt
from trio_paho_mqtt import AsyncClient


MQTT_HOST = os.getenv("LH_MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("LH_MQTT_PORT", 1883))


@dataclass
class Subscription:
    topic: str
    send_channel: trio.MemorySendChannel
    receive_channel: trio.MemoryReceiveChannel
    parse_json: bool

    async def __aiter__(self):
        async with self.receive_channel:
            async for payload in self.chanreceive_channelnel:
                if self.parse_json:
                    payload = json.loads(payload)

                yield payload

class MQTTClient:
    def __init__(self):
        self._running = False
        self._subscriptions: dict[str, list[Subscription]] = {}

    @property
    def running(self):
        return self._running

    async def _handle_messages(self, client: AsyncClient):
        async for message in client.messages():
            for topic_subs in self._subscriptions.values():
                for sub in topic_subs:
                    if mqtt.topic_matches_sub(sub.topic, message.topic):
                        await sub.send_channel.send(message)

    async def run(self, nursery: trio.Nursery):
        self._sync_client = mqtt.Client()
        self._client = AsyncClient(self._sync_client, nursery)
        self._client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        self._running = True

        nursery.start_soon(self._handle_messages, self._client)

    def subscribe(self, topic, qos = 0, options = None, properties = None, parse_json=True):
        if not self.running:
            raise ValueError("MQTT client is not running")

        send_channel, receive_channel = trio.open_memory_channel(0)
        sub = Subscription(topic, send_channel, receive_channel, parse_json)

        # subscribe to the mqtt topic if this is the first subscriber
        if topic not in self._subscriptions:
            self._client.subscribe(topic, qos, options, properties)
            self._subscriptions[topic] = []

        # store the subscription
        self._subscriptions[topic].append(sub)
        return sub

    def unsubscribe(self, sub: Subscription, properties = None):
        if not self.running:
            raise ValueError("MQTT client is not running")

        # find and remove the subscription
        topic_subs = self._subscriptions[sub.topic]
        topic_subs.remove(sub)

        # remove the mqtt subscription, if no more subscribers are left
        if not topic_subs:
            self._client.unsubscribe(sub.topic, properties)
            del self._subscriptions[sub.topic]

    def publish(self, topic, payload):
        if not self.running:
            raise ValueError("MQTT client is not running")

        # serialize json
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload)

        self._client.publish(topic, payload)

_global_mqtt_client = MQTTClient()
def get_mqtt():
    return _global_mqtt_client

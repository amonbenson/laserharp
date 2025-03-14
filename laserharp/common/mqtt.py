import os
import trio
import json
import logging
from collections import defaultdict
from typing import Any, Optional
from dataclasses import dataclass
import paho.mqtt.client as mqtt
from trio_paho_mqtt import AsyncClient


MQTT_HOST = os.getenv("LH_MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("LH_MQTT_PORT", 1883))

logger = logging.getLogger("lh:mqtt")


@dataclass
class Subscription:
    topic: str
    send_channel: trio.MemorySendChannel
    receive_channel: trio.MemoryReceiveChannel
    raw: bool

    async def __aiter__(self):
        async with self.receive_channel:
            async for payload in self.receive_channel:
                try:
                    if not self.raw:
                        payload = json.loads(payload)
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode payload: {payload}")
                    return

                yield payload

class MQTTClient:
    def __init__(self):
        self._subscriptions: dict[str, list[Subscription]] = {}
        self._ready_event = trio.Event()

    async def _handle_messages(self, client: AsyncClient):
        self._ready_event.set()

        async for message in client.messages():
            for topic_subs in self._subscriptions.values():
                for sub in topic_subs:
                    if mqtt.topic_matches_sub(sub.topic, message.topic):
                        await sub.send_channel.send(message.payload)

    async def run(self):
        try:
            async with trio.open_nursery() as nursery:
                logger.info("Connecting to broker")
                self._sync_client = mqtt.Client()
                self._client = AsyncClient(self._sync_client, nursery)
                self._client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)

                nursery.start_soon(self._handle_messages, self._client)
        except* trio.Cancelled:
            logger.info("Disconnecting from broker")
            self._client.disconnect()

    async def wait_ready(self):
        await self._ready_event.wait()

    async def subscribe(self, topic, qos = 0, options = None, properties = None, raw=False):
        await self._ready_event.wait()

        send_channel, receive_channel = trio.open_memory_channel(0)
        sub = Subscription(topic, send_channel, receive_channel, raw)

        # subscribe to the mqtt topic if this is the first subscriber
        if topic not in self._subscriptions:
            logger.debug(f"SUB {topic}")
            self._client.subscribe(topic, qos, options, properties)
            self._subscriptions[topic] = []

        # store the subscription
        self._subscriptions[topic].append(sub)
        return sub

    async def unsubscribe(self, sub: Subscription, properties = None):
        await self._ready_event.wait()

        # find and remove the subscription
        topic_subs = self._subscriptions[sub.topic]
        topic_subs.remove(sub)

        # remove the mqtt subscription, if no more subscribers are left
        if not topic_subs:
            logger.debug(f"UNSUB {sub.topic}")
            self._client.unsubscribe(sub.topic, properties)
            del self._subscriptions[sub.topic]

    async def publish(self, topic, payload, qos=0, retain=False, properties=None):
        await self._ready_event.wait()

        # serialize json
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload)

        logger.debug(f"PUB {topic}: {payload}")
        self._client.publish(topic, payload, qos, retain, properties)

MQTT = MQTTClient()

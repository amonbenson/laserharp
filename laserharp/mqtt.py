import socket
import logging
import traceback
from typing import Optional, Any, Self
import json
import trio
import paho.mqtt.client as mqtt
from .component_v2 import Component
from .env import getenv


MQTT_HOST = getenv("LH_MQTT_HOST", type=str, default="localhost")
MQTT_PORT = getenv("LH_MQTT_PORT", type=int, default=1883)


PayloadType = bytes | dict | list


class Subscription:
    VALID_ENCODINGS = ("raw", "str", "json")

    def __init__(self, client: "MQTTClient", topic: str, *, encoding: str = "json", message_buffer_size: int = 16):
        self._client = client
        self._topic = topic
        self._encoding = encoding
        self._send_channel, self._receive_channel = trio.open_memory_channel(message_buffer_size)

        if self._encoding not in self.VALID_ENCODINGS:
            raise ValueError(f"encoding must be one of {self.VALID_ENCODINGS} but was {self._encoding}")

    @property
    def topic(self):
        return self._topic

    @property
    def encoding(self):
        return self._encoding

    def put(self, payload: bytes):
        try:
            self._send_channel.send_nowait(payload)
        except trio.WouldBlock:
            logging.warning("Message buffer full. Consider increasing message_buffer_size")

            # discard an old message to fit the new message
            self._receive_channel.receive_nowait()
            self._send_channel.send_nowait(payload)

    def matches(self, topic: str):
        return mqtt.topic_matches_sub(self._topic, topic)

    async def receive(self) -> PayloadType:
        payload: bytes = await self._receive_channel.receive()
        self._client.set_read_event()

        match self._encoding:
            case "raw":
                return bytes(payload)
            case "str":
                return str(payload)
            case "json":
                try:
                    return json.loads(payload)
                except json.JSONDecodeError as e:
                    self._client.logger.error(f"Failed to decode JSON payload {e}")

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> PayloadType:
        try:
            return await self.receive()
        except trio.EndOfChannel:
            raise StopAsyncIteration from None


class PubSub:
    def __init__(self, client: "MQTTClient", topic: str, *, qos: int = 0, retain: bool = True, encoding: str = "json"):
        self._client = client
        self._logger = logging.getLogger(f"pubsub:{topic}")

        self._topic = topic
        self._qos = qos
        self._retain = retain
        self._encoding = encoding

        self._value = None
        self._client_update_event = trio.Event()
        self._broker_update_event = trio.Event()

        self._sub: Subscription = None

    async def _handle_receive(self):
        async for payload in self._sub:
            self._client.logger.debug(f"Got new value for {self._topic}")
            self._value = payload
            self._broker_update_event.set()

    async def _handle_send(self):
        while True:
            # wait for client updates, then publish the change
            await self._client_update_event.wait()
            self._client_update_event = trio.Event()

            await self._client.publish(self._topic, self._value, qos=self._qos, retain=self._retain)

    async def run(self):
        self._sub = await self._client.subscribe(self._topic, qos=self._qos, encoding=self._encoding, message_buffer_size=0)

        async with trio.open_nursery() as nursery:
            nursery.start_soon(self._handle_receive)
            nursery.start_soon(self._handle_send)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        # set the new value locally and mark the update
        self._value = value
        self._client_update_event.set()


class MQTTClient(Component):
    CONNECT_TIMEOUT = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._sock = self._client.socket()

        # internal events
        self._connect_event = trio.Event()
        self._large_write_event = trio.Event()
        self._should_read_event = trio.Event()
        self._should_read_event.set()

        # subscriber hash map
        self._subscriptions: dict[str, list[Subscription]] = {}

        # keep track of pubsub values
        self._pubsubs: list[PubSub] = []
        self._pubsub_nursery: trio.Nursery = None

        # register mqtt callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._client.on_socket_open = self._on_socket_open
        self._client.on_socket_close = self._on_socket_close
        self._client.on_socket_register_write = self._on_socket_register_write
        self._client.on_socket_unregister_write = self._on_socket_unregister_write

        # register mqtt loop tasks
        self.add_worker("read_loop", self._read_loop)
        self.add_worker("write_loop", self._write_loop)
        self.add_worker("misc_loop", self._misc_loop)
        self.add_worker("pubsub_loop", self._pubsub_loop)

    @property
    def logger(self):
        return self._logger

    def set_read_event(self):
        self._should_read_event.set()

    async def setup(self):
        self._logger.info(f"Connecting to {MQTT_HOST}:{MQTT_PORT}...")
        self._client.connect(MQTT_HOST, MQTT_PORT)

    async def teardown(self):
        self._logger.info("Disconnecting...")
        self._client.disconnect()

    async def _read_loop(self):
        while True:
            await self._should_read_event.wait()
            if self._sock.fileno() > 0:
                await trio.lowlevel.wait_readable(self._sock)
            else:
                await trio.sleep(0.1)
            self._client.loop_read()

    async def _write_loop(self):
        while True:
            await self._large_write_event.wait()
            if self._sock.fileno() > 0:
                await trio.lowlevel.wait_writable(self._sock)
            else:
                await trio.sleep(0.1)
            self._client.loop_write()

    async def _misc_loop(self):
        while self._client.loop_misc() == mqtt.MQTT_ERR_SUCCESS:
            await trio.sleep(1)

    async def _pubsub_loop(self):
        async with trio.open_nursery() as nursery:
            self._pubsub_nursery = nursery

            # start already created pubsub values
            for value in self._pubsubs:
                nursery.start_soon(value.run)

            # keep nursery alive if no pubsub values had been registered
            nursery.start_soon(trio.sleep_forever)

    def _on_connect(self, client, userdata, connect_flags, reason_code, properties):
        self._logger.info("Connected")
        self._connect_event.set()

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        self._logger.info("Disconnected")
        self._connect_event = trio.Event()

    def _on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        self._logger.debug(f"Received from {msg.topic}: {msg.payload.decode("utf-8")[:100]}")

        # forward the message to all matching subscribers
        for topic_subscriptions in self._subscriptions.values():
            for sub in topic_subscriptions:
                if sub.matches(msg.topic):
                    sub.put(msg.payload)

        # unset the read event
        self._should_read_event = trio.Event()

    def _on_socket_open(self, client, userdata, sock):
        self._logger.debug("Socket opened")
        self._sock = sock
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2048)

    def _on_socket_close(self, client, userdata, sock):
        self._logger.debug("Socket closed")

    def _on_socket_register_write(self, client, userdata, sock):
        self._logger.debug("Registered large write")
        # large write request - start write loop
        self._large_write_event.set()

    def _on_socket_unregister_write(self, client, userdata, sock):
        self._logger.debug("Unregistered large write")
        # finished large write - stop write loop
        self._large_write_event = trio.Event()

    def is_connected(self):
        return self._client.is_connected()

    async def wait_connected(self, timeout: Optional[float] = None):
        if self.is_connected:
            return

        with trio.fail_after(timeout or float("inf")):
            while not self.is_connected():
                self._connect_event.wait()

    def _register_subscription(self, sub: Subscription) -> bool:
        # insert the subscription object into the hash map
        topic_subscriptions = self._subscriptions.setdefault(sub.topic, [])
        topic_subscriptions.append(sub)

        # return true if this is the first subscriber
        is_first = len(topic_subscriptions) == 1
        return is_first

    def _unregister_subscription(self, sub: Subscription) -> bool:
        # check if the subscription object exists
        topic_subscriptions = self._subscriptions.get(sub.topic, [])
        if sub.topic not in topic_subscriptions:
            raise ValueError(f"Subscription {sub.topic} does not exist or was already unsubscribed")

        # remove the subscription object
        topic_subscriptions.remove(sub)

        # delete the whole list if no more topic subscriptions are left
        was_last = not topic_subscriptions
        if was_last:
            del self._subscriptions[sub.topic]
        return was_last

    async def subscribe(self, topic: str, *, qos: int = 0, **kwargs) -> Subscription:
        await self.wait_connected()

        self._logger.debug(f"Subscribing to {topic}")
        sub = Subscription(self, topic, **kwargs)
        is_first = self._register_subscription(sub)

        if is_first:
            self._client.subscribe(topic, qos)

        return sub

    async def unsubscribe(self, sub: Subscription):
        await self.wait_connected()

        self._logger.debug(f"unsubscribing from {sub.topic}")
        is_last = self._unregister_subscription(sub)

        if is_last:
            self._client.unsubscribe(sub.topic)

    async def publish(self, topic: str, payload: PayloadType, *, qos: int = 0, retain: bool = False):
        await self.wait_connected()

        if isinstance(payload, (list, dict)):
            # encode json
            payload = json.dumps(payload).encode("utf-8")
        elif isinstance(payload, (bytes, bytearray)):
            pass  # keep bytes as-is
        else:
            # stringify all other values
            payload = str(payload).encode("utf-8")

        self._logger.debug(f"Publishing to {topic}: {payload.decode("utf-8")[:100]}")

        self._client.publish(topic, payload, qos, retain)

    def pubsub(self, topic: str, **kwargs) -> PubSub:
        value = PubSub(self, topic, **kwargs)
        self._pubsubs.append(value)

        # run the pubsub value immediately if it was created while the component was already running
        if self.is_connected():
            self._pubsub_nursery.start_soon(value.run)

        return value

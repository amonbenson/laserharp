import socket
import logging
import traceback
from typing import Optional, Literal, Self, overload
import json
import trio
import paho.mqtt.client as mqtt
from .component_v2 import Component
from .env import getenv


MQTT_HOST = getenv("LH_MQTT_HOST", type=str, default="localhost")
MQTT_PORT = getenv("LH_MQTT_PORT", type=int, default=1883)


PayloadEncoding = Literal["raw"] | Literal["str"] | Literal["json"]

RawPayloadType = bytes | bytearray
StrPayloadType = str
JsonPayloadType = str | int | float | bool | None | list | dict
PayloadType = RawPayloadType | StrPayloadType | JsonPayloadType


@overload
def decode_payload(raw_payload: bytes, encoding: Literal["raw"]) -> RawPayloadType: ...


@overload
def decode_payload(raw_payload: bytes, encoding: Literal["str"]) -> StrPayloadType: ...


@overload
def decode_payload(raw_payload: bytes, encoding: Literal["json"]) -> JsonPayloadType: ...


def decode_payload(raw_payload: bytes, encoding: PayloadEncoding = "json") -> PayloadType:
    if not isinstance(raw_payload, bytes):
        raise ValueError(f"Expected raw_payload of type bytes, got {type(raw_payload)}")

    match encoding:
        case "raw":
            return raw_payload
        case "str":
            return raw_payload.decode("utf-8")
        case "json":
            if raw_payload == b"null":
                return None

            try:
                return json.loads(raw_payload)
            except json.JSONDecodeError as e:
                raise ValueError("Failed to decode JSON") from e
        case _:
            raise ValueError(f"Invalid encoding: {encoding}")


@overload
def encode_payload(payload: bytes | bytearray, encoding: Literal["raw"]) -> bytes: ...


@overload
def encode_payload(payload: str, encoding: Literal["str"]) -> bytes: ...


@overload
def encode_payload(payload: str | int | float | bool | None | dict | list, encoding: Literal["json"]) -> bytes: ...


def encode_payload(payload: PayloadType, encoding: PayloadEncoding = "json") -> bytes:
    match encoding:
        case "raw":
            if not isinstance(payload, (bytes, bytearray)):
                raise ValueError(f"Expected payload of type bytes or bytearray, got {type(payload)}")
            return bytes(payload)
        case "str":
            if not isinstance(payload, str):
                raise ValueError(f"Expected payload of type str, got {type(payload)}")
            return payload.encode("utf-8")
        case "json":
            if not isinstance(payload, (str, int, float, bool, type(None), dict, list)):
                raise ValueError(f"Expected payload of json serializable type, got {type(payload)}")
            return json.dumps(payload).encode("utf-8")
        case _:
            raise ValueError(f"Invalid encoding: {encoding}")


class Subscription[T: PayloadType]:
    def __init__(self, client: "MQTTClient", topic: str, *, encoding: PayloadEncoding = "json", message_buffer_size: int = 16):
        self._client = client
        self._topic = topic
        self._encoding = encoding
        self._send_channel, self._receive_channel = trio.open_memory_channel(message_buffer_size)

    @property
    def topic(self):
        return self._topic

    @property
    def encoding(self):
        return self._encoding

    def put(self, raw_payload: bytes):
        try:
            self._send_channel.send_nowait(raw_payload)
        except trio.WouldBlock:
            logging.warning("Message buffer full. Consider increasing message_buffer_size")

            # # discard an old message to fit the new message
            # self._receive_channel.receive_nowait()
            # self._send_channel.send_nowait(raw_payload)

    def matches(self, topic: str):
        return mqtt.topic_matches_sub(self._topic, topic)

    async def receive(self) -> T:
        raw_payload: bytes = await self._receive_channel.receive()
        self._client.set_read_event()

        return decode_payload(raw_payload, self._encoding)

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> T:
        try:
            return await self.receive()
        except trio.EndOfChannel:
            raise StopAsyncIteration from None


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

        # register mqtt callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._client.on_socket_open = self._on_socket_open
        self._client.on_socket_close = self._on_socket_close
        self._client.on_socket_register_write = self._on_socket_register_write
        self._client.on_socket_unregister_write = self._on_socket_unregister_write

        # register mqtt loop tasks
        self.add_worker(self._read_loop)
        self.add_worker(self._write_loop)
        self.add_worker(self._misc_loop)

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
        if sub not in topic_subscriptions:
            raise ValueError(f"Subscription {sub.topic} does not exist or was already unsubscribed")

        # remove the subscription object
        topic_subscriptions.remove(sub)

        # delete the whole list if no more topic subscriptions are left
        was_last = not topic_subscriptions
        if was_last:
            del self._subscriptions[sub.topic]
        return was_last

    async def subscribe[T: PayloadType](self, topic: str, *, qos: int = 0, encoding: PayloadEncoding = "json", message_buffer_size: int = 16) -> Subscription[T]:
        await self.wait_connected()

        self._logger.debug(f"Subscribing to {topic}")
        sub = Subscription(self, topic, encoding=encoding, message_buffer_size=message_buffer_size)
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

    async def publish[T: PayloadType](self, topic: str, payload: T, *, encoding: PayloadEncoding = "json", qos: int = 0, retain: bool = False):
        await self.wait_connected()

        raw_payload = encode_payload(payload, encoding=encoding)

        self._logger.debug(f"Publishing to {topic}: {raw_payload.decode("utf-8")[:100]}")
        self._client.publish(topic, raw_payload, qos, retain)

    async def read[T: PayloadType](self, topic: str, *, encoding: PayloadEncoding = "json", default: Optional[T] = None, required: bool = False, timeout: float = 0.1) -> T:
        # subscribe to the specified topic
        sub = await self.subscribe(topic, qos=1, encoding=encoding, message_buffer_size=0)

        # read a single message (probably the retained message)
        with trio.move_on_after(timeout) as cancel_scope:
            payload = await sub.receive()

        # sunsub from the topic again
        await self.unsubscribe(sub)

        # either return the received payload, a default value, or raise a timeout error
        if not cancel_scope.cancel_called:
            return payload
        if not required:
            return default
        raise ValueError("Topic read timed out")

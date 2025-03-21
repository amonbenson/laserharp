from typing import Optional
import trio
from ..component_v2 import Component
from ..mqtt import Subscription, PayloadType, PayloadEncoding
from .base import MQTTBaseComponent


class Access:
    def __init__(self, client: str = "rw", broker: str = "rw"):
        assert client in ("ro", "wo", "rw"), "invalid client access descriptor"
        assert broker in ("ro", "wo", "rw"), "invalid broker access descriptor"

        self.client_read = "r" in client
        self.client_write = "w" in client
        self.broker_read = "r" in broker
        self.broker_write = "w" in broker

        if not self.broker_write:
            raise NotImplementedError("Broker write access cannot be restricted")

    def has(self, *levels: str):
        for level in levels:
            if not hasattr(self, level):
                raise ValueError(f"Unknown access level: {level}")

        return all(getattr(self, level) for level in levels)

    def require(self, *levels: str):
        if not self.has(*levels):
            raise ValueError(f"Access denied ({'& '.join(levels)})")

    @staticmethod
    def full():
        return Access("rw", "rw")


class PubSubComponent[T: PayloadType](MQTTBaseComponent):
    DEFAULT_COOLDOWN = 0.001  # 1ms default cooldown period

    def __init__(self, name: str, parent: Component, *, qos: int = 0, retain: bool = True, default: Optional[T] = None, required: bool = False, access: Access = Access.full(), encoding: PayloadEncoding = "json"):
        super().__init__(name, parent)

        # store the subscription properties
        self._qos = qos
        self._retain = retain
        self._default = default
        self._required = required
        self._access = access
        self._encoding = encoding

        # internal client value
        self._client_value: T = default
        self._client_update_event = trio.Event()
        self._broker_update_event = trio.Event()

        self._sub: Subscription[T] = None

        # start tasks to handle receive (client -> app) and send (app -> client) communication
        if self._access.has("client_read", "broker_write"):
            self.add_worker(self._handle_receive)
        if self._access.has("client_write", "broker_read"):
            self.add_worker(self._handle_send)

    async def setup(self):
        if self._access.has("client_read"):
            # read the initial client value
            self._client_value = await self.read(None, encoding=self._encoding, default=self._default, required=self._required)

            # create a subscription to wait for continous updates
            self._sub = await self.subscribe(None, qos=self._qos, encoding=self._encoding, message_buffer_size=0)

    async def teardown(self):
        if self._sub is not None:
            await self.unsubscribe(self._sub)

    async def _handle_receive(self):
        self._access.require("client_read", "broker_write")

        async for payload in self._sub:
            # wait for broker updates, then update the internal value
            self._logger.debug(f"Got new value for {self._topic}")
            self._client_value = payload
            self._broker_update_event.set()

    async def _handle_send(self):
        self._access.require("client_write", "broker_read")

        while True:
            # wait for client updates, then publish the change
            await self._client_update_event.wait()
            self._client_update_event = trio.Event()

            await self.publish(None, self._client_value, encoding=self._encoding, qos=self._qos, retain=self._retain)

    @property
    def value(self) -> T:
        self._access.require("client_read")
        return self._client_value

    @value.setter
    def value(self, value: T):
        self._access.require("client_write")
        # set the new value locally and mark the update
        self._client_value = value
        self._client_update_event.set()

    async def wait_change(self) -> T:
        self._access.require("client_read")
        await self._broker_update_event.wait()
        self._broker_update_event = trio.Event()
        return self._client_value

    def discard_change(self):
        # reset the broker event even if the change was not handeled
        self._broker_update_event = trio.Event()

    @staticmethod
    async def wait_any_change(*pubsubs: "PubSubComponent", cooldown: float = DEFAULT_COOLDOWN):
        # wait for the cooldown period and discard any changes that arrive in between
        if cooldown > 0:
            await trio.sleep(cooldown)
            for pubsub in pubsubs:
                pubsub.discard_change()

        # start a nursery that gets canceled once any of the pubsubs receives a change
        async def cancel_on_change(pubsub: PubSubComponent, cancel_scope: trio.CancelScope):
            await pubsub.wait_change()
            cancel_scope.cancel()

        try:
            async with trio.open_nursery() as nursery:
                for pubsub in pubsubs:
                    nursery.start_soon(cancel_on_change, pubsub, nursery.cancel_scope)
        except trio.Cancelled:
            pass

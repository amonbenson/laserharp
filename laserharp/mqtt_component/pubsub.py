from typing import Optional
import trio
from ..component_v2 import Component
from ..mqtt import Subscription, PayloadType, PayloadEncoding
from .base import MQTTBaseComponent


class PubSubComponent[T: PayloadType](MQTTBaseComponent):
    DEFAULT_COOLDOWN = 0.001  # 1ms default cooldown period

    def __init__(self, name: str, parent: Component, *, qos: int = 0, retain: bool = True, default: Optional[T] = None, required: bool = False, encoding: PayloadEncoding = "json"):
        super().__init__(name, parent)

        # store the subscription properties
        self._qos = qos
        self._retain = retain
        self._default = default
        self._required = required
        self._encoding = encoding

        # internal client value
        self._client_value: T = default
        self._client_update_event = trio.Event()
        self._broker_update_event = trio.Event()

        self._sub: Subscription[T] = None

        self.add_worker(self._handle_receive)
        self.add_worker(self._handle_send)

    async def setup(self):
        # read the initial client value
        self._client_value = await self.read(None, encoding=self._encoding, default=self._default, required=self._required)

        # create a subscription to wait for continous updates
        self._sub = await self.subscribe(None, qos=self._qos, encoding=self._encoding, message_buffer_size=0)

    async def teardown(self):
        await self.unsubscribe(self._sub)

    async def _handle_receive(self):
        async for payload in self._sub:
            # wait for broker updates, then update the internal value
            self._logger.debug(f"Got new value for {self._topic}")
            self._client_value = payload
            self._broker_update_event.set()

    async def _handle_send(self):
        while True:
            # wait for client updates, then publish the change
            await self._client_update_event.wait()
            self._client_update_event = trio.Event()

            await self.publish(None, self._client_value, encoding=self._encoding, qos=self._qos, retain=self._retain)

    @property
    def value(self) -> T:
        return self._client_value

    @value.setter
    def value(self, value: T):
        # set the new value locally and mark the update
        self._client_value = value
        self._client_update_event.set()

    async def wait_change(self) -> T:
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

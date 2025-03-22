from typing import Optional, Callable
import jsonschema.exceptions
import jsonschema.validators
import trio
import jsonschema
from referencing.jsonschema import EMPTY_REGISTRY
from ..component_v2 import Component
from ..mqtt import Subscription, PayloadType, JsonPayloadType, PayloadEncoding
from .base import MQTTBaseComponent


class EndpointComponent[T: PayloadType](MQTTBaseComponent):
    class Access:
        def __init__(self, client: str = "rw", broker: str = "rw"):
            assert client in ("r", "w", "rw"), "invalid client access descriptor"
            assert broker in ("r", "w", "rw"), "invalid broker access descriptor"

            self.client_read = "r" in client
            self.client_write = "w" in client
            self.broker_read = "r" in broker
            self.broker_write = "w" in broker

        def has(self, *levels: str):
            for level in levels:
                if not hasattr(self, level):
                    raise ValueError(f"Unknown access level: {level}")

            return all(getattr(self, level) for level in levels)

        def require(self, *levels: str):
            if not self.has(*levels):
                raise ValueError(f"Access denied ({'& '.join(levels)})")

        @classmethod
        def full(cls):
            return cls(client="rw", broker="rw")

    DEFAULT_COOLDOWN = 0.001  # 1ms default cooldown period

    def __init__(
        self,
        name: str,
        parent: Component,
        *,
        topic: Optional[str] = None,
        default: T = None,
        schema: Optional[dict] = None,
        qos: int = 0,
        retain: bool = True,
        access: Access | str = Access.full(),
        encoding: PayloadEncoding = "json",
    ):
        super().__init__(name, parent, topic=topic)

        # store the subscription properties
        self._qos = qos
        self._retain = retain
        self._default = default
        self._access = access if isinstance(access, self.Access) else self.Access(**access)
        self._encoding = encoding

        # create JSON schema validator
        self._schema_validator: jsonschema.Validator = None
        if schema is not None:
            if encoding != "json":
                raise ValueError("schema is only supported for encoding='json'")

            validator_cls: jsonschema.Validator = jsonschema.validators.validator_for(schema, default=jsonschema.validators.Draft7Validator)
            validator_cls.check_schema(schema)
            self._schema_validator = validator_cls(schema)

        # validate the default value
        if default is None:
            match encoding:
                case "raw":
                    default = b""
                case "str":
                    default = ""
                case "json":
                    default = {}
        self._try_validate(default, message="Validation failed for the default value: {e}", raise_exception=True)

        # internal client value
        self._client_value: T = default
        self._client_update_event = trio.Event()
        self._broker_update_event = trio.Event()

        self._sub: Subscription[T] = None

        # start tasks to handle receive (client -> app) and send (app -> client) communication
        if self._access.has("broker_write"):
            self.add_worker(self._handle_receive)
        if self._access.has("broker_read"):
            self.add_worker(self._handle_send)

    def validate(self, value: T) -> bool:
        # check value type based on encoding
        match self._encoding:
            case "raw":
                valid_types = (bytes, bytearray)
            case "str":
                valid_types = (str,)
            case "json":
                # valid_types = (str, int, float, bool, type(None), dict, list)
                valid_types = (dict, list)

        assert isinstance(value, valid_types), f"Invalid type: {type(value).__name__}"

        # check json values via schema
        if self._encoding == "json" and self._schema_validator is not None:
            self._schema_validator.validate(value)

        # accept value
        return True

    def _try_validate(self, value: T, *, message="Validation failed: {e}", log_exception: bool = True, raise_exception: bool = False) -> bool:
        try:
            return self.validate(value)
        except Exception as e:  # pylint: disable=broad-exception-caught
            if log_exception:
                self._logger.warning(message.format(e=e))
            if raise_exception:
                raise ValueError(message.format(e=e)) from e
            return False

    async def setup(self):
        retained_payload = None

        if self._access.has("broker_write"):
            # read the initial client value (a retained message from the broker)
            retained_payload = await self.read(self.OWN_TOPIC, encoding=self._encoding, default=None, required=False)
            if retained_payload is not None and self._try_validate(retained_payload, message="Validation failed for initial broker-retained value: {e}. Publishing the client-default value."):
                self._client_value = retained_payload

            # create a subscription to wait for continous updates
            self._sub = await self.subscribe(self.OWN_TOPIC, qos=self._qos, encoding=self._encoding, message_buffer_size=0)

        # publish the initial client value if it's different from the current retained message
        if self._access.has("broker_read") and self._client_value != retained_payload:
            await self.publish(self.OWN_TOPIC, self._client_value, encoding=self._encoding, qos=self._qos, retain=self._retain)

    async def teardown(self):
        if self._sub is not None:
            await self.unsubscribe(self._sub)

    async def _handle_receive(self):
        self._access.require("broker_write")

        async for payload in self._sub:
            # wait for broker updates, then update the internal value
            self._logger.debug(f"Got new value for {self._topic}")

            if not self._try_validate(payload, message="Validation failed for broker-set value: {e}. Keeping current client value and forcing a publish."):
                self._client_update_event.set()
                continue

            self._client_value = payload
            self._broker_update_event.set()

    async def _handle_send(self):
        self._access.require("broker_read")

        while True:
            # wait for client updates, then publish the change
            await self._client_update_event.wait()
            self._client_update_event = trio.Event()

            await self.publish(self.OWN_TOPIC, self._client_value, encoding=self._encoding, qos=self._qos, retain=self._retain)

    @property
    def value(self) -> T:
        self._access.require("client_read")

        return self._client_value

    @value.setter
    def value(self, value: T):
        self._access.require("client_write")

        if not self._try_validate(value, message="Validation failed for client-set value: {e}. Ignoring."):
            return

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
    async def wait_any_change(*endpoints: "EndpointComponent", cooldown: float = DEFAULT_COOLDOWN):
        # wait for the cooldown period and discard any changes that arrive in between
        if cooldown > 0:
            await trio.sleep(cooldown)
            for endpoint in endpoints:
                endpoint.discard_change()

        # start a nursery that gets canceled once any of the endpoints receives a change
        async def cancel_on_change(endpoint: EndpointComponent, cancel_scope: trio.CancelScope):
            await endpoint.wait_change()
            cancel_scope.cancel()

        try:
            async with trio.open_nursery() as nursery:
                for endpoint in endpoints:
                    nursery.start_soon(cancel_on_change, endpoint, nursery.cancel_scope)
        except trio.Cancelled:
            pass


# class RawEndpointComponent(EndpointComponent[bytes]):
#     def __init__(self, name: str, parent: Component, **kwargs):
#         super().__init__(name, parent, encoding="raw", **kwargs)

#     def validate(self, value: bytes):
#         assert isinstance(value, bytes), f"Invalid type: {type(value).__name__}"
#         return True


# class JsonEndpointComponent(EndpointComponent[JsonPayloadType]):
#     def __init__(self, name: str, parent: Component, *, schema: dict = None, **kwargs):
#         super().__init__(name, parent, encoding="raw", **kwargs)

#         if schema is not None:
#             jsonschema.Validator.check_schema(schema)
#             self._schema_validator = jsonschema.Validator(schema)

#     def validate(self, value: JsonPayloadType):
#         assert isinstance(value, (str, int, float, bool, type(None), dict, list)), f"Invalid type: {type(value).__name__}"

#         # no schema provided, accept any value
#         if self._schema_validator is None:
#             return True

#         # use JSON schema validation
#         error = jsonschema.exceptions.best_match(self._schema_validator.iter_errors(value))
#         if error is not None:
#             raise error

#         return True

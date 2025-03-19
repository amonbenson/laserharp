import logging
import trio
from abc import ABC, abstractmethod
from typing import Callable, Optional, overload


class Component(ABC):
    SETUP_TIMEOUT = 5
    CANCEL_TIMEOUT = 5

    def __init__(self, name: str, parent: Optional["Component"]):
        self._name = name
        self._parent = parent
        self._cancel_scope: Optional[trio.CancelScope] = None

        self._full_name = f"{parent.full_name}:{name}" if parent else self._name
        self._logger = logging.getLogger(self._full_name)

        self._children: dict[str, Component] = {}
        # self._channels: dict[str, (trio.MemorySendChannel, trio.MemoryReceiveChannel)] = {}

        self._initialized = False
        self._running = False
        self._running_event = trio.Event()

    @property
    def name(self):
        return self._name

    @property
    def full_name(self):
        return self._full_name

    @property
    def running(self):
        return self._running

    def cancel(self):
        if not self._running:
            raise ValueError("Cannot cancel: component is not running")

        self._cancel_scope.cancel()

    def add_child[C: "Component"](self, name: str, child_type: type[C], *args, **kwargs) -> C:
        if self._initialized:
            raise ValueError("Component is already initialized.")

        if isinstance(child_type, Component):
            raise ValueError(f"child_type must be a class type, e.g. {type(child_type)}, not an instance of a Component class")
        if not isinstance(child_type, type(Component)):
            raise ValueError(f"Cannot instantiate child of unsupported type: {child_type}")

        if name in self._children:
            raise ValueError(f"Child {name} already exists")

        child = child_type(name, self, *args, **kwargs)
        self._children[name] = child
        return child

    def add_worker(self, name: str, worker_method: Callable, *args, **kwargs) -> "WorkerComponent":
        return self.add_child(name, WorkerComponent, worker_method, args, kwargs)

    def child[C: "Component"](self, name: str) -> C:
        return self._children[name]

    # def add_channel(self, name: str, max_buffer_size: int | float = 0):
    #     if self._initialized:
    #         raise ValueError("Component is already initialized.")

    #     self._channels[name] = trio.open_memory_channel(max_buffer_size)

    # def send_channel(self, name: str) -> trio.MemorySendChannel:
    #     return self._channels[name][0]

    # def receive_channel(self, name: str) -> trio.MemoryReceiveChannel:
    #     return self._channels[name][1]

    async def wait_running(self):
        while not self._running:
            await self._running_event.wait()

    async def setup(self):
        pass

    async def teardown(self):
        pass

    async def run(self, cancel_scope: Optional[trio.CancelScope] = None):
        try:
            # mark component as initialized
            self._initialized = True
            self._cancel_scope = cancel_scope

            # invoke the start method of this component
            self._logger.info(f"Starting {self.name}...")
            try:
                with trio.fail_after(self.SETUP_TIMEOUT):
                    await self.setup()
            except trio.TooSlowError:
                self._logger.error("Component setup timed out")
                raise

            # start all children in parallel
            self._logger.info(f"Starting {self.name} children/workers...")
            async with trio.open_nursery() as nursery:
                for child in self._children.values():
                    nursery.start_soon(child.run, nursery.cancel_scope)

                # mark as running
                self._running = True
                self._running_event.set()

        finally:
            # invoke the stop method with a timeout
            self._logger.info(f"Stopping {self.name}...")
            try:
                with trio.fail_after(self.CANCEL_TIMEOUT, shield=True):
                    await self.teardown()
            except trio.TooSlowError:
                self._logger.error("Component teardown timed out")
                raise

            self._cancel_scope = None


class WorkerComponent(Component):
    def __init__(self, name: str, parent: Component, method: Callable, args: list, kwargs: dict):
        super().__init__(name, parent)
        self._method = method
        self._args = args
        self._kwargs = kwargs

    def setup(self):
        pass  # do nothing here, we override the run method instead

    async def run(self, cancel_scope):
        self._logger.info(f"Running worker {self.name}...")
        await self._method(*self._args, **self._kwargs)


class RootComponent(Component):
    def __init__(self, name: str):
        super().__init__(name, None)

    async def run(self):
        # use a global cancel scope
        cancel_scope = trio.CancelScope()
        with cancel_scope:
            await super().run(cancel_scope)

import logging
import trio
from abc import ABC, abstractmethod
from typing import Callable, Optional


class Component(ABC):
    STOP_TIMEOUT = 1

    def __init__(self, name: str, parent: Optional["Component"]):
        self._name = name
        self._parent = parent
        self._cancel_scope: Optional[trio.CancelScope] = None

        self._full_name = f"{parent.full_name}:{name}" if parent else self._name
        self._logger = logging.getLogger(self._full_name)

        self._children: dict[str, Component] = {}
        self._channels: dict[str, (trio.MemorySendChannel, trio.MemoryReceiveChannel)] = {}

        self._initialized = False
        self._running = False
        self._running_event = trio.Event()

        # run the setup method immediately
        self.setup()
        self._initialized = True

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

    def add_child(self, name: str, child: type["Component"] | Callable, *args, **kwargs):
        if self._initialized:
            raise ValueError("Component is already initialized.")

        if isinstance(child, type(Component)):
            # instantiate a new child
            child_instance = child(name, self, *args, **kwargs)
        elif isinstance(child, Callable):
            # wrap callables inside a single method component
            child_instance = SingleMethodComponent(name, self, child, args, kwargs)
        else:
            raise ValueError(f"Cannot instantiate child of unsupported type: {child}")

        self._children[name] = child_instance

    def child(self, name):
        return self._children[name]

    def add_channel(self, name: str, max_buffer_size: int | float = 0):
        if self._initialized:
            raise ValueError("Component is already initialized.")

        self._channels[name] = trio.open_memory_channel(max_buffer_size)

    def channel(self, name):
        return self._channels[name]

    async def wait_running(self):
        while not self._running:
            await self._running_event.wait()

    @abstractmethod
    def setup(self):
        pass

    async def start(self):
        pass

    async def stop(self):
        pass

    async def run(self, cancel_scope: Optional[trio.CancelScope] = None):
        try:
            self._cancel_scope = cancel_scope

            # invoke the start method of this component
            self._logger.info("Starting...")
            await self.start()

            # start all children in parallel
            async with trio.open_nursery() as nursery:
                for child in self._children.values():
                    nursery.start_soon(child.run, nursery.cancel_scope)

                # mark as running
                self._running = True
                self._running_event.set()

        finally:
            # invoke the stop method with a timeout
            self._logger.info("Stopping...")
            with trio.fail_after(self.STOP_TIMEOUT, shield=True):
                await self.stop()

            self._cancel_scope = None


class SingleMethodComponent(Component):
    def __init__(self, name: str, parent: Component, method: Callable, args: list, kwargs: dict):
        super().__init__(name, parent)
        self._method = method
        self._args = args
        self._kwargs = kwargs

    def setup(self):
        pass  # do nothing here, we override the run method instead

    async def run(self, cancel_scope):
        self._logger.info("Starting...")
        await self._method(*self._args, **self._kwargs)


class RootComponent(Component):
    def __init__(self, name: str):
        super().__init__(name, None)

    async def run(self):
        # use a global cancel scope
        cancel_scope = trio.CancelScope()
        with cancel_scope:
            await super().run(cancel_scope)

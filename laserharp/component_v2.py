import logging
import trio
from abc import ABC, abstractmethod
from typing import Callable, Optional, overload


class Component(ABC):
    SETUP_TIMEOUT = 5
    CANCEL_TIMEOUT = 5

    _global_children = {}

    def __init__(self, name: str, parent: Optional["Component"] = None):
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

    def is_root(self):
        return self._parent is None

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

        # instantiate the child
        child = child_type(name, self, *args, **kwargs)

        # check if the child's __init__ method was called successfully
        if not hasattr(child, "_children"):
            raise ValueError(f"Invalid child. Did you call super().__init__(...) from {child_type.__name__}.__init__(...)?")

        self._children[name] = child
        return child

    def add_global_child[C: "Component"](self, name: str, child_type: type[C], *args, **kwargs) -> C:
        if name in Component._global_children:
            raise ValueError(f"Child {name} already exists globally.")

        child = self.add_child(name, child_type, *args, **kwargs)
        Component._global_children[name] = child

        return child

    def add_worker(self, worker_method: Callable, *args, **kwargs) -> "WorkerComponent":
        name = worker_method.__name__
        if not (name.startswith("_run_") or name.startswith("_handle_")):
            self._logger.warning(f"Worker methods should start with '_run' or '_handle' (got '{name}')")

        # note: WorkerComponent takes in args and kwargs as direct parameters, so we don't use the spread syntax here
        return self.add_child(name, WorkerComponent, worker_method, args, kwargs)

    def get_child[C: "Component"](self, name: str) -> C:
        if name not in self._global_children:
            raise ValueError(f"Child {name} does not exist")

        return self._children[name]

    def get_global_child[C: "Component"](self, name: str) -> C:
        if name not in self._global_children:
            raise ValueError(f"Global child {name} does not exist")

        return Component._global_children[name]

    # def get_global_singleton[C: "Component"](self, name: str, child_type: type[C], *args, **kwargs) -> C:
    #     if name not in self._global_children:
    #         return self.add_global_child(name, child_type, *args, **kwargs)

    #     return self.get_global_child(name)

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

    async def _run(self, cancel_scope: Optional[trio.CancelScope] = None):
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
            self._logger.info(f"Starting {self.name} children and workers...")
            async with trio.open_nursery() as nursery:
                for child in self._children.values():
                    nursery.start_soon(child.run, nursery.cancel_scope)

                # mark as running
                self._running = True
                self._running_event.set()

            # run finished
            self._logger.info("All children and workers exited.")

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

    async def run(self, cancel_scope: Optional[trio.CancelScope] = None):
        if self.is_root():
            # use a global cancel scope
            root_cancel_scope = trio.CancelScope()
            with root_cancel_scope:
                await self._run(root_cancel_scope)
        else:
            await self._run(cancel_scope)


class WorkerComponent(Component):
    def __init__(self, name: str, parent: Component, method: Callable, args: list, kwargs: dict):
        super().__init__(name, parent)
        self._method = method
        self._args = args
        self._kwargs = kwargs

    def setup(self):
        pass  # do nothing here, we override the run method instead

    async def run(self, cancel_scope):
        self._logger.info(f"Starting worker {self.name}...")
        await self._method(*self._args, **self._kwargs)

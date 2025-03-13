from abc import ABC, abstractmethod
from typing import Generic, TypeVar, AsyncGenerator
import logging
import asyncio


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("async_pubsub")

T = TypeVar("T")

class Subscription(ABC, Generic[T]):
    def __init__(self):
        self._queue: asyncio.Queue[T] = asyncio.Queue()

    @abstractmethod
    async def accept(self, message: T) -> bool:
        ...

    async def put(self, message: T):
        if await self.accept(message):
            await self._queue.put(message)

    async def __aiter__(self) -> AsyncGenerator[T, None]:
        while True:
            message = await self._queue.get()
            yield message

class Publisher(Generic[T]):
    def __init__(self, subscription_cls: type[Subscription[T]]):
        self._subscription_cls = subscription_cls
        self._subscriptions: list[Subscription[T]] = []

    @abstractmethod
    async def source(self):
        ...

    async def run(self):
        try:
            async for message in self.source():
                for sub in self._subscriptions:
                    await sub.put(message)
        except asyncio.CancelledError:
            pass
        finally:
            pass

    async def subscribe(self, *args, **kwargs) -> Subscription[T]:
        sub = self._subscription_cls(*args, **kwargs)
        self._subscriptions.append(sub)
        return sub


class AsyncRangeSubscription(Subscription[int]):
    def __init__(self, kind: str):
        super().__init__()
        self._kind = kind

    async def accept(self, message):
        match self._kind:
            case "even":
                return message % 2 == 0
            case "odd":
                return message % 2 == 1
            case _:
                raise ValueError(f"Invalid kind: {self._kind}")

class AsyncRange(Publisher[AsyncRangeSubscription]):
    def __init__(self, start, end):
        super().__init__(AsyncRangeSubscription)
        self.data = range(start, end)

    async def source(self):
        for i in self.data:
            await asyncio.sleep(0.5)
            yield i



async def main():
    arange = AsyncRange(0, 5)

    even_sub = await arange.subscribe("even")
    odd_sub = await arange.subscribe("odd")

    async def consume(name: str, subscription: AsyncRangeSubscription):
        try:
            async for message in subscription:
                print(f"{name} received: {message}")
        except asyncio.CancelledError:
            pass

    tasks = map(asyncio.create_task, [
        arange.run(),
        consume("even_sub", even_sub),
        consume("odd_sub", odd_sub),
    ])

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())

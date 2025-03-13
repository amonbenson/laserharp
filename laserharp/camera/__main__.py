import os
import trio
from . import get_camera

if __name__ == "__main__":
    async def consumer(frames: trio.MemoryReceiveChannel):
        async with frames:
            async for frame in frames:
                print(f"Got frame {frame}")

    async def main():
        camera = get_camera()

        async with trio.open_nursery() as nursery:
            if bool(os.getenv("LH_EMULATOR")):
                from ..mqtt import get_mqtt
                nursery.start_soon(get_mqtt().run, nursery)

            nursery.start_soon(camera.run, nursery)
            nursery.start_soon(consumer, camera.frame_receive_channel())

    trio.run(main)

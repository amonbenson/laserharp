import trio
from . import get_camera
from ...common.env import getenv

if __name__ == "__main__":
    async def consumer(frames: trio.MemoryReceiveChannel):
        async with frames:
            async for frame in frames:
                print(f"Got frame {frame}")

    async def main():
        camera = get_camera()

        async with trio.open_nursery() as nursery:
            if getenv("LH_EMULATOR", type=bool):
                from ...common.mqtt import MQTT
                nursery.start_soon(MQTT.run)

            nursery.start_soon(camera.run, nursery)
            nursery.start_soon(consumer, camera.frame_receive_channel())

    trio.run(main)

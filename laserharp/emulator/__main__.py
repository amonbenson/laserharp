import trio
from ..common.mqtt import get_mqtt

async def camera_stream():
    await trio.sleep(0.5) # very ugly, use condition or another technique to wait for mqtt to be ready

    try:
        while True:
            get_mqtt().publish("lh/emulator/camera/stream", "test")
            await trio.sleep(0.5) # trio.sleep(1 / 50)
    except trio.Cancelled:
        pass

async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(get_mqtt().run, nursery)
        nursery.start_soon(camera_stream)

if __name__ == "__main__":
    trio.run(main)

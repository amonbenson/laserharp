import trio
from ..common.mqtt import MQTT

async def camera_stream():
    try:
        while True:
            MQTT.publish("lh/emulator/camera/stream", "test")
            await trio.sleep(0.5) # trio.sleep(1 / 50)
    except trio.Cancelled:
        pass

async def start_components():
    # make sure IO tasks are running until starting the main components
    async with MQTT:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(camera_stream)

async def main():
    async with trio.open_nursery() as nursery:
        # start IO tasks first
        nursery.start_soon(MQTT.run, nursery)
        nursery.start_soon(start_components)

if __name__ == "__main__":
    trio.run(main)

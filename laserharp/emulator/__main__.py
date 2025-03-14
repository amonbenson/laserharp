import os
import logging
import trio
from ..common.mqtt import MQTT
from .camera import Camera
from .stm_board import STMBoard


NUM_LASERS = int(os.getenv("LH_EMULATOR_NUM_LASERS", 11))

logger = logging.getLogger("lh:emulator")


async def main():
    stm = STMBoard(NUM_LASERS)
    camera = Camera()

    # start all required tasks in parallel
    async with trio.open_nursery() as nursery:
        nursery.start_soon(MQTT.run)
        nursery.start_soon(stm.run)
        # nursery.start_soon(camera.run)

if __name__ == "__main__":
    trio.run(main)

import logging
import trio
from ..common.mqtt import MQTT


logger = logging.getLogger("lh:emulator:camera")


class Camera:
    async def run(self):
        try:
            logger.info("Starting camera emulator")
            while True:
                await MQTT.publish("lh/emulator/camera/stream", "test")
                await trio.sleep(0.5) # trio.sleep(1 / 50)
        except trio.Cancelled:
            logger.info("Stopping camera emulator")

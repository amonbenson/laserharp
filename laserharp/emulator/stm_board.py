import logging
import trio
import numpy as np
from ..common.mqtt import MQTT


logger = logging.getLogger("lh:emulator:stm")


class STMBoard:
    def __init__(self, num_lasers):
        self.lasers = np.ones(num_lasers, dtype=float)

    async def run(self):
        # publish the initial laser state
        await MQTT.publish("lh/emulator/lasers/brightnesses", self.lasers.tolist(), retain=True)

        # start subscribing to the tx line
        sub = await MQTT.subscribe("lh/emulator/serial/tx")

        logger.info("STM emulator running")

        async for message in sub:
            try:
                await self._handle_message(message)
            except Exception as e:
                logger.error(f"Failed to handle message: {e}")

    async def _send(self, data: list[int]):
        await MQTT.publish("lh/emulator/serial/rx", data)

    async def _handle_message(self, data: list[int]):
        if len(data) != 4:
            logger.warning(f"Received message of invalid length: {data}")

        cmd_msb = data[0] & 0xF0
        cmd_lsb = data[0] & 0x0F

        match cmd_msb:
            case 0x00:
                raise NotImplementedError("USB Midi not implemented")
            case 0x10:
                raise NotImplementedError("Din Midi not implemented")
            case 0x80:
                match cmd_lsb:
                    case 0x00:
                        # set brightness of a single laser
                        await self.set_laser_brightness(data[1], data[2], data[3])
                    case 0x01:
                        # set brightness of all lasers
                        for i in range(len(self.lasers)):
                            await self.set_laser_brightness(i, data[1], data[2])
                    case 0x02:
                        # get brightness of a laser
                        brightness = self.get_laser_brightness(data[1])
                        await self._send([0x82, data[1], brightness, 0])
                    case _:
                        raise ValueError(f"Invalid command: {data[0] :02X}")
            case 0xF0:
                match cmd_lsb:
                    case 0x00:
                        # firmware version inquiry
                        await self._send([0xF0, 0x00, 0x01, 0x00])
                    case _:
                        raise ValueError(f"Invalid command: {data[0] :02X}")
            case _:
                raise ValueError(f"Invalid/Unimplemented command: {data[0] :02X}")

    def get_laser_brightness(self, diode_index: int):
        if diode_index not in range(len(self.lasers)):
            raise ValueError(f"Invalid diode index: {diode_index}")

        return self.lasers[diode_index]

    async def set_laser_brightness(self, diode_index: int, brightness: int, fade_duration: int):
        if fade_duration > 0:
            raise NotImplementedError("Fading is not implemented")
            return

        if diode_index not in range(len(self.lasers)):
            raise ValueError(f"Invalid diode index: {diode_index}")

        if brightness not in range(128):
            raise ValueError(f"Invalid brightness: {brightness}")

        self.lasers[diode_index] = brightness / 127
        await MQTT.publish("lh/emulator/lasers/brightnesses", self.lasers.tolist(), retain=True)

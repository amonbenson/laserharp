import logging
import trio
import cv2
import base64
import numpy as np
import random
from ..common.mqtt import MQTT


logger = logging.getLogger("lh:emulator:camera")


class Camera:
    def __init__(self):
        self._config = {
            # mechanical parameters
            "fov": [53.50, 41.41],  # field of view in degrees
            "mount_angle": 15.0,  # angle between camera center and vertical axis in degrees
            "mount_distance": 0.14338,  # distance from camera to laser plane in meters
            # basic confguration
            "resolution": [640, 480],  # VGA resolution
            "stream_resolution": [640, 480],  # VGA resolution
            "framerate": 50,  # max: 50
            # "rotation": 180, # configure any 90 degree rotation
            # exposure settings
            # "shutter_speed": 50000,  # in microseconds
            # "iso": 200,
            # image settings
            # "brightness": 50,
            # "contrast": 0,
            # "saturation": 0,
            # "sharpness": 0,
        }

        self._frame = np.zeros((self._config["resolution"][1], self._config["resolution"][0], 1), np.uint8)
        self._frame_lock = trio.Lock()

    def _angle_to_ypos(self, angle: float):
        fov_y = np.radians(self._config["fov"][1])
        height = self._config["resolution"][1]
        return angle / fov_y * height

    async def _run_config_handler(self):
        # publish initial config
        await MQTT.publish("lh/emulator/camera/config", self._config, qos=1, retain=True)

        sub = await MQTT.subscribe("lh/emulator/camera/config", qos=1)
        async for config in sub:
            async with self._frame_lock:
                cv2.resize(self._frame, (config["resolution"][1], config["resolution"][0]), dst=self._frame)

            self._config = config
            logger.info(f"Camera config updated: {config}")

    async def _run_intersection_handler(self):
        sub = await MQTT.subscribe("lh/emulator/lasers/intersections")
        async for message in sub:
            async with self._frame_lock:
                # clear frame
                self._frame.fill(0)

                # draw intersections
                for i, intersection in enumerate(message):
                    if intersection is None:
                        continue

                    fov_y = np.radians(self._config["fov"][1])
                    mount_angle = np.radians(self._config["mount_angle"])
                    camera_bottom = np.pi / 2 - mount_angle - fov_y / 2
                    ya = self._angle_to_ypos(-camera_bottom)
                    yb = self._angle_to_ypos(np.pi / 2 - camera_bottom)

                    y_metric = 3 * intersection  # assuming a maximum height of 3 meters
                    y_tan = y_metric / self._config["mount_distance"]
                    y_angle = np.atan(y_tan)
                    y_screen = y_angle * (yb - ya) / (np.pi / 2) + ya

                    x_screen = (i + 0.5) / len(message) * self._config["resolution"][0]

                    cv2.circle(self._frame, (int(x_screen), int(y_screen)), 10, (255,), -1)

    async def _run_stream(self):
        logger.info("Camera stream running")

        while True:
            # encode frame to jpg
            async with self._frame_lock:
                # cv2.line(
                #     self._frame,
                #     (random.randint(0, self._config["resolution"][0]), random.randint(0, self._config["resolution"][1])),
                #     (random.randint(0, self._config["resolution"][0]), random.randint(0, self._config["resolution"][1])),
                #     (random.randint(0, 255),),
                #     10,
                # )
                _, jpg = cv2.imencode(".jpg", self._frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])

            # send base64 encoded payload
            payload = base64.b64encode(jpg)
            await MQTT.publish("lh/emulator/camera/stream", payload, qos=0, debug=False)

            # emulate frame rate
            await trio.sleep(1 / self._config["framerate"])

    async def run(self):
        try:
            async with trio.open_nursery() as nursery:
                nursery.start_soon(self._run_config_handler)
                nursery.start_soon(self._run_intersection_handler)
                nursery.start_soon(self._run_stream)
        except* trio.Cancelled:
            logger.info("Camera emulator stopped")

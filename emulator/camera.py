import logging
import trio
import cv2
import base64
import numpy as np
import random
from laserharp.mqtt_component import ConfigurableComponent, PUBLISH_ONLY_ACCESS


logger = logging.getLogger("lh:emulator:camera")


class Camera(ConfigurableComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_config(
            """
            type: object
            properties:
                fov_x:
                    title: "FOV X"
                    description: "Field of view in the x-direction (in degrees)"
                    type: number
                    minimum: 1
                    maximum: 179
                    default: 53.50

                fov_y:
                    title: "FOV Y"
                    description: "Field of view in the y-direction (in degrees)"
                    type: number
                    minimum: 1
                    maximum: 179
                    default: 41.41

                mount_angle:
                    title: "Mount Angle"
                    description: "Angle between the camera view center line and vertical axis (in degrees)"
                    type: number
                    minimum: 0
                    maximum: 90
                    default: 15.0

                mount_distance:
                    title: "Mount Distance"
                    description: "Distance from camera to laser plane (in meters)"
                    type: number
                    minimum: 0
                    maximum: 1
                    default: 0.14338

                width:
                    title: "Width"
                    type: integer
                    minimum: 240
                    maximum: 1440
                    default: 640

                height:
                    title: "Height"
                    type: integer
                    minimum: 160
                    maximum: 1080
                    default: 480

                framerate:
                    title: "Framerate"
                    type: integer
                    minimum: 1
                    maximum: 50
                    default: 1

                rotation:
                    title: "Rotation"
                    description: "Set any 90-degree rotation (in degrees)"
                    type: integer
                    enum: [0, 90, 180, 270]
                    default: 0

                shutter_speed:
                    title: "Shutter speed"
                    title: "Shutter speed (in microseconds)"
                    type: integer
                    minimum: 1
                    maximum: 10000000
                    default: 50000

                iso:
                    title: "ISO"
                    title: "Camera sensor ISO sensitivity"
                    type: integer
                    minimum: 10
                    maximum: 800
                    default: 200
            required:
                - fov_x
                - fov_y
                - mount_angle
                - mount_distance
                - width
                - height
                - framerate
                - rotation
                - shutter_speed
                - iso
            """
        )

        self._frame = np.zeros((self.config.value["height"], self.config.value["width"], 1), np.uint8)
        self._frame_lock = trio.Lock()

        self._mqtt._logger.setLevel("DEBUG")
        self.stream = self.add_endpoint("stream", encoding="raw", qos=0, retain=False, access=PUBLISH_ONLY_ACCESS)

        self.add_worker(self._run_stream)
        self.add_worker(self._handle_config_change)

    def _angle_to_ypos(self, angle: float):
        fov_y = np.radians(self.config.value["fov_y"])
        height = self.config["height"]
        return angle / fov_y * height

    # async def _run_config_handler(self):
    #     # publish initial config
    #     await MQTT.publish("lh/emulator/camera/config", self._config, qos=1, retain=True)

    #     sub = await MQTT.subscribe("lh/emulator/camera/config", qos=1)
    #     async for config in sub:
    #         async with self._frame_lock:
    #             cv2.resize(self._frame, (config["resolution"][1], config["resolution"][0]), dst=self._frame)

    #         self._config = config
    #         logger.info(f"Camera config updated: {config}")

    # async def _run_intersection_handler(self):
    #     sub = await MQTT.subscribe("lh/emulator/lasers/intersections")
    #     async for message in sub:
    #         async with self._frame_lock:
    #             # clear frame
    #             self._frame.fill(0)

    #             # draw intersections
    #             for i, intersection in enumerate(message):
    #                 if intersection is None:
    #                     continue

    #                 fov_y = np.radians(self._config["fov"][1])
    #                 mount_angle = np.radians(self._config["mount_angle"])
    #                 camera_bottom = np.pi / 2 - mount_angle - fov_y / 2
    #                 ya = self._angle_to_ypos(-camera_bottom)
    #                 yb = self._angle_to_ypos(np.pi / 2 - camera_bottom)

    #                 y_metric = 3 * intersection  # assuming a maximum height of 3 meters
    #                 y_tan = y_metric / self._config["mount_distance"]
    #                 y_angle = np.atan(y_tan)
    #                 y_screen = y_angle * (yb - ya) / (np.pi / 2) + ya

    #                 x_screen = (i + 0.5) / len(message) * self._config["resolution"][0]

    #                 cv2.circle(self._frame, (int(x_screen), int(y_screen)), 10, (255,), -1)

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
            self.stream.value = payload

            # emulate frame rate
            await trio.sleep(1 / self.config.value["framerate"])

    async def _handle_config_change(self):
        while True:
            config = await self.config.wait_change()
            self._logger.warning("Config change handler not implemented")

    # async def run(self):
    #     try:
    #         async with trio.open_nursery() as nursery:
    #             nursery.start_soon(self._run_config_handler)
    #             nursery.start_soon(self._run_intersection_handler)
    #             nursery.start_soon(self._run_stream)
    #     except* trio.Cancelled:
    #         logger.info("Camera emulator stopped")

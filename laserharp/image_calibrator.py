from dataclasses import dataclass
import time
import logging
import os
import numpy as np
import cv2
import yaml
import json
from perci import ReactiveDictNode
from .camera import Camera
from .laser_array import LaserArray
from .component import Component


def _compare_config(a: dict, b: dict):
    keys = set(a.keys()) & set(b.keys())
    a = {k: a[k] for k in keys}
    b = {k: b[k] for k in keys}

    for k in keys:
        va = a[k]
        vb = b[k]

        # make sure we can compare tuples and lists
        if isinstance(va, tuple):
            va = list(va)
        if isinstance(vb, tuple):
            vb = list(vb)

        if isinstance(va, dict) and isinstance(vb, dict):
            if not _compare_config(va, vb):
                return False
        elif va != vb:
            logging.debug(f"Key {k} does not match: {a[k]} != {b[k]}")
            return False

    return True


@dataclass
class Calibration:
    # y limits in pixels
    ya: float
    yb: float

    # beam line parameters in pixels
    x0: np.ndarray
    m: np.ndarray

    def __post_init__(self):
        # type casting
        self.ya = np.float32(self.ya)
        self.yb = np.float32(self.yb)
        self.x0 = np.array(self.x0, dtype=np.float32)
        self.m = np.array(self.m, dtype=np.float32)

        # sanity checks
        assert self.ya < self.yb
        assert len(self.x0) == len(self.m)

    def to_dict(self):
        return {
            "ya": float(self.ya),
            "yb": float(self.yb),
            "x0": self.x0.tolist(),
            "m": self.m.tolist(),
        }

    @staticmethod
    def from_dict(d):
        return Calibration(ya=d["ya"], yb=d["yb"], x0=np.array(d["x0"]), m=np.array(d["m"]))


class ImageCalibrator(Component):
    def __init__(self, name: str, global_state: ReactiveDictNode, laser_array: LaserArray, camera: Camera):
        super().__init__(name, global_state)

        self.laser_array = laser_array
        self.camera = camera

        # load the stored calibration data
        self.calibration = None

        self.state["calibration"] = None
        self.state["current_index"] = None

    def start(self):
        pass

    def stop(self):
        pass

    def required_config(self) -> dict:
        # get all configuration values that must be consistent between calibration and runtime
        laser_array_config = self.laser_array.config.json()
        camera_config = self.camera.config.json()

        return {
            "laser_array": laser_array_config,
            "camera": {
                "fov": camera_config["fov"],
                "mount_angle": camera_config["mount_angle"],
                "resolution": camera_config["resolution"],
                "rotation": camera_config["rotation"],
            },
        }

    def load(self) -> bool:
        d = json.loads(self.settings["calibration_data"])
        if not d:
            logging.warning("No calibration data available")
            return False

        # check if the config is compatible
        required_config = d["required_config"]
        if not _compare_config(required_config, self.required_config()):
            logging.warning("Calibration data is incompatible with current configuration")
            return False

        self.calibration = Calibration.from_dict(d["calibration"])

        # set the calibration data in the state
        self.state["calibration"] = self.calibration.to_dict()
        self.state["current_index"] = None

        return True

    def save(self):
        if self.calibration is None:
            raise RuntimeError("Not calibrated yet")

        # update the stored calibration data
        self.settings["calibration_data"] = json.dumps(
            {
                "required_config": self.required_config(),
                "calibration": self.calibration.to_dict(),
            },
            separators=(",", ":"),
        )

    def _angle_to_ypos(self, angle: float):
        fov_y = np.radians(self.camera.config["fov"][1])
        height = self.camera.resolution[1]
        return angle / fov_y * height

    def _combined_capture(self, num_frames: int, interval: float, mode="avg"):
        result = self.camera.capture().astype(np.float32) / 255.0

        for _ in range(num_frames - 1):
            frame = self.camera.capture().astype(np.float32) / 255.0

            if mode == "avg":
                result += frame
            elif mode == "max":
                result = np.maximum(result, frame)

            time.sleep(interval)

        if mode == "avg":
            result /= num_frames

        return result

    def _fit_line(self, img):
        # apply gaussian blur
        ksize = self.config["preblur"]
        blurred = cv2.GaussianBlur(img, (ksize, ksize), 0)

        # get the brightes x coordinate of each row as point estimates
        b = np.max(blurred, axis=1)
        xs = np.argmax(blurred, axis=1)
        ys = np.arange(img.shape[0])

        # use the threshold mask as weights
        ws = b > self.config["threshold"]

        # check if the minimum coverage is met
        if np.sum(ws) / img.shape[0] < self.config["min_coverage"]:
            return None, None

        # fit a line to the points (swap x and y because we want to fit a vertical line)
        return np.polyfit(y=xs, x=ys, deg=1, w=ws)

    def calibrate(self, save_debug_images=False) -> Calibration:
        logging.info("Starting calibration")

        # store the laser state
        self.laser_array.push_state()

        # setup the static calibration data
        fov_y = np.radians(self.camera.config["fov"][1])
        mount_angle = np.radians(self.camera.config["mount_angle"])
        camera_bottom = np.pi / 2 - mount_angle - fov_y / 2
        # camera_top = np.pi / 2 - mount_angle + fov_y / 2

        # calculate the position of the 0 and 90 degree mark in pixel space
        ya = self._angle_to_ypos(-camera_bottom)
        yb = self._angle_to_ypos(np.pi / 2 - camera_bottom)

        calibration = Calibration(
            ya=ya,
            yb=yb,
            x0=-np.ones(len(self.laser_array), dtype=np.float32),
            m=np.zeros(len(self.laser_array), dtype=np.float32),
        )
        self.state["calibration"] = calibration.to_dict()

        # STEP 1: capture the base image
        logging.info("Capturing base image")
        self.laser_array.set_all(0)

        base_img = self._combined_capture(10, 0.1, mode="max")

        if save_debug_images:
            cv2.imwrite("cap_base.jpg", (base_img * 255).astype(np.uint8))

        # STEP 2: fit a line to each individual laser's beam path
        for i, _ in enumerate(self.laser_array):
            logging.info(f"Capturing laser {i}")
            self.laser_array[i] = 127

            combined_capture = np.zeros_like(base_img)
            self.state["current_index"] = i

            while True:
                # capture the laser beam and subtract the base image
                logging.debug("Start capture")
                capture = self._combined_capture(30, 0, mode="max")
                capture = np.clip(capture - base_img, 0, 1)

                # combine all captures
                combined_capture = np.maximum(combined_capture, capture)

                # convert to uint8
                beam_img = (combined_capture * 255).astype(np.uint8)
                if save_debug_images:
                    cv2.imwrite(f"cap_laser_{i}.jpg", beam_img)

                # fit a line to the laser beam
                logging.debug("Fitting line")

                # if the camera is disabled, use dummy data to simulate the calibration
                if not self.camera.enabled:
                    logging.warning("Camera interface is disabled. Using dummy data for calibration.")
                    p = i / (len(self.laser_array) - 1) - 0.5

                    m = p * 0.2
                    x0 = self.camera.resolution[0] * (0.5 + p * 0.8)
                else:
                    m, x0 = self._fit_line(beam_img)

                if m is None:
                    logging.warning("Beam too weak. Continuing...")
                    continue

                if np.abs(m) > 0.8:
                    logging.warning("Beam gradient to high. Continuing...")
                    continue

                # save the calibration data
                calibration.x0[i] = x0
                calibration.m[i] = m

                self.state["calibration"]["x0"][i] = x0
                self.state["calibration"]["m"][i] = m

                # visualize the result
                if save_debug_images:
                    y_start = 0
                    y_end = yb

                    x_start = x0 + m * y_start
                    x_end = x0 + m * y_end

                    rgb = cv2.cvtColor(beam_img, cv2.COLOR_GRAY2RGB)
                    rgb = cv2.line(
                        rgb,
                        (int(x_start), int(y_start)),
                        (int(x_end), int(y_end)),
                        (255, 255, 0),
                        1,
                    )

                    cv2.imwrite(f"cap_laser_{i}_line.jpg", rgb)

                break

            self.laser_array.set_all(0)
            time.sleep(0.2)

        # STEP 3: store the fitted line data
        self.laser_array.set_all(0)
        time.sleep(1)

        # restore the previous laser state
        self.laser_array.pop_state()

        logging.info("Calibration complete")

        self.calibration = calibration
        self.state["current_index"] = None

        return calibration

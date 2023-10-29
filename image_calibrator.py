from dataclasses import dataclass
import time
import numpy as np
import cv2
import logging
import traceback
from .camera import Camera
from .laser_array import LaserArray

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


class ImageCalibrator:
    def __init__(self, laser_array: LaserArray, camera: Camera, config):
        self.laser_array = laser_array
        self.camera = camera
        self.config = config

    def _angle_to_ypos(self, angle: float):
        fov_y = np.radians(self.camera.config['fov'][1])
        height = self.camera.resolution[1]
        return angle / fov_y * height

    def _combined_capture(self, num_frames: int, interval: float, mode='avg'):
        result = self.camera.capture().astype(np.float32) / 255.0

        for _ in range(num_frames - 1):
            frame = self.camera.capture().astype(np.float32) / 255.0

            if mode == 'avg':
                result += frame
            elif mode == 'max':
                result = np.maximum(result, frame)

            time.sleep(interval)

        if mode == 'avg':
            result /= num_frames

        return result

    def _fit_line(self, img):
        # apply gaussian blur
        ksize = self.config['preblur']
        blurred = cv2.GaussianBlur(img, (ksize, ksize), 0)
        
        # get the brightes x coordinate of each row as point estimates
        b = np.max(blurred, axis=1)
        xs = np.argmax(blurred, axis=1)
        ys = np.arange(img.shape[0])

        # use the threshold mask as weights
        ws = b > self.config['threshold']

        # check if the minimum coverage is met
        if np.sum(ws) / img.shape[0] < self.config['min_coverage']:
            raise Exception("Minimum coverage not met")

        # fit a line to the points (swap x and y because we want to fit a vertical line)
        return np.polyfit(y=xs, x=ys, deg=1, w=ws)

    def calibrate(self, save_debug_images=False):
        logging.info("Starting calibration")

        # store the laser state
        self.laser_array.push_state()

        # setup the static calibration data
        fov_y = np.radians(self.camera.config['fov'][1])
        mount_angle = np.radians(self.camera.config['mount_angle'])
        camera_bottom = np.pi / 2 - mount_angle - fov_y / 2
        camera_top = np.pi / 2 - mount_angle + fov_y / 2

        # calculate the position of the 0 and 90 degree mark in pixel space
        ya = self._angle_to_ypos(-camera_bottom)
        yb = self._angle_to_ypos(np.pi / 2 - camera_bottom)

        calibration = Calibration(
            ya=ya,
            yb=yb,
            x0=np.zeros(len(self.laser_array), dtype=np.float32),
            m=np.zeros(len(self.laser_array), dtype=np.float32))

        # STEP 1: capture the base image
        logging.info("Capturing base image")
        self.laser_array.set_all(0)

        base_img = self._combined_capture(10, 0.1, mode='max')

        if save_debug_images:
            cv2.imwrite('cap_base.jpg', (base_img * 255).astype(np.uint8))

        # STEP 2: fit a line to each individual laser's beam path
        i = 0
        while i < len(self.laser_array):
            beam_img = np.zeros_like(base_img)

            try:
                logging.info(f"Capturing laser {i}")
                self.laser_array[i] = 127

                # capture the laser beam and subtract the base image
                logging.debug("Start capture")
                beam_img = np.maximum(self._combined_capture(30, 0, mode='max'), beam_img)
                beam_img = np.clip(beam_img - base_img, 0, 1)

                # convert to uint8
                beam_img = (beam_img * 255).astype(np.uint8)

                if save_debug_images:
                    cv2.imwrite(f'cap_laser_{i}.jpg', beam_img)

                # fit a line to the laser beam
                logging.debug("Fitting line")
                m, x0 = self._fit_line(beam_img)

                if np.abs(m) > 0.8:
                    logging.warning(f"Calibration failed. Retrying...")
                    continue

                # save the calibration data
                calibration.x0[i] = x0
                calibration.m[i] = m

                # visualize the result
                if save_debug_images:
                    y_start = 0
                    y_end = yb

                    x_start = x0 + m * y_start
                    x_end = x0 + m * y_end

                    rgb = cv2.cvtColor(beam_img, cv2.COLOR_GRAY2RGB)
                    rgb = cv2.line(rgb,
                        (int(x_start), int(y_start)),
                        (int(x_end), int(y_end)),
                        (255, 255, 0),
                        1)

                    cv2.imwrite(f'cap_laser_{i}_line.jpg', rgb)

                i += 1

                self.laser_array.set_all(0)

            except Exception as e:
                traceback.print_exc()
                logging.warning(f"Calibration failed. Retrying...")

        # STEP 3: store the fitted line data
        self.laser_array.set_all(0)
        time.sleep(1)

        # restore the previous laser state
        self.laser_array.pop_state()

        logging.info("Calibration complete")
        return calibration

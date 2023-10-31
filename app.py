from enum import Enum
import logging
from .ipc import IPCController
from .laser_array import LaserArray
from .camera import Camera
from .image_calibrator import ImageCalibrator
from .image_processor import ImageProcessor


class LaserHarpApp:
    class State(Enum):
        IDLE = 0
        STARTING = 1
        RUNNING = 2
        CALIBRATING = 3
        STOPPING = 4

    def _state_change(self, origin_states: list[State], target_state: State):
        if self.state not in origin_states:
            raise RuntimeError(f"Invalid state: {self.state}")

        logging.debug(f"App state change: {self.state} -> {target_state}")
        self.state = target_state

    def __init__(self, config: dict):
        self.config = config

        # setup all components
        self.ipc = IPCController(self.config['ipc'])
        self.laser_array = LaserArray(self.ipc, self.config['laser_array'])
        self.camera = Camera(self.config['camera'])
        self.calibrator = ImageCalibrator(self.laser_array, self.camera, self.config['image_calibrator'])
        self.processor = ImageProcessor(self.laser_array, self.camera, self.config['image_processor'])

        self.camera.on('frame', self._on_frame)

        self.state = self.State.IDLE

    def start(self, force_calibration=False):
        self._state_change([self.State.IDLE], self.State.STARTING)

        # start all components
        logging.info("Starting components...")
        self.ipc.start()
        self.camera.start()

        # load the calibration
        logging.info("Loading calibration...")
        success = self.calibrator.load()
        if not success or force_calibration:
            self.run_calibration()

        # enable all lasers
        self.laser_array.set_all(127)

        self._state_change([self.State.STARTING], self.State.RUNNING)

    def stop(self):
        self._state_change([self.State.RUNNING], self.State.STOPPING)

        # stop all components
        self.camera.stop()
        self.ipc.stop()

        self._state_change([self.State.STOPPING], self.State.IDLE)

    def _on_frame(self, frame):
        # skip if not running
        if self.state != self.State.RUNNING:
            return

        # invoke the image processor
        result = self.processor.process(frame)

    def run_calibration(self):
        prev_state = self.state
        self._state_change([self.State.RUNNING, self.State.STARTING], self.State.CALIBRATING)

        # run the calibrator
        calibration = self.calibrator.calibrate()
        self.calibrator.save()

        # update the processor
        self.processor.set_calibration(calibration)

        self._state_change([self.State.CALIBRATING], prev_state)

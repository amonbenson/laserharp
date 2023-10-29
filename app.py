from enum import Enum
from .ipc import IPCController
from .laser_array import LaserArray
from .camera import Camera
from .image_calibrator import ImageCalibrator
from .image_processor import ImageProcessor


class LaserHarpApp:
    def State(Enum):
        IDLE = 0
        STARTING = 1
        RUNNING = 2
        CALIBRATING = 3
        STOPPING = 4

    def __init__(self, config: dict):
        self.config = config

        # setup all components
        self.ipc = IPCController(self.config['ipc'])
        self.laser_array = LaserArray(self.ipc, self.config['laser_array'])
        self.camera = Camera(self.config['camera'])
        self.image_calibrator = ImageCalibrator(self.laser_array, self.camera, self.config['image_calibrator'])
        self.image_processor = ImageProcessor(self.laser_array, self.camera, self.config['image_processor'])

        self.camera.on('frame', self._on_frame)

        self.state = self.State.IDLE

    def start(self, force_recalibration=False):
        self.ipc.start()
        self.camera.start()

        # load the calibration
        result = self.image_calibrator.load()
        if not result or force_recalibration:
            self.perform_calibration()

        # enable all lasers
        self.laser_array.set_all(127)

    def stop(self):
        self.camera.stop()
        self.ipc.stop()

    def _on_frame(self, frame):
        # invoke the image processor
        result = self.image_processor.process(frame)

    def perform_calibration():
        pass

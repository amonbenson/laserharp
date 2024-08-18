from enum import Enum
import logging
import threading
import time
from .events import EventEmitter
from .midi import MidiEvent
from .ipc import IPCController
from .laser_array import LaserArray
from .camera import Camera
from .image_calibrator import ImageCalibrator
from .image_processor import ImageProcessor


class LaserHarpApp(EventEmitter):
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
        self.emit("state", self.state)

    def __init__(self, config: dict):
        super().__init__()

        self.config = config

        # setup all components
        self.ipc = IPCController(self.config['ipc'])
        self.laser_array = LaserArray(self.ipc, self.config['laser_array'])
        self.camera = Camera(self.config['camera'])
        self.calibrator = ImageCalibrator(self.laser_array, self.camera, self.config['image_calibrator'])
        self.processor = ImageProcessor(self.laser_array, self.camera, self.config['image_processor'])

        # setup the ipc read process
        self.capture_thread = threading.Thread(target=self._capture_thread, daemon=True)
        # self.ipc_read_thread = threading.Thread(target=self._ipc_read_process, daemon=True)

        self._frame_rate = None
        self._frame_last_update = time.time()
        self.frame_emit_rate = 10
        self._frame_emit_last_update = time.time()

        self.state = self.State.IDLE
        self.emit("state", self.state)
        self.emit("calibration", self.calibrator.calibration)

    def start(self, force_calibration=False):
        self._state_change([self.State.IDLE], self.State.STARTING)

        # start all components
        logging.info("Starting components...")
        self.ipc.start()
        self.camera.start()

        # start all threads
        logging.info("Starting threads...")
        self.capture_thread.start()
        # self.ipc_read_process.start()

        # load the calibration
        logging.info("Loading calibration...")
        if self.calibrator.load() and not force_calibration:
            # use the loaded calibration
            self.processor.set_calibration(self.calibrator.calibration)
            self.emit("calibration", self.calibrator.calibration)
        else:
            # run a new calibration
            self.run_calibration()

        # enable all lasers
        self.laser_array.set_all(127)

        self._state_change([self.State.STARTING], self.State.RUNNING)

    def stop(self):
        self._state_change([self.State.RUNNING], self.State.STOPPING)

        # disable all lasers
        self.laser_array.set_all(0)

        # stop all threads
        self.capture_thread.join(timeout=1)
        # self.ipc_read_process.join(timeout=1)
        # self.ipc_read_process.terminate()

        # stop all components
        self.camera.stop()
        self.ipc.stop()

        self._state_change([self.State.STOPPING], self.State.IDLE)

    """
    def _ipc_read_process(self):
        while self.state != self.State.IDLE:
            # read the next event
            event = self.ipc.read()
            if event is None:
                continue

            # process the event
            self._handle_midi_event(event)
    """

    def _capture_thread(self):
        while self.state != self.State.IDLE:
            # stop if the camera is not running anymore
            if self.camera.state != Camera.State.RUNNING:
                break

            # capture the next frame
            frame = self.camera.capture()

            # emit at a lower rate
            t = time.time()
            emit_enabled = t - self._frame_emit_last_update >= 1 / self.frame_emit_rate
            if emit_enabled:
                self._frame_emit_last_update = t

            # calculate capture rate
            new_framerate = 1 / (t - self._frame_last_update)
            self._frame_rate = new_framerate * 0.5 + self._frame_rate * 0.5 if self._frame_rate is not None else new_framerate
            self._frame_last_update = t
            if emit_enabled:
                self.emit("frame_rate", self._frame_rate)

            if emit_enabled:
                self.emit("frame", frame)

            # invoke the image processor
            result = self.processor.process(frame)
            
            if emit_enabled:
                self.emit("result", result)

            # TODO: generate midi data

    def _note_to_laser(self, note: int):
        if note == 127: return 127
        else: return note - self.config['root_note']

    def _laser_to_note(self, index: int):
        if index == 127: return 127
        else: return index + self.config['root_note']

    def _handle_midi_event(self, event: MidiEvent):
        # handle midi note on/off messages from any interface
        if event.message.type == 'note_on':
            index = self._note_to_laser(event.message.note)
            brightness = event.message.velocity
        elif event.message.type == 'note_off':
            index = self._note_to_laser(event.message.note)
            brightness = 0
        else:
            logging.warning(f"Unhandled midi event: {event}")
            return

        # set the laser brightness (this will send an IPC packet to the STM)
        if index <= len(self.laser_array):
            self.laser_array[index] = brightness
        elif index == 127:
            self.laser_array.set_all(brightness)
        else:
            logging.warning(f"Midi note out of range: {index}")
            return

    def run_calibration(self):
        prev_state = self.state
        self._state_change([self.State.RUNNING, self.State.STARTING], self.State.CALIBRATING)

        # run the calibrator
        calibration = self.calibrator.calibrate(save_debug_images=self.config['save_debug_images'])
        self.calibrator.save()

        # update the processor
        self.processor.set_calibration(calibration)
        self.emit("calibration", self.calibrator.calibration)

        self._state_change([self.State.CALIBRATING], prev_state)

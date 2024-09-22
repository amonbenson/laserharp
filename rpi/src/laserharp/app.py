import logging
import threading
import time
import numpy as np
from perci import reactive, ReactiveDictNode
import cv2
from .midi import MidiEvent
from .ipc import IPCController
from .din_midi import DinMidi
from .laser_array import LaserArray
from .camera import Camera
from .image_calibrator import ImageCalibrator
from .image_processor import ImageProcessor
from .midi_converter import MidiConverter
from .component import Component
from .settings import SettingsManager


class LaserHarpApp(Component):
    def __init__(self, config: dict):
        self._component_names = ["app", "ipc", "din_midi", "laser_array", "camera", "image_processor", "image_calibrator", "midi_converter"]
        self._global_state = reactive({name: {"config": config[name]} for name in self._component_names})

        super().__init__("app", self._global_state)

        # setup the settings manager
        self.settings = SettingsManager(self._global_state)
        self.settings.setup()

        # setup all components
        self.ipc = IPCController("ipc", self._global_state)
        self.din_midi = DinMidi("din_midi", self._global_state)
        self.laser_array = LaserArray("laser_array", self._global_state, self.ipc)
        self.camera = Camera("camera", self._global_state)
        self.calibrator = ImageCalibrator("image_calibrator", self._global_state, self.laser_array, self.camera)
        self.processor = ImageProcessor("image_processor", self._global_state, self.laser_array, self.camera)
        self.midi_converter = MidiConverter("midi_converter", self._global_state, self.laser_array, self.din_midi)

        # setup all processing threads
        self._capture_thread = threading.Thread(target=self._capture_thread_run, daemon=True)
        self._calibrate_thread = threading.Thread(target=self._calibrate_thread_run, daemon=True)
        self._ipc_read_thread = threading.Thread(target=self._ipc_read_thread_run, daemon=True)
        self._din_midi_read_thread = threading.Thread(target=self._din_midi_read_thread_run, daemon=True)

        self._calibration_request = False

        self._prev_result = None
        self._prev_pitch_bend = 8192

        self.state["status"] = "stopped"

    def _status_change(self, origin_states: list[str], target_status: str):
        if self.state["status"] not in origin_states:
            raise RuntimeError(f"Invalid state: {self.state['status']}")

        logging.debug(f"App state change: {self.state['status']} -> {target_status}")
        self.state["status"] = target_status

    def get_global_state(self) -> ReactiveDictNode:
        return self._global_state

    def get_settings(self) -> SettingsManager:
        return self.settings

    def start(self, force_calibration=False):
        self._status_change(["stopped"], "starting")

        # start all components
        logging.info("Starting components...")
        self.ipc.start()
        self.din_midi.start()
        self.laser_array.start()
        self.camera.start()
        self.calibrator.start()
        self.processor.start()

        # start all threads
        logging.info("Starting threads...")
        self._capture_thread.start()
        # self.ipc_read_thread.start()
        self._din_midi_read_thread.start()

        # load the calibration
        logging.info("Loading calibration...")
        if self.calibrator.load() and not force_calibration:
            # use the loaded calibration
            self.processor.set_calibration(self.calibrator.calibration)
        else:
            # run a new calibration
            self.run_calibration()

        # enable all lasers
        self.laser_array.set_all(127)

        self._status_change(["starting"], "running")

        # start the calibration thread. If a calibration should be performed, this will take over now
        self._calibrate_thread.start()

    def stop(self):
        self._status_change(["running"], "stopping")

        # disable all lasers
        self.laser_array.set_all(0)

        # stop all threads
        self._capture_thread.join(timeout=1)
        # self.ipc_read_thread.join(timeout=1)
        self._din_midi_read_thread.join(timeout=1)

        # stop all components
        self.processor.stop()
        self.calibrator.stop()
        self.camera.stop()
        self.laser_array.stop()
        self.din_midi.stop()
        self.ipc.stop()

        self._status_change(["stopping"], "stopped")

    def _calibrate_thread_run(self):
        while self.state["status"] != "stopping":
            # wait for a calibration request
            if not self._calibration_request:
                time.sleep(1)
                continue

            self._calibration_request = False

            prev_status = self.state["status"]
            self._status_change(["starting", "running"], "calibrating")

            # run the calibrator
            calibration = self.calibrator.calibrate(save_debug_images=self.config["save_debug_images"])
            self.calibrator.save()

            # update the processor
            self.processor.set_calibration(calibration)

            self._status_change(["calibrating"], prev_status)

    def _capture_thread_run(self):
        while self.state["status"] != "stopping":
            # wait if we are currently starting up or calibrating
            if self.state["status"] in ("starting", "calibrating"):
                time.sleep(0.1)
                continue

            # stop if the app or camera is not running anymore
            if self.camera.state["status"] != "running":
                break

            # capture the next frame
            frame = self.camera.capture()

            # draw a random blob for testing
            if not self.camera.enabled and self.config["generate_debug_intersections"]:
                phi = self.camera.frame_count * 0.05
                px = int(frame.shape[1] / 2 + np.cos(phi) * frame.shape[0] * 0.3)
                py = int(frame.shape[0] / 2 + np.sin(phi) * frame.shape[0] * 0.3)
                cv2.circle(frame, (px, py), 60, (255, 255, 255), -1)

            # invoke the image processor
            result = self.processor.process(frame)

            # invoke the midi converter
            self.midi_converter.process(result)

            # # set the laser brightness
            # for i, active in enumerate(result.active):
            #     note = self._laser_to_note(i)
            #     note_on = active and not (self._prev_result and self._prev_result.active[i])
            #     note_off = not active and (self._prev_result and self._prev_result.active[i])

            #     if note_on:
            #         self.din_midi.send(MidiEvent(0, "note_on", note=note, velocity=127))
            #     elif note_off:
            #         self.din_midi.send(MidiEvent(0, "note_off", note=note))

            # # use the average modulation to send pitch bend
            # num_active = sum(result.active)
            # mod_sum = sum(result.modulation)
            # mod_avg = mod_sum / num_active if num_active > 0 else 0
            # pitch_bend = max(-8192, min(8191, int(mod_avg * 8192)))

            # if pitch_bend != self._prev_pitch_bend:
            #     self.din_midi.send(MidiEvent(0, "pitchwheel", pitch=pitch_bend))
            # self._prev_pitch_bend = pitch_bend

            # # self._midi_serial.flush()

            # self._prev_result = result

    def _ipc_read_thread_run(self):
        while self.state["status"] != "stopping":
            # read a message
            data = self.ipc.read_raw(timeout=0.5)
            if data is None:
                continue

            # TODO: handle the ipc message

    def _din_midi_read_thread_run(self):
        while self.state["status"] != "stopping":
            # read a message
            event = self.din_midi.read(timeout=0.5)
            if event is None:
                continue

            # TODO: handle the midi event

    def _note_to_laser(self, note: int):
        if note == 127:
            return 127

        return note - self.config["root_note"]

    def _laser_to_note(self, index: int):
        if index == 127:
            return 127

        return index + self.config["root_note"]

    def _handle_midi_event(self, event: MidiEvent):
        # handle midi note on/off messages from any interface
        if event.message.type == "note_on":
            index = self._note_to_laser(event.message.note)
            brightness = event.message.velocity
        elif event.message.type == "note_off":
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
        # notify the calibration thread
        self._calibration_request = True

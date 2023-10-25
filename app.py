import logging
import mido
import time
import numpy as np
import traceback
import yaml
import os
import cv2
from multiprocessing import Process, Lock
from enum import Enum
from .config import CONFIG
from .ipc import IPCController
from .camera import Camera, InterceptionEvent
from .midi import MidiEvent


CALIBRATION_FILE = os.path.join(os.path.dirname(__file__), 'calibration.yaml')


IPC_CN_DIN = 0
IPC_CN_USB = 1
IPC_CN_BLE = 2
IPC_CN_LASER_BRIGHTNESS = 3


class LaserHarpApp:
    class State(Enum):
        IDLE = 0
        RUNNING = 1
        CALIBRATING = 2

    def __init__(self):
        self.state = LaserHarpApp.State.IDLE
        self.state_lock = Lock()

        self.root_note = CONFIG['root_note']
        self.note_status = np.zeros(CONFIG['num_lasers'], dtype=np.uint8)

        # use hardware serial to interface with the STM
        self.ipc = IPCController('/dev/ttyS0', baudrate=115200)
        self.laser_state = np.ones(CONFIG['num_lasers'], dtype=np.uint8) * 127

        # setup camera interface
        self.camera = Camera()

        # setup processes
        self.ipc_proc = Process(target=self._ipc_loop)
        self.interception_proc = Process(target=self._interception_loop)

        self.calibration = None

    def send_din_midi(self, message: mido.Message):
        self.ipc.send(MidiEvent(IPC_CN_DIN, message))

    def send_usb_midi(self, message: mido.Message):
        self.ipc.send(MidiEvent(IPC_CN_USB, message))

    def send_ble_midi(self, message: mido.Message):
        # TODO: implement BLE
        pass

    def set_laser(self, index: int, brightness: int):
        self.laser_state[index] = brightness

        if CONFIG['laser_translation_table'] is not None:
            index = CONFIG['laser_translation_table'][index]
        self.ipc.send(MidiEvent(IPC_CN_LASER_BRIGHTNESS, mido.Message('control_change', control=index, value=brightness)))

    def set_all_lasers(self, brightness: int):
        self.laser_state[:] = brightness
        self.ipc.send(MidiEvent(IPC_CN_LASER_BRIGHTNESS, mido.Message('control_change', control=127, value=brightness)))

    def start(self, force_calibration=False):
        if self.state != LaserHarpApp.State.IDLE:
            raise RuntimeError("App was already started")

        with self.state_lock:
            self.state = LaserHarpApp.State.RUNNING

            # start all threads
            self.ipc_proc.start()
            self.interception_proc.start()

            # start the camera interface
            self.camera.start()

            # enable all lasers
            self.set_all_lasers(127)

            logging.info("App running")

        # load calibration data
        calibration_required = False

        if force_calibration:
            calibration_required = True
        else:
            try:
                self.load_calibration()
            except:
                logging.warning("No valid calibration data found. Starting new calibration...")
                calibration_required = True

        if calibration_required:
            self.calibrate()

        self.apply_calibration()

    def stop(self):
        if self.state != LaserHarpApp.State.RUNNING:
            raise RuntimeError("App is not running")

        with self.state_lock:
            self.state = LaserHarpApp.State.IDLE

            # stop all threads
            self.ipc_proc.terminate()
            self.ipc_proc.join(timeout=0.5)
            self.interception_proc.terminate()
            self.interception_proc.join(timeout=0.5)

            # stop the camera interface
            self.camera.stop()

            # stop IPC
            self.ipc.stop()

    def _interception_loop(self):
        while self.state != LaserHarpApp.State.IDLE:
            try:
                # wait if we're not running
                while self.state != LaserHarpApp.State.RUNNING:
                    time.sleep(0.1)

                # handle any incoming events
                event = self.camera.read(timeout=0.1)
                if event is None:
                    continue

                self._handle_interception_event(event)

            except Exception as e:
                traceback.print_exc()
                logging.warning(f"Unhandled exception in interception event loop: {e}")

    def _note_to_laser(self, note: int):
        if note == 127: return 127
        else: return note - self.root_note

    def _laser_to_note(self, index: int):
        if index == 127: return 127
        else: return index + self.root_note

    def _ipc_loop(self):
        while self.state != LaserHarpApp.State.IDLE:
            try:
                # wait if we're not running
                while self.state != LaserHarpApp.State.RUNNING:
                    time.sleep(0.1)

                event = self.ipc.read(timeout=0.1)
                if event is None:
                    continue

                # STM handles USB and DIN midi, so this is the only cable number we expect to receive
                if event.cable_number in [IPC_CN_DIN, IPC_CN_USB]:
                    self._handle_midi_event(event)
                else:
                    logging.warning(f"Unhandled IPC event: {event}")

            except Exception as e:
                traceback.print_exc()
                logging.warning(f"Unhandled exception in IPC event loop: {e}")

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
        if index <= CONFIG['num_lasers']:
            self.set_laser(index, brightness)
        elif index == 127:
            self.set_all_lasers(brightness)
        else:
            logging.warning(f"Midi note out of range: {index}")
            return

    def _handle_interception_event(self, event: InterceptionEvent):
        # set note status to 127 if the beamlength is not nan/inf
        new_note_status = np.where(np.isfinite(event.beamlength), 127, 0).astype(np.uint8)

        # send midi note on/off messages for each laser to all interfaces
        for i in range(CONFIG['num_lasers']):
            if new_note_status[i] != self.note_status[i]:
                cmd = 'note_on' if new_note_status[i] else 'note_off'
                note = self._laser_to_note(i)
                velocity = new_note_status[i]

                message = mido.Message(cmd, note=note, velocity=velocity)
                self.send_din_midi(message)
                self.send_usb_midi(message)
                self.send_ble_midi(message)

        # update note status
        np.copyto(self.note_status, new_note_status)

    def store_calibration(self):
        print(self.calibration)
        with open(CALIBRATION_FILE, 'w') as f:
            yaml.dump({
                'num_lasers': CONFIG['num_lasers'],
                'laser_translation_table': CONFIG['laser_translation_table'],
                'calibration': self.calibration
            }, f, indent=4)

    def load_calibration(self):
        with open(CALIBRATION_FILE, 'r') as f:
            calibration = yaml.safe_load(f)

        if calibration['num_lasers'] != CONFIG['num_lasers']:
            raise RuntimeError("Number of lasers does not match calibration file")

        if calibration['laser_translation_table'] != CONFIG['laser_translation_table']:
            raise RuntimeError("Laser translation table does not match calibration file")

        self.calibration = calibration['calibration']

    def apply_calibration(self):
        self.camera.set_calibration(**self.calibration)

    def _angle_to_ypos(self, angle: float):
        fov_y = np.radians(CONFIG['camera']['fov'][1])
        return angle / fov_y * self.camera.height

    def _combined_capture(self, num_frames: int, interval: float, mode='avg'):
        result = self.camera.capture(grayscale=True).astype(np.float32) / 255.0

        for i in range(num_frames - 1):
            frame = self.camera.capture(grayscale=True).astype(np.float32) / 255.0

            if mode == 'avg':
                result += frame
            elif mode == 'max':
                result = np.maximum(result, frame)

            time.sleep(interval)

        if mode == 'avg':
            result /= num_frames

        assert(result.shape[1] == self.camera.width)
        assert(result.shape[0] == self.camera.height)

        return result

    def _fit_line(self, img, min_coverage=0.3):
        # apply gaussian blue
        blurred = cv2.GaussianBlur(img, (17, 17), 0)
        
        # get the brightes x coordinate of each row as point estimates
        b = np.max(blurred, axis=1)
        xs = np.argmax(blurred, axis=1)
        ys = np.arange(img.shape[0])

        # weight each estimate by a threshold
        thresh = np.max(blurred) * 0.4
        ws = b > thresh

        # check if the minimum coverage is met
        if np.sum(ws) / img.shape[0] < min_coverage:
            raise RuntimeError("Minimum coverage not met")

        # fit a line to the points (swap x and y because we want to fit a vertical line)
        return np.polyfit(y=xs, x=ys, deg=1, w=ws)

    def calibrate(self):
        with self.state_lock:
            self.state = LaserHarpApp.State.CALIBRATING
            logging.info("Starting calibration")

            # save the laser state
            prev_laser_state = self.laser_state.copy()

            # setup the static calibration data
            fov_y = np.radians(CONFIG['camera']['fov'][1])
            mount_angle = np.radians(CONFIG['camera']['mount_angle'])
            camera_top = np.pi / 2 - mount_angle + fov_y / 2
            camera_bottom = np.pi / 2 - mount_angle - fov_y / 2

            # calculate the position of the 0 and 90 degree mark in pixel space
            ya = self._angle_to_ypos(-camera_bottom)
            yb = self._angle_to_ypos(np.pi / 2 - camera_bottom)

            calibration = {
                'ya': float(ya),
                'yb': float(yb),
                'x0': [],
                'm': []
            }

            # STEP 1: capture the base image
            logging.info("Capturing base image")
            self.set_all_lasers(0)

            base_img = self._combined_capture(10, 0.1, mode='max')
            cv2.imwrite('cap_base.jpg', (base_img * 255).astype(np.uint8))

            # STEP 2: fit a line to each individual laser's beam path
            i = 0
            while i < CONFIG['num_lasers']:

                beam_img = np.zeros_like(base_img)

                try:
                    logging.info(f"Capturing laser {i}")
                    self.set_laser(i, 127)

                    # capture the laser beam and subtract the base image
                    logging.debug("Start capture")
                    beam_img = np.maximum(self._combined_capture(30, 0, mode='max'), beam_img)
                    beam_img = np.clip(beam_img - base_img, 0, 1)

                    # convert to uint8
                    beam_img = (beam_img * 255).astype(np.uint8)
                    cv2.imwrite(f'cap_laser_{i}.jpg', beam_img)

                    # fit a line to the laser beam
                    logging.debug("Fitting line")
                    m, x0 = self._fit_line(beam_img)

                    if np.abs(m) > 0.8:
                        logging.warning(f"Calibration failed. Retrying...")
                        continue

                    # save the calibration data
                    calibration['x0'].append(float(x0))
                    calibration['m'].append(float(m))

                    # visualize the result
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

                    self.set_all_lasers(0)

                except Exception as e:
                    traceback.print_exc()
                    logging.warning(f"Calibration failed. Retrying...")

            # STEP 3: store the fitted line data
            self.set_all_lasers(0)
            time.sleep(1)

            # store the calibration data
            self.calibration = calibration
            self.store_calibration()

            # restore the previous laser state
            for i, brightness in enumerate(prev_laser_state):
                self.set_laser(i, brightness)

            # return to running state
            self.state = LaserHarpApp.State.RUNNING
            logging.info("Calibration complete")

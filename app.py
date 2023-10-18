import logging
import mido
import time
import numpy as np
import traceback
import cv2
from multiprocessing import Process, Lock
from enum import Enum
from .ipc import IPCController
from .camera import Camera, InterceptionEvent
from .midi import MidiEvent


NUM_LASERS = 2
LASER_TRANSLATION_TABLE = np.array([11, 12])

CAMERA_FRAMERATE = 60

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

        self.note_status = np.zeros(NUM_LASERS, dtype=np.uint8)

        # use hardware serial to interface with the STM
        self.ipc = IPCController('/dev/ttyS0', baudrate=115200)
        self.laser_state = np.ones(NUM_LASERS, dtype=np.uint8) * 127

        # setup camera interface
        self.camera = Camera(framerate=CAMERA_FRAMERATE, N_beams=NUM_LASERS)

        # setup processes
        self.ipc_proc = Process(target=self._ipc_loop)
        self.interception_proc = Process(target=self._interception_loop)

    def send_din_midi(self, message: mido.Message):
        self.ipc.send(MidiEvent(IPC_CN_DIN, message))

    def send_usb_midi(self, message: mido.Message):
        self.ipc.send(MidiEvent(IPC_CN_USB, message))

    def send_ble_midi(self, message: mido.Message):
        # TODO: implement BLE
        pass

    def set_laser(self, index: int, brightness: int):
        self.laser_state[index] = brightness

        if LASER_TRANSLATION_TABLE is not None:
            index = LASER_TRANSLATION_TABLE[index]
        self.ipc.send(MidiEvent(IPC_CN_LASER_BRIGHTNESS, mido.Message('control_change', control=index, value=brightness)))

    def set_all_lasers(self, brightness: int):
        self.laser_state[:] = brightness
        self.ipc.send(MidiEvent(IPC_CN_LASER_BRIGHTNESS, mido.Message('control_change', control=127, value=brightness)))

    def start(self):
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
            index = event.message.note
            brightness = event.message.velocity
        elif event.message.type == 'note_off':
            index = event.message.note
            brightness = 0
        else:
            logging.warning(f"Unhandled midi event: {event}")
            return

        # set the laser brightness (this will send an IPC packet to the STM)
        if index <= NUM_LASERS:
            self.set_laser(index, brightness)
        elif index == 127:
            self.set_all_lasers(brightness)
        else:
            logging.warning(f"Midi note out of range: {index}")
            return

    def _handle_interception_event(self, event: InterceptionEvent):
        #print(event.beamlength)

        # set note status to 127 if the beamlength is not nan/inf
        new_note_status = np.where(np.isfinite(event.beamlength), 127, 0).astype(np.uint8)

        # send midi note on/off messages for each laser to all interfaces
        for i in range(NUM_LASERS):
            if new_note_status[i] != self.note_status[i]:
                cmd = 'note_on' if new_note_status[i] else 'note_off'
                note = i
                velocity = new_note_status[i]

                message = mido.Message(cmd, note=note, velocity=velocity)
                self.send_din_midi(message)
                self.send_usb_midi(message)
                self.send_ble_midi(message)

        # update note status
        np.copyto(self.note_status, new_note_status)

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

        return result

    def calibrate(self):
        with self.state_lock:
            self.state = LaserHarpApp.State.CALIBRATING
            logging.info("Starting calibration")

            # save the laser state
            prev_laser_state = self.laser_state.copy()

            # STEP 1: capture the base image
            logging.info("Capturing base image")
            self.set_all_lasers(0)
            time.sleep(1)

            base_img = self._combined_capture(10, 0.1, mode='max')
            cv2.imwrite('cap_base.jpg', (base_img * 255).astype(np.uint8))

            # STEP 2: capture each laser individually
            i = 0
            while i < NUM_LASERS:
                try:
                    logging.info(f"Capturing laser {i}")
                    self.set_laser(i, 127)
                    time.sleep(1)

                    # capture the laser beam and subtract the base image
                    beam_img = self._combined_capture(30, 0.1, mode='max')
                    beam_img = np.clip(beam_img - base_img, 0, 1)

                    # fit a line to the laser beam
                    beam_img = (beam_img * 255).astype(np.uint8)
                    _, thresh = cv2.threshold(beam_img, 127, 255, cv2.THRESH_BINARY)
                    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                    cnt = contours[0]
                    [vx, vy, x, y] = cv2.fitLine(cnt, cv2.DIST_L2, 0, 0.01, 0.01)

                    if np.abs(vx / vy) > 0.1:
                        logging.warning(f"Calibration failed. Retrying...")
                        continue

                    # visualize the beam
                    yl = int((-x * vy / vx) + y)
                    yr = int(((beam_img.shape[1] - x) * vy / vx) + y)

                    rgb = cv2.cvtColor(beam_img, cv2.COLOR_GRAY2RGB)
                    cv2.line(rgb, (0, yl), (beam_img.shape[1], yr), (0, 0, 255), 2)
                    cv2.imwrite(f'cap_laser_{i}.jpg', rgb)

                    i += 1

                    self.set_all_lasers(0)
                    time.sleep(0.5)

                except Exception as e:
                    traceback.print_exc()
                    logging.warning(f"Calibration failed. Retrying...")

            # restore the previous laser state
            for i, brightness in enumerate(prev_laser_state):
                self.set_laser(i, brightness)

            # return to running state
            self.state = LaserHarpApp.State.RUNNING
            logging.info("Calibration complete")

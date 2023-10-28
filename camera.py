from multiprocessing import Process, Array
import picamera
import numpy as np
import ctypes
from .events import EventEmitter


class Camera(EventEmitter):
    class StreamTarget(EventEmitter):
        def __init__(self, camera: 'Camera', frame_callback: callable):
            self.camera = camera
            self.frame_callback = frame_callback

            w, h = self.camera.resolution
            self._frame_buffer = Array(ctypes.c_uint8, w * h)

        @property
        def _frame(self):
            # return a numpy reference to the frame buffer (unsafe)
            w, h = self.camera.resolution
            return np.from_buffer(self._frame_buffer.get_obj(), dtype=np.uint8).reshape(h, w)

        def write(self, yuv_buffer):
            # convert the yuv buffer to a numpy array
            # convert to numpy array
            yuv = np.frombuffer(yuv_buffer, dtype=np.uint8)

            # extract the luminance component
            w, h = self.camera.resolution
            yuv = yuv.reshape((h * 3 // 2, w))
            frame = yuv[:h, :w]

            # call the frame handler
            self.frame_callback(frame)

            # store the frame
            with self._frame_buffer.get_lock():
                np.copyto(self._frame, frame)

        def get_frame(self):
            w, h = self.camera.resolution

            # copy the frame buffer
            with self._frame_buffer.get_lock():
                frame = self._frame.copy()

            return frame

    def __init__(self, config: dict):
        # setup camera
        self.picam = picamera.PiCamera()
        self.picam.resolution = self.config['resolution']
        self.picam.framerate = self.config['framerate']
        self.picam.rotation = self.config['rotation']

        # set manual exposure and white balance
        self.picam.shutter_speed = self.config['shutter_speed']
        self.picam.iso = self.config['iso']
        self.picam.exposure_mode = 'off'
        self.picam.awb_mode = 'off'
        self.picam.awb_gains = (1.5, 1.5)

        # image settings
        self.picam.brightness = self.config['brightness']
        self.picam.contrast = self.config['contrast']
        self.picam.saturation = self.config['saturation']
        self.picam.sharpness = self.config['sharpness']
        self.picam.exposure_compensation = 0
        self.picam.meter_mode = 'average'

        self.stream_target = self.StreamTarget(self, self._on_frame)

        self.capture_process = None
        self.running = False

    @property
    def resolution(self):
        return self.config['resolution']

    @property
    def framerate(self):
        return self.config['framerate']

    def _on_frame(self, frame):
        self.emit('frame', frame)

    def start(self):
        if self.running: return

        self.process = Process(target=self._capture_loop)
        self.process.start()
        self.running = True

    def stop(self):
        if not self.running: return

        self.running = False
        self.process.terminate(timeout=1)
        self.process.join()

    def _capture_loop(self):
        self.picam.start_recording(self.stream_target, format='yuv')

        # start capturing. For each frame, the stream target's write() method is called
        try:
            while self.running:
                self.picam.wait_recording(1)
        finally:
            self.picam.stop_recording()

    def capture(self, *kargs, **kwargs) -> np.ndarray:
        return self.stream_target.get_frame(*kargs, **kwargs)

    def close(self):
        self.picam.close()

import time
import threading
import picamera
import numpy as np


class Camera:
    class ImageProcessor:
        def __init__(self, resolution):
            self.resolution = resolution

            self.frame = None
            self.frame_lock = threading.Lock()
            self.frame_event = threading.Event()

        def write(self, buf):
            w, h = self.resolution

            # get a grayscale frame
            with self.frame_lock:
                # convert the YUV stream to a numpy array and extract the Y component
                self.frame = np.frombuffer(buf, dtype=np.uint8).reshape((h * 3 // 2, w))
                self.frame = self.frame[:h, :w]

                self.frame_event.set()

            # TODO: image processing

        def flush(self):
            # clear the event
            self.frame_event.clear()

        def get_frame_safe(self):
            # wait for a frame to be available
            self.frame_event.wait()

            # return a copy of the current frame
            with self.frame_lock:
                return self.frame.copy()

    def __init__(self):
        self.camera = picamera.PiCamera()
        self.camera.resolution = (640, 480) # VGA resolution
        self.camera.framerate = 60
        self.camera.rotation = 180
        self.thread = None
        self.running = False

        self.image_processor = self.ImageProcessor(resolution=self.camera.resolution)

    def start(self):
        if self.running: return

        self.thread = threading.Thread(target=self._capture_loop)
        self.thread.start()
        self.running = True

    def stop(self):
        if not self.running: return

        self.running = False
        self.thread.join()

    def _capture_loop(self):
        self.camera.start_recording(self.image_processor, format='yuv')

        # start capturing. For each frame, the image processor's write() method is called
        try:
            while self.running:
                self.camera.wait_recording(1)
        finally:
            self.camera.stop_recording()

    def capture(self) -> np.ndarray:
        return self.image_processor.get_frame_safe()

    def close(self):
        self.camera.close()

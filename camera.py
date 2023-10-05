import time
import threading
import picamera
import numpy as np
import cv2


class Camera:
    class ImageProcessor:
        def __init__(self, resolution: tuple, N_beams):
            self.resolution = resolution
            self.N_beams = N_beams

            self.beam_start = np.zeros((N_beams, 2), dtype=np.int32)
            self.beam_end = np.zeros((N_beams, 2), dtype=np.int32)

            self.status = np.full(N_beams, np.nan, dtype=np.float32)

            self.frame = None
            self.frame_lock = threading.Lock()
            self.frame_event = threading.Event()

            # initial calibration
            w, h = self.resolution
            xs = np.linspace(0, w - 1, N_beams, endpoint=True, dtype=np.int32)
            beam_start = np.stack((xs, np.zeros_like(xs)), axis=1)
            beam_end = np.stack((xs, np.full_like(xs, h - 1)), axis=1)
            self.calibrate(beam_start, beam_end)

        def calibrate(self, beam_start, beam_end):
            # assert x in ascending order for both arrays
            assert(np.all(np.diff(beam_start[:, 0]) > 0))
            assert(np.all(np.diff(beam_end[:, 0]) > 0))

            # assert end y > start y for each beam
            assert(np.all(beam_end[:, 1] > beam_start[:, 1]))

            # store the calibration points
            np.copyto(self.beam_start, beam_start)
            np.copyto(self.beam_end, beam_end)

        def write(self, buf):
            w, h = self.resolution

            # get a grayscale frame
            with self.frame_lock:
                # convert the YUV stream to a numpy array and extract the Y component
                self.frame = np.frombuffer(buf, dtype=np.uint8).reshape((h * 3 // 2, w))
                self.frame = self.frame[:h, :w]

                self.frame_event.set()

            # TODO: vectorize this?
            new_status = np.full_like(self.status, np.nan)
            for i in range(self.N_beams):
                N_samples = self.beam_end[i, 1] - self.beam_start[i, 1] + 1
                xs = np.linspace(self.beam_start[i, 0], self.beam_end[i, 0], N_samples, endpoint=True, dtype=np.int32)
                ys = np.linspace(self.beam_start[i, 1], self.beam_end[i, 1], N_samples, endpoint=True, dtype=np.int32)
                vs = np.linspace(0, 1, N_samples, endpoint=True, dtype=np.float32)

                b_max = 0
                for x, y, v in zip(xs, ys, vs):
                    b = self.frame[y, x]
                    if b > b_max:
                        b_max = b
                        new_status[i] = v

            status_changed = np.any(self.status != new_status)
            self.status = new_status
            if status_changed:
                print(self.status[0])

        def flush(self):
            # clear the event
            self.frame_event.clear()

        def get_frame(self, *, draw_calibration: bool = False):
            # wait for a frame to be available
            self.frame_event.wait()

            # return a copy of the current frame
            with self.frame_lock:
                frame = self.frame.copy()

            # convert grayscale to bgr
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

            # draw a line for each beam span
            if draw_calibration:
                for i in range(self.N_beams):
                    cv2.line(frame, tuple(self.beam_start[i]), tuple(self.beam_end[i]), (0, 0, 255), 1)

            return frame

    def __init__(self):
        self.camera = picamera.PiCamera()
        self.camera.resolution = (640, 480) # VGA resolution
        self.camera.framerate = 60
        self.camera.rotation = 180
        self.thread = None
        self.running = False

        self.image_processor = self.ImageProcessor(
            resolution=self.camera.resolution,
            N_beams=1
        )

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

    def capture(self, *kargs, **kwargs) -> np.ndarray:
        return self.image_processor.get_frame(*kargs, **kwargs)

    def close(self):
        self.camera.close()

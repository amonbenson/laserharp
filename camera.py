import threading
import picamera
import numpy as np


class Camera:
    def __init__(self):
        self.camera = picamera.PiCamera()
        self.camera.resolution = (320, 240) # QVGA resolution
        self.camera.framerate = 60
        self.camera.rotation = 180
        self.thread = None
        self.running = False

    def start(self):
        if not self.running:
            self.thread = threading.Thread(target=self._capture_loop)
            self.thread.start()
            self.running = True

    def stop(self):
        if self.running:
            self.running = False
            self.thread.join()

    def _capture_loop(self):
        stream = picamera.PiCameraCircularIO(self.camera, seconds=10)
        self.camera.start_recording(stream, format='h264')
        try:
            while self.running:
                self.camera.wait_recording(0.1)
                # Get the current frame as a numpy array
                frame = np.frombuffer(stream.getvalue(), dtype=np.uint8)

                # Get the Y-component of the YUV stream
                frame = frame.reshape((int(self.camera.resolution[1] * 1.5), self.camera.resolution[0]))
                grayscale = frame[:self.camera.resolution[1], :self.camera.resolution[0]]

                x, y = 100, 100 # Example pixel position
                threshold = 128 # Example brightness threshold
                brightness = grayscale[y, x]
                print(brightness)

                if brightness > threshold:
                    pass
        finally:
            self.camera.stop_recording()
            stream.close()
            self.camera.close()

    def capture(self, filename):
        self.camera.capture(filename)

    def close(self):
        self.camera.close()

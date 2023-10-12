import subprocess
import multiprocessing


class BleMidi:
    def __init__(self):
        self._btmidi_server = None

    def start(self):
        # start the btmidi-server background process
        self._btmidi_server = subprocess.Popen(["btmidi-server"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def stop(self):
        # stop the btmidi-server background process
        self._btmidi_server.kill()

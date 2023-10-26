import unittest
from ..midi import MidiEvent
from ..laser_array import LaserArray


class DummyIPCController:
    def __init__(self):
        self.event = None

    def send(self, event: MidiEvent):
        self.event = event


class Test_LaserArray(unittest.TestCase):
    def setUp(self):
        config = {
            'ipc': {
                'cables': {
                    'laser_array': 3
                }
            },
            'laser_array': {
                'size': 3
            }
        }

        self.ipc = DummyIPCController()
        self.laser_array = LaserArray(config, self.ipc)

    def tearDown(self):
        pass

    def test_laser_array(self):
        pass

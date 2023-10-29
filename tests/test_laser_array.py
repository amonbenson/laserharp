import unittest
from ..laser_array import LaserArray
from ..midi import MidiEvent
from .mock import MockIPC


class Test_LaserArray(unittest.TestCase):
    def setUp(self):
        self.ipc = MockIPC(config={
            'cables': {
                'laser_array': 3
            }
        })

        self.laser_array = LaserArray(self.ipc, config={
            'size': 3,
            'laser_translation_table': [3, 4, 5]
        })

    def tearDown(self):
        pass

    def test_len(self):
        self.assertEqual(len(self.laser_array), 3)

    def test_set(self):
        self.laser_array.set(1, 64)

        # test if the state is correct
        self.assertEqual(self.laser_array[1], 64)

        # test if a message was sent
        self.assertEqual(self.ipc.event, MidiEvent('laser_array', 'control_change', control=4, value=64))

    def test_set_all(self):
        self.laser_array.set_all(101)

        # test if the state is correct
        self.assertEqual(self.laser_array[0], 101)
        self.assertEqual(self.laser_array[1], 101)
        self.assertEqual(self.laser_array[2], 101)

        # test if a message was sent
        self.assertEqual(self.ipc.event, MidiEvent('laser_array', 'control_change', control=127, value=101))

    def test_stack(self):
        self.laser_array.set(0, 64)
        self.laser_array.push_state()

        self.laser_array.set(0, 127)
        self.assertEqual(self.laser_array[0], 127)
        self.assertEqual(self.ipc.event, MidiEvent('laser_array', 'control_change', control=3, value=127))

        self.laser_array.pop_state()
        self.assertEqual(self.laser_array[0], 64)
        self.assertEqual(self.ipc.event, MidiEvent('laser_array', 'control_change', control=3, value=64))


if __name__ == '__main__':
    unittest.main()

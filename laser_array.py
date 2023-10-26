import numpy as np
import mido
from .ipc import IPCController
from .midi import MidiEvent


class LaserArray():
    def __init__(self, ipc: IPCController, **config):
        self.config = config
        self.ipc = ipc

        self._cn = config['ipc']['cables']['laser_array']

        self._state = np.zeros(config['size'], dtype=np.uint8)
        self._state_stack = []

    def __len__(self):
        return len(self._state)

    def __getitem__(self, key):
        return self._state[key]

    def __setitem__(self, key, value):
        self.set(key, value)

    def set(self, index: int, brightness: int):
        assert(0 <= index < len(self))
        assert(0 <= brightness <= 127)

        # return if nothing changed
        if self._state[index] == brightness:
            return

        self._state[index] = brightness

        # apply the translation table and send the message
        if self.config['laser_translation_table'] is not None:
            index = self.config['laser_translation_table'][index]
        self.ipc.send(MidiEvent(self._cn, mido.Message('control_change', control=index, value=brightness)))

    def set_all(self, brightness: int):
        self._state[:] = brightness

        # send a special message to set all lasers at once
        self.ipc.send(MidiEvent(self._cn, mido.Message('control_change', control=127, value=brightness)))

    def push_state(self):
        self._state_stack.append(self._state.copy())

    def pop_state(self):
        self._state = self._state_stack.pop()

        # update all lasers to this state
        for i, brightness in enumerate(self._state):
            self.set(i, brightness)

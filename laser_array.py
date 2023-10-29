import numpy as np
import mido
from .ipc import IPCController
from .midi import MidiEvent


class LaserArray():
    def __init__(self, ipc: IPCController, config: dict):
        self.config = config
        self.ipc = ipc

        self._state = np.zeros(self.config['size'], dtype=np.uint8)
        self._state_stack = []

    def __len__(self):
        return len(self._state)

    def __getitem__(self, key):
        return self._state[key]

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            if key == slice(None):
                # if all lasers are set, we can use the set_all method
                self.set_all(value)
            else:
                # set each laser individually
                for i in range(*key.indices(len(self))):
                    self.set(i, value)
        else:
            # set a single laser
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
        self.ipc.send(MidiEvent('laser_array', 'control_change', control=index, value=brightness))

    def set_all(self, brightness: int):
        self._state[:] = brightness

        # send a special message to set all lasers at once
        self.ipc.send(MidiEvent('laser_array', 'control_change', control=127, value=brightness))

    def push_state(self):
        self._state_stack.append(self._state.copy())

    def pop_state(self):
        state = self._state_stack.pop()

        # update all lasers to this state
        for i, brightness in enumerate(state):
            self.set(i, brightness)

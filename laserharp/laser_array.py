import time
import numpy as np
from .ipc import IPCController
from perci import ReactiveDictNode
from .component import Component


class LaserArray(Component):
    ANIMATIONS = ["boot", "flip", "test"]
    ANIMATION_FOLLOW_ACTIONS = ["loop", "freeze", "off", "restore"]

    def __init__(self, name: str, global_state: ReactiveDictNode, ipc: IPCController):
        super().__init__(name, global_state)

        self.ipc = ipc

        self._size = self.config["size"]

        if "translation_table" in self.config:
            self._translation_table = [int(i) for i in self.config["translation_table"]]
        else:
            self._translation_table = None

        self._laser_state = np.zeros(self._size, dtype=np.uint8)
        self._state_stack = []

    def __len__(self):
        return len(self._laser_state)

    def __getitem__(self, key):
        return self._laser_state[key]

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

    def set(self, index: int, brightness: int, fade_duration: float = 0.0):
        assert 0 <= index < len(self)
        assert 0 <= brightness <= 127

        # return if nothing changed
        if self._laser_state[index] == brightness:
            return

        self._laser_state[index] = brightness

        # apply the translation table and send the message
        if self._translation_table is not None:
            index = self._translation_table[index]
        self.ipc.send_raw(bytes([0x80, index, brightness, np.clip(int(fade_duration * 10), 0, 255)]))

    def set_all(self, brightness: int, fade_duration: float = 0.0):
        self._laser_state[:] = brightness

        # send a message to set all lasers at once
        self.ipc.send_raw(bytes([0x81, brightness, np.clip(int(fade_duration * 10), 0, 255), 0x00]))

    def push_state(self):
        self._state_stack.append(self._laser_state.copy())

    def pop_state(self):
        state = self._state_stack.pop()

        # update all lasers to this state
        for i, brightness in enumerate(state):
            self.set(i, brightness)

    def play_animation(self, animation: str, duration: float = 1.0, follow_action: str = "loop", *, blocking=False):
        animation_id = self.ANIMATIONS.index(animation)
        if animation_id == -1:
            raise ValueError(f"Unknown animation: {animation}")

        duration_byte = np.clip(int(duration * 10), 0, 255)

        follow_action_id = self.ANIMATION_FOLLOW_ACTIONS.index(follow_action)
        if follow_action_id == -1:
            raise ValueError(f"Unknown follow action: {follow_action}")

        self.ipc.send_raw(bytes([0x83, animation_id, duration_byte, follow_action_id]))

        if blocking:
            time.sleep(duration)

    def stop_animation(self):
        self.ipc.send_raw(bytes([0x84, 0x00, 0x00, 0x00]))

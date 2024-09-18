import numpy as np
from perci import ReactiveDictNode
from .component import Component
from .midi import MidiEvent
from .image_processor import ImageProcessor
from .laser_array import LaserArray
from .din_midi import DinMidi


class MidiConverter(Component):
    NUM_SECTIONS = 3

    def __init__(self, name: str, global_state: ReactiveDictNode, laser_array: LaserArray, din_midi: DinMidi):
        super().__init__(name, global_state)

        self._laser_array = laser_array
        self._din_midi = din_midi

        self._num_lasers = len(self._laser_array)

        # setup an array of shape (num_sections, num_lasers) to keep track of which lasers are active
        self.state["active"] = [[False] * self._num_lasers for _ in range(self.NUM_SECTIONS)]

    def start(self):
        pass

    def stop(self):
        pass

    def _is_in_section(self, section: int, length: float) -> bool:
        bounds = self.config["sections"]["bounds"]
        start = bounds[section]
        end = bounds[section + 1] if section < len(bounds) - 1 else np.inf

        return start <= length < end

    def process(self, interceptions: ImageProcessor.Result):
        for x in range(self._num_lasers):
            active = interceptions.active[x]
            length = interceptions.length[x]
            _modulation = interceptions.modulation[x]

            for y in range(self.NUM_SECTIONS):
                note_active = active and self._is_in_section(y, length)

                # skip if the note does not need to be updated
                if self.state["active"][y][x] == note_active:
                    continue

                note = self.config["root_note"] + y * self.config["section"]["octave_spacing"] * 12

                # send the note on/off message
                if note_active:
                    pass
                else:
                    pass

                # set the new state
                self.state["active"][y][x] = note_active

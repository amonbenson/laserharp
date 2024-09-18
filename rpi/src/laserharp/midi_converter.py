import numpy as np
from perci import ReactiveDictNode
from .component import Component
from .midi import MidiEvent
from .image_processor import ImageProcessor
from .laser_array import LaserArray
from .din_midi import DinMidi


class MidiConverter(Component):
    NUM_SECTIONS = 3
    MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]
    STEP_NAMES = ["c", "d", "e", "f", "g", "a", "b"]

    def __init__(self, name: str, global_state: ReactiveDictNode, laser_array: LaserArray, din_midi: DinMidi):
        super().__init__(name, global_state)

        self._laser_array = laser_array
        self._din_midi = din_midi

        # setup an array of shape (num_sections, num_lasers) to keep track of which lasers are active
        self.state["active"] = [[False] * len(self._laser_array) for _ in range(self.NUM_SECTIONS)]

    def start(self):
        pass

    def stop(self):
        pass

    def _is_in_section(self, section: int, length: float) -> bool:
        start = self.settings["section_start_" + str(section)]
        end = self.settings.get("section_start_" + str(section + 1), np.inf)

        return start <= length < end

    def _apply_scale(self, step: int) -> int:
        step = step % len(self.MAJOR_SCALE)
        step_name = self.STEP_NAMES[step]

        # apply major scale
        note = self.MAJOR_SCALE[step]

        # apply alterations from the pedal positions
        note += self.settings["pedal_position_" + step_name]

        return note

    def process(self, interceptions: ImageProcessor.Result):
        for x in range(len(self._laser_array)):
            active = bool(interceptions.active[x])
            length = float(interceptions.length[x])
            _modulation = float(interceptions.modulation[x])

            # use the diode index x as the step position and apply the current scale
            note_offset = self._apply_scale(x)

            for y in range(self.NUM_SECTIONS):
                note_active = active and self._is_in_section(y, length)

                # skip if the note does not need to be updated
                if self.state["active"][y][x] == note_active:
                    continue

                # calculate the midi note
                note = self.settings["root_note"]
                note += y * self.settings["section_octave_spacing"] * 12
                note += note_offset

                # send the note on/off message
                if note_active:
                    self._din_midi.send(MidiEvent(0, "note_on", note=note, velocity=127))
                else:
                    self._din_midi.send(MidiEvent(0, "note_off", note=note))

                # set the new state
                self.state["active"][y][x] = note_active

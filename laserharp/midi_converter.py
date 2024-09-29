import numpy as np
from perci import ReactiveDictNode
from .component import Component
from .midi import MidiEvent
from .image_processor import ImageProcessor
from .laser_array import LaserArray
from .din_midi import DinMidi


class MidiConverter(Component):
    NUM_SECTIONS = 3
    MAJOR_SCALE_NOTES = [0, 2, 4, 5, 7, 9, 11]

    def __init__(self, name: str, global_state: ReactiveDictNode, laser_array: LaserArray, din_midi: DinMidi):
        super().__init__(name, global_state)

        self._laser_array = laser_array
        self._din_midi = din_midi

        # setup an array of shape (num_sections, num_lasers) to keep track of which lasers are active
        self._prev_beam_acive = [False] * len(self._laser_array)
        self.state["active"] = [[False] * len(self._laser_array) for _ in range(self.NUM_SECTIONS)]

        self._first_iteration = True

    def start(self):
        pass

    def stop(self):
        pass

    def _is_in_section(self, section: int, length: float) -> bool:
        start = self.settings["section_start_" + str(section)]
        end = self.settings.get("section_start_" + str(section + 1), np.inf)

        return start <= length < end

    def _apply_scale(self, step: int) -> int:
        octave = step // len(self.MAJOR_SCALE_NOTES)
        step = step % len(self.MAJOR_SCALE_NOTES)

        # apply major scale
        note = self.MAJOR_SCALE_NOTES[step]

        # apply alterations from the pedal positions
        note += self.settings[f"pedal_position_{step}"]

        # apply octave
        note += octave * 12

        return note

    def process(self, interceptions: ImageProcessor.Result):
        # set initial beam brightness
        if self._first_iteration:
            self._laser_array.set_all(self.settings["unplucked_beam_brightness"])
            self._first_iteration = False
            return

        for x in range(len(self._laser_array)):  # pylint: disable=consider-using-enumerate
            active = bool(interceptions.active[x])
            length = float(interceptions.length[x])
            _modulation = float(interceptions.modulation[x])

            # set the beam brightness
            if active and not self._prev_beam_acive[x]:
                self._laser_array[x] = self.settings["plucked_beam_brightness"]
            elif not active and self._prev_beam_acive[x]:
                self._laser_array[x] = self.settings["unplucked_beam_brightness"]
            self._prev_beam_acive[x] = active

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

                if note < 0:
                    note = 0
                elif note > 127:
                    note = 127

                # send the note on/off message
                if note_active:
                    self._din_midi.send(MidiEvent(0, "note_on", note=note, velocity=127))
                else:
                    self._din_midi.send(MidiEvent(0, "note_off", note=note))

                # set the new state
                self.state["active"][y][x] = note_active

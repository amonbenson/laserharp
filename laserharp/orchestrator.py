import logging
from typing import Any, Optional
import numpy as np
from perci import ReactiveDictNode, watch
from .component import Component
from .midi import MidiEvent
from .image_processor import ImageProcessor
from .laser_array import LaserArray
from .din_midi import DinMidi
from .scales import calculate_pedal_positions


class Orchestrator(Component):
    MAJOR_SCALE = np.array([0, 2, 4, 5, 7, 9, 11], dtype=np.uint8)  # map step -> note
    MAJOR_SCALE_INVERSE = np.array([0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6], dtype=np.uint8)  # map note -> step

    def __init__(self, name: str, global_state: ReactiveDictNode, laser_array: LaserArray, din_midi: DinMidi):
        super().__init__(name, global_state)

        self._laser_array = laser_array
        self._din_midi = din_midi

        # setup an array of shape (num_sections, num_lasers) to keep track of which lasers are active
        self.state["active"] = [[False] * len(self._laser_array)]

        self._intersections = np.inf * np.ones(len(self._laser_array), dtype=float)
        self._previous_velocities = np.zeros(128, dtype=np.uint8)
        self._previous_pitch_bend = 0

        self._note_lookup_table = -1 * np.ones(len(self._laser_array), dtype=np.int8)  # map step -> note
        self._note_lookup_table_reverse = -1 * np.ones(128, dtype=np.int8)  # map note -> step

        self._brightness_lookup_cache = -1 * np.ones(128, dtype=np.int8)
        self._emulated_lookup_cache = -1 * np.ones(128, dtype=np.int8)

        watch(self.settings.get_child("flipped"), lambda change: self._on_flipped_changed(change.value))

    def _update_lookup_tables(self):
        # reset tables
        self._note_lookup_table.fill(-1)
        self._note_lookup_table_reverse.fill(-1)

        # generate scale table
        indices = np.arange(7, dtype=np.int8)
        scale_table = np.mod(self.MAJOR_SCALE[np.mod(indices + 7 - self.MAJOR_SCALE_INVERSE[self.settings["key"]].astype(np.int8), 7)] + self.settings["key"], 12)
        assert len(scale_table) == 7

        for i in range(len(self._laser_array)):
            step = i + self.settings["mode"]
            octave = step // len(scale_table)
            step_within_octave = np.mod(step, len(scale_table))
            note = (self.settings["octave"] + octave) * 12 + scale_table[step_within_octave]
            # print(i, "->", note)

            # skip if note is out of bounds
            if not 0 < note <= 128:
                continue

            # use either normal or flipped laser index
            laser_index = len(self._laser_array) - i - 1 if self.settings["flipped"] else i

            # store both forward and reverse lookup
            self._note_lookup_table[laser_index] = note
            self._note_lookup_table_reverse[note] = laser_index

        # reset caches
        self._brightness_lookup_cache = -1 * np.ones(128, dtype=np.int8)
        self._emulated_lookup_cache = -1 * np.ones(128, dtype=np.int8)

    def _lookup_laser_index(self, note: int, on: bool, cache: Optional[np.ndarray] = None):
        if on:
            # lookup via the normal lookup table
            index = self._note_lookup_table_reverse[note]
            if cache is not None:
                cache[note] = index
        else:
            # lookup via the cache. If no entry exists, use the normal lookup table
            if cache is not None and cache[note] != -1:
                index = cache[note]
                cache[note] = -1
            else:
                index = self._note_lookup_table_reverse[note]

        return index

    def _on_flipped_changed(self, _: bool):
        # play flip animation
        self._laser_array.play_animation("flip", 0.5, "restore")

        # regenerate lookup tables
        self._update_lookup_tables()

    def start(self):
        # initialize the lookup tables
        self._update_lookup_tables()

        # light all lasers
        self._laser_array.set_all(127, 1.0)

        # release all notes
        for note in range(128):
            self._din_midi.send(MidiEvent(0, "note_off", note=note))

    def stop(self):
        # release all notes
        for note in range(128):
            self._din_midi.send(MidiEvent(0, "note_off", note=note))

    def flip(self):
        self.settings["flipped"] = not self.settings["flipped"]

    def handle_midi_event(self, event: MidiEvent):
        match event.message.type:
            case "note_on" | "note_off":
                note = event.message.note
                velocity = event.message.velocity if event.message.type == "note_on" else 0

                match event.message.channel:
                    case 0:  # brightness channel
                        index = self._lookup_laser_index(note, velocity > 0, self._brightness_lookup_cache)
                        if index == -1:
                            return

                        brightness = np.clip(velocity, self.settings["unplucked_beam_brightness"], 127)
                        self._laser_array.set(index, brightness)
                    case 1:  # config channel
                        if velocity == 0:
                            return

                        if 0 <= note < 12:
                            # set key
                            self.settings["key"] = note
                        elif 12 <= note < 24:
                            # set mode
                            self.settings["mode"] = int(self.MAJOR_SCALE_INVERSE[note - 12])
                        elif 24 <= note < 34:
                            # set octave
                            self.settings["octave"] = note - 24
                        elif note == 127:
                            # reset all
                            self.settings["key"] = 0
                            self.settings["octave"] = 4
                            self.settings["mode"] = 0

                            # TODO: reset caches, previous velocity and send panic (all notes off)

                        self._update_lookup_tables()

                    case 2:  # emulate channel
                        index = self._lookup_laser_index(note, velocity > 0, self._emulated_lookup_cache)
                        if index == -1:
                            return

                        self._intersections[index] = np.minimum(0.5, velocity * 0.01) if velocity > 0 else np.inf
            case _:
                return

    def process(self, intersections: ImageProcessor.Result, dt: float):
        # store intersection lengths. Use np.inf for inactive beams
        self._intersections = np.where(intersections.active, intersections.length, np.inf)

        # calculate new velocities and average modulation
        velocities = np.zeros(128, dtype=np.uint8)
        modulationSum = 0
        modulationContributors = 0

        for i in range(len(self._laser_array)):
            # convert laser index to note number
            note = self._note_lookup_table[i]
            if note == -1:
                continue

            # set the note
            if not np.isinf(self._intersections[i]):
                velocities[note] = 127

                modulationSum += intersections.modulation[i]
                modulationContributors += 1

        # compare with previous state to generate note on/off events
        for note in range(128):
            previous_velocity = self._previous_velocities[note]
            velocity = velocities[note]

            # send note off
            if velocity == 0 and previous_velocity > 0:
                self._din_midi.send(MidiEvent(0, "note_off", note=note))

            # send note on
            if velocity > 0 and previous_velocity == 0:
                self._din_midi.send(MidiEvent(0, "note_on", note=note, velocity=velocity))

        # store previous velocities
        self._previous_velocities = velocities

        # calculate pitch bend
        if modulationContributors > 0:
            modulation = modulationSum / modulationContributors
        else:
            modulation = 0

        pitch_bend = int(np.clip(modulation * 8192, -8192, 8191))  # pitch bend range is -8192 to 8191
        if pitch_bend != self._previous_pitch_bend:
            self._din_midi.send(MidiEvent(0, "pitchwheel", pitch=pitch_bend))
            self._previous_pitch_bend = pitch_bend

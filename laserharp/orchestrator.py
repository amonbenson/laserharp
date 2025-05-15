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

        self._previous_intersections = np.inf * np.ones(len(self._laser_array), dtype=float)
        self._intersections = np.inf * np.ones(len(self._laser_array), dtype=float)

        self._brightnesses = np.zeros(len(self._laser_array), dtype=np.uint8)
        self._previous_velocities = np.zeros(128, dtype=np.uint8)

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

            # store both forward and reverse lookup
            self._note_lookup_table[i] = note
            self._note_lookup_table_reverse[note] = i

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

    # def _on_scale_changed(self, scale: str):
    #     # apply the new scale
    #     if scale != "Custom":
    #         self.set_scale(scale)

    # def _on_pedal_or_mute_changed(self, _: Any):
    #     # set the selected scale name to "Custom" if the change did not originate from a scale change
    #     if not self._changing_scale:
    #         self.settings["selected_scale"] = "Custom"

    def start(self):
        # initialize lookup tables
        self._update_lookup_tables()

        # fade in the initial color
        self._update_brightnesses(fade_duration=0.5)

    def stop(self):
        # set all notes off
        # for note, _ in enumerate(self.state["velocities"]):
        #     self.state["velocities"][note] = 0
        pass

    def flip(self):
        self.settings["flipped"] = not self.settings["flipped"]

    # def set_scale(self, scale: str | int | list[int]):
    #     if isinstance(scale, str):
    #         # find pedal positions by name
    #         scale_obj = next((s for s in self.state["scale_pedal_positions"] if s["name"] == scale), None)
    #         if scale_obj is None:
    #             raise ValueError(f"Scale {scale} not found.")

    #         pedal_positions = scale_obj["pedal_positions"]

    #     elif isinstance(scale, int):
    #         # find scale by index
    #         pedal_positions = self.state["scale_pedal_positions"][scale]["pedal_positions"]

    #     elif isinstance(scale, list):
    #         # calculate pedal positions for custom scale
    #         pedal_positions = calculate_pedal_positions(scale)

    #     else:
    #         raise ValueError(f"Invalid scale type {type(scale)}.")

    #     # apply the new pedal positions
    #     self._changing_scale = True

    #     for i, position in enumerate(pedal_positions):
    #         self.settings[f"pedal_position_{i}"] = position if position is not None else 0
    #         self.settings[f"pedal_mute_{i}"] = position is None

    #     self._changing_scale = False

    # def _divide_cc_range(self, value: int, sections: int) -> int:
    #     return (value * sections) // 128

    def handle_midi_event(self, event: MidiEvent):
        # match event.message.type:
        #     case "control_change":
        #         # restore brightness immediately
        #         match event.message.control:
        #             case 102:
        #                 # restore brightness
        #                 self._brightness_reset_counter = 0
        #             case 103:
        #                 # set unpluckled brightness
        #                 self.settings["unplucked_beam_brightness"] = event.message.value
        #             case 104:
        #                 # set plucked brightness
        #                 self.settings["plucked_beam_brightness"] = event.message.value
        #             case 105:
        #                 # set muted brightness
        #                 self.settings["muted_beam_brightness"] = event.message.value
        #             case control if 110 <= control <= 116:
        #                 position = control - 110
        #                 match self._divide_cc_range(event.message.value, 4):
        #                     case 0:
        #                         # mute pedal
        #                         self.settings[f"pedal_position_{position}"] = 0
        #                         self.settings[f"pedal_mute_{position}"] = True
        #                     case 1:
        #                         # set pedal to sharp position
        #                         self.settings[f"pedal_position_{position}"] = 1
        #                         self.settings[f"pedal_mute_{position}"] = False
        #                     case 2:
        #                         # set pedal to natural position
        #                         self.settings[f"pedal_position_{position}"] = 0
        #                         self.settings[f"pedal_mute_{position}"] = False
        #                     case _:
        #                         # set pedal to flat position
        #                         self.settings[f"pedal_position_{position}"] = -1
        #                         self.settings[f"pedal_mute_{position}"] = False
        #             case _:
        #                 pass
        #     case "note_on":
        #         # set on color directly
        #         if event.message.note < len(self._laser_array):
        #             self._brightness_reset_counter = self.BRIGHTNESS_RESET_TICKS
        #             self._brightness_user[event.message.note] = event.message.velocity
        #     case "note_off":
        #         # schedule off color for the next update
        #         if event.message.note < len(self._laser_array):
        #             self._brightness_reset_counter = self.BRIGHTNESS_RESET_TICKS
        #             self._brightness_user_scheduled_off[event.message.note] = True
        #     case _:
        #         pass

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

    def _update_brightnesses(self, fade_duration: float = 0):
        for i in range(len(self._laser_array)):
            # if not np.isinf(self._intersections[i]):
            #     brightness = self.settings["plucked_beam_brightness"]
            # else:
            #     brightness = self.settings["unplucked_beam_brightness"]

            # if brightness != self._brightnesses[i]:
            #     self._laser_array.set(i, brightness, fade_duration)
            #     self._brightnesses[i] = brightness

            # keep minimum brightness
            b = self.settings["unplucked_beam_brightness"]
            if self._brightnesses[i] < b or fade_duration > 0:
                self._laser_array.set(i, b, fade_duration)
                self._brightnesses[i] = b

    def _update_velocities(self):
        velocities = np.zeros(128, dtype=np.uint8)

        for i in range(len(self._laser_array)):
            # convert laser index to note number
            note = self._note_lookup_table[i]
            if note == -1:
                continue

            # set the note
            if not np.isinf(self._intersections[i]):
                velocities[note] = 127

        # compare with previous state
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

    def process(self, interceptions: ImageProcessor.Result):
        # store interception lengths if they changed
        new_inters = np.where(interceptions.active, interceptions.length, np.inf)

        for i in range(len(self._laser_array)):
            if new_inters[i] != self._previous_intersections[i]:
                self._intersections[i] = new_inters[i]

        self._previous_intersections = new_inters

        # update midi output velocities
        self._update_velocities()

        # update brightness based on intersections
        self._update_brightnesses()

    # def _is_in_section(self, section: int, length: float) -> bool:
    #     start = self.settings["section_start_" + str(section)]
    #     end = self.settings.get("section_start_" + str(section + 1), np.inf)

    #     return start <= length < end

    # def _apply_pedal_positions(self, step: int) -> int:
    #     octave = step // len(self.MAJOR_SCALE_NOTES)
    #     step = step % len(self.MAJOR_SCALE_NOTES)

    #     # apply major scale
    #     note = self.MAJOR_SCALE_NOTES[step]

    #     # apply alterations from the pedal positions
    #     note += self.settings[f"pedal_position_{step}"]

    #     # apply octave
    #     note += octave * 12

    #     return note

    # def update_velocities(self, interceptions: ImageProcessor.Result):
    #     velocities = [0] * 128

    #     # iterate over each section and calculate the corresponding midi note and velocity
    #     for x, _ in enumerate(self._laser_array):
    #         beam_x = len(self._laser_array) - x - 1 if self.settings["flipped"] else x

    #         active = bool(interceptions.active[beam_x])
    #         length = float(interceptions.length[beam_x])
    #         _modulation = float(interceptions.modulation[beam_x])

    #         # deactivate the beam if it is muted
    #         if self.settings[f"pedal_mute_{x % len(self.MAJOR_SCALE_NOTES)}"]:
    #             active = False

    #         # use the diode index x as the step position and apply the current scale
    #         note_offset = self._apply_pedal_positions(x)

    #         for y in range(self.NUM_SECTIONS):
    #             note_active = active and self._is_in_section(y, length)

    #             # calculate the midi note
    #             note = self.config["root_note"]
    #             note += self.settings["global_transpose"]
    #             note += self.settings["section_transpose"] * (y - self.NUM_SECTIONS // 2)
    #             note += note_offset

    #             if note < 0 or note > 127:
    #                 continue

    #             # store the velocity
    #             velocity = 127 if note_active else 0
    #             velocities[note] = max(velocities[note], velocity)

    #             # store the new state
    #             self.state["active"][y][x] = note_active

    #     # apply the new velocities
    #     for note, velocity in enumerate(velocities):
    #         self.state["velocities"][note] = velocity

    # def update_brightness(self, fade_duration: float = 0.0):
    #     # skip brightness updates if the user is controlling the brightness
    #     if self._brightness_reset_counter > 0:
    #         self._brightness_reset_counter -= 1

    #         # check if any beams are scheduled to be turned off
    #         for x, brightness in enumerate(self._brightness_user):
    #             self._laser_array.set(x, brightness, fade_duration=fade_duration)

    #             # apply scheduled off for the next update tick
    #             # This will essentially delay note off messages by one update cycle and prevent flickering on fast updates
    #             if self._brightness_user_scheduled_off[x]:
    #                 self._brightness_user[x] = 0
    #                 self._brightness_user_scheduled_off[x] = False

    #         return

    #     # iterate over each beam and apply the corresponding brightness
    #     for x, _ in enumerate(self._laser_array):
    #         beam_x = len(self._laser_array) - x - 1 if self.settings["flipped"] else x

    #         if self.settings[f"pedal_mute_{x % len(self.MAJOR_SCALE_NOTES)}"]:
    #             # if the beam is muted, apply the muted brightness
    #             brightness = self.settings["muted_beam_brightness"]
    #         elif any(self.state["active"][y][x] for y in range(self.NUM_SECTIONS)):
    #             # if any of the corresponding sections are active, apply the plucked brightness
    #             brightness = self.settings["plucked_beam_brightness"]
    #         else:
    #             # otherwise, apply the unpluckled brightness
    #             brightness = self.settings["unplucked_beam_brightness"]

    #         self._laser_array.set(beam_x, brightness, fade_duration=fade_duration)

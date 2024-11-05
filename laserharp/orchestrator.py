import time
import logging
from typing import Optional
import numpy as np
from perci import ReactiveDictNode, watch
from perci.changes import Change, UpdateChange
from .component import Component
from .midi import MidiEvent
from .image_processor import ImageProcessor
from .laser_array import LaserArray
from .din_midi import DinMidi
from .scales import calculate_pedal_positions


class Orchtestrator(Component):
    NUM_SECTIONS = 3
    MAJOR_SCALE_NOTES = [0, 2, 4, 5, 7, 9, 11]

    def __init__(self, name: str, global_state: ReactiveDictNode, laser_array: LaserArray, din_midi: DinMidi):
        super().__init__(name, global_state)

        self._laser_array = laser_array
        self._din_midi = din_midi

        # setup the pedal positions for each predefined scale
        self.state["scale_pedal_positions"] = []
        for scale in self.config["scales"]:
            try:
                self.state["scale_pedal_positions"].append(
                    {
                        "name": scale["name"],
                        "pedal_positions": calculate_pedal_positions(scale["notes"]),
                    }
                )
            except ValueError as e:
                logging.error(f"Error while calculating pedal positions for scale {scale['name']}: {e}")
                logging.exception(e)
                raise e

        # setup an array of shape (num_sections, num_lasers) to keep track of which lasers are active
        self.state["active"] = [[False] * len(self._laser_array) for _ in range(self.NUM_SECTIONS)]
        self.state["velocities"] = [0] * 128

        watch(self.state["velocities"], lambda change: self._send_note_message(int(change.path[-1]), change.value))
        watch(self.settings.get_child("flipped"), lambda change: self._on_flipped(change.value))

    def start(self):
        # fade in the initial color
        print("ORCHESTRATOR INITIALIZED")
        self._laser_array.set_all(self.settings["unplucked_beam_brightness"], fade_duration=0.5)

    def stop(self):
        # set all notes off
        for note, _ in enumerate(self.state["velocities"]):
            self.state["velocities"][note] = 0

    def set_scale(self, scale: str | int | list[int]):
        if isinstance(scale, str):
            # find pedal positions by name
            scale_obj = next((s for s in self.state["scale_pedal_positions"] if s["name"] == scale), None)
            if scale_obj is None:
                raise ValueError(f"Scale {scale} not found.")

            pedal_positions = scale_obj["pedal_positions"]

        elif isinstance(scale, int):
            # find scale by index
            pedal_positions = self.state["scale_pedal_positions"][scale]["pedal_positions"]

        elif isinstance(scale, list):
            # calculate pedal positions for custom scale
            pedal_positions = calculate_pedal_positions(scale)

        else:
            raise ValueError(f"Invalid scale type {type(scale)}.")

        # apply the new pedal positions
        for i, position in enumerate(pedal_positions):
            self.settings[f"pedal_position_{i}"] = position if position is not None else 0
            self.settings[f"pedal_mute_{i}"] = position is None

    def flip(self):
        self.settings["flipped"] = not self.settings["flipped"]

    def process(self, interceptions: ImageProcessor.Result):
        self.update_velocities(interceptions)
        self.update_brightness()

    def update_velocities(self, interceptions: ImageProcessor.Result):
        velocities = [0] * 128

        # iterate over each section and calculate the corresponding midi note and velocity
        for x, _ in enumerate(self._laser_array):
            beam_x = len(self._laser_array) - x - 1 if self.settings["flipped"] else x

            active = bool(interceptions.active[beam_x])
            length = float(interceptions.length[beam_x])
            _modulation = float(interceptions.modulation[beam_x])

            # deactivate the beam if it is muted
            if self.settings[f"pedal_mute_{x % len(self.MAJOR_SCALE_NOTES)}"]:
                active = False

            # use the diode index x as the step position and apply the current scale
            note_offset = self._apply_scale(x)

            for y in range(self.NUM_SECTIONS):
                note_active = active and self._is_in_section(y, length)

                # calculate the midi note
                note = self.settings["root_note"]
                note += y * self.settings["section_octave_spacing"] * 12
                note += note_offset

                if note < 0 or note > 127:
                    continue

                # store the velocity
                velocity = 127 if note_active else 0
                velocities[note] = max(velocities[note], velocity)

                # store the new state
                self.state["active"][y][x] = note_active

        # apply the new velocities
        for note, velocity in enumerate(velocities):
            self.state["velocities"][note] = velocity

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

    def _send_note_message(self, note: int, velocity: int):
        if velocity == 0:
            self._din_midi.send(MidiEvent(0, "note_off", note=note))
        else:
            self._din_midi.send(MidiEvent(0, "note_on", note=note, velocity=velocity))

    def _on_flipped(self, _: bool):
        # play flip animation
        self._laser_array.play_animation("flip", 0.5, "restore")

    def update_brightness(self):
        for x, _ in enumerate(self._laser_array):
            beam_x = len(self._laser_array) - x - 1 if self.settings["flipped"] else x

            # if the beam is muted, apply the muted brightness
            if self.settings[f"pedal_mute_{x % len(self.MAJOR_SCALE_NOTES)}"]:
                self._laser_array[beam_x] = self.settings["muted_beam_brightness"]
                continue

            # check if any of the corresponding sections are active
            active = any(self.state["active"][y][x] for y in range(self.NUM_SECTIONS))

            # set the beam brightness
            brightness = self.settings["plucked_beam_brightness"] if active else self.settings["unplucked_beam_brightness"]
            self._laser_array[beam_x] = brightness

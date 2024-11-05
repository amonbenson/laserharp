from itertools import product
import logging

PEDAL_NATURAL_NOTES = [0, 2, 4, 5, 7, 9, 11]  # major scale


def _get_all_pedal_positions(valid_alterations: list[list[int]]) -> list[list[int]]:
    """
    This function generates all possible combinations of pedal positions. If a valid alteration is empty, None is returned for that pedal position.

    Example:
        valid_alterations = [[0], [0], [1], [], [0, 1], [-1, 0], [0]]
        result = [
            [0, 0, 1, None, 0, -1, 0],
            [0, 0, 1, None, 0, 0, 0],
            [0, 0, 1, None, 1, -1, 0],
            [0, 0, 1, None, 1, 0, 0],
        ]
    """

    # replace empty list with [None] for each position
    valid_alterations = [[None] if not alterations else alterations for alterations in valid_alterations]

    # generate all combinations
    return product(*valid_alterations)


def _is_valid_pedal_positions(pedal_positions: list[int], scale_notes: list[int]) -> bool:
    """
    This function checks if the given pedal positions are valid. A pedal position is valid, if each note within the scale can be played by at least one pedal.
    """

    return all(any((natural_note + alteration) % 12 == note for natural_note, alteration in zip(PEDAL_NATURAL_NOTES, pedal_positions) if alteration is not None) for note in scale_notes)


def calculate_pedal_positions(scale_notes: list[int]):
    """
    The following algorithm is used:
    - For each pedal position, all valid alterations are stored. An alteration is considered valid, if the natural pedal note + alteration occurs within the scale.
    - Possible alterations are: -1 (flat), 0 (natural), or 1 (sharp). If no alteration fits, the valid alterations list is empty and the pedal must be muted later on.
    - Then, each combination of pedal positions is checked. If any note within the scale cannot be played with the given pedal positions, the combination is invalid.
    - The first valid combination is returned.
    """

    # get all possible alterations for each pedal note
    valid_alterations = [[] for _ in range(7)]
    for i, pedal_step in enumerate(PEDAL_NATURAL_NOTES):
        for alteration in range(-1, 2):
            if (pedal_step + alteration) % 12 in scale_notes:
                valid_alterations[i].append(alteration)

    # check all combinations of pedal positions
    logging.debug(f"Checking alterations {valid_alterations} for scale notes {scale_notes}")
    for pedal_positions in _get_all_pedal_positions(valid_alterations):
        if _is_valid_pedal_positions(pedal_positions, scale_notes):
            print(f"Found valid pedal positions: {pedal_positions}")
            return list(pedal_positions)

    raise ValueError("No valid pedal position found.")

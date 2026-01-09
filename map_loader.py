"""Map loading and utility functions."""

import os
from config import MAPS_FOLDER


def load_maps():
    """Load all map files from the maps folder."""
    files = []
    for f in os.listdir(MAPS_FOLDER):
        files.append(f)
    return files



def load_map(filename):
    """Load a map file and return it as a 2D list."""
    with open(filename) as f:
        return [list(line.strip()) for line in f]


def find_player(game_map):
    """Find the player's starting position in the map."""
    for y, row in enumerate(game_map):
        for x, cell in enumerate(row):
            if cell == "P":
                return x, y
    return None, None


def find_all_targets(game_map, target_char):
    """Find all positions of a specific character in the map."""
    targets = []
    for y, row in enumerate(game_map):
        for x, cell in enumerate(row):
            if cell == target_char:
                targets.append((x, y))
    return targets


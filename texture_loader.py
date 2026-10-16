"""Load the active woodland atlas, ground and puzzle art."""
from functools import lru_cache
from pathlib import Path
import pygame
from puzzle_art import create_puzzle_tiles

ART_FOLDER = Path(__file__).resolve().parent / 'textures' / 'woodland'


@lru_cache(maxsize=4)
def load_textures_with_size(tile_size):
    atlas = pygame.image.load(str(ART_FOLDER / 'tiles.png')).convert_alpha()
    cell_w, cell_h = atlas.get_width() // 3, atlas.get_height() // 3
    cells = {'1': (1, 0), 'P': (2, 0), 'C': (0, 1), 'E': (1, 1),
             'W': (2, 1), 'L': (0, 2), 'F': (1, 2), 'R': (2, 2)}
    textures = {
        key: pygame.transform.smoothscale(
            atlas.subsurface((col*cell_w, row*cell_h, cell_w, cell_h)),
            (tile_size, tile_size))
        for key, (col, row) in cells.items()
    }
    ground = pygame.image.load(str(ART_FOLDER / 'ground-day.png')).convert()
    textures['0'] = pygame.transform.smoothscale(ground, (tile_size, tile_size))
    textures['0'].fill((221, 231, 210), special_flags=pygame.BLEND_RGB_MULT)
    textures.update(create_puzzle_tiles(tile_size, textures))
    return textures


def create_player_textures(textures):
    rabbit = textures['P']
    return {'right': rabbit, 'left': pygame.transform.flip(rabbit, True, False),
            'up': rabbit, 'down': rabbit}

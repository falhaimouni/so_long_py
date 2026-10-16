"""Texture loading functions."""

import os
from pathlib import Path
from functools import lru_cache
import pygame
from config import TEXTURES_FOLDER


@lru_cache(maxsize=4)
def load_textures_with_size(tile_size):
    """Load all texture images and scale them to the specified tile size."""
    textures = {}
    texture_map = {
        "1": "tree.png",    # Wall/Tree
        "0": "grass.png",   # Floor/Grass
        "P": "rabbit.png",  # Player/Rabbit
        "C": "carrot.png",  # Collectible/Carrot
        "E": "burrow.png",  # Exit/Burrow
        "W": "water.png",   # Water (Level 2)
        "L": "log.png",     # Log (Level 2)
        "F": "fox.png",     # Fox (Level 3)
        "R": "rock.png"     # Rock (Alternative Wall)
    }
    
    atlas_path = Path(__file__).resolve().parent / 'textures' / 'woodland' / 'tiles.png'
    atlas = pygame.image.load(str(atlas_path)).convert_alpha() if atlas_path.exists() else None
    atlas_order = {'0': (0, 0), '1': (1, 0), 'P': (2, 0),
                   'C': (0, 1), 'E': (1, 1), 'W': (2, 1),
                   'L': (0, 2), 'F': (1, 2), 'R': (2, 2)}
    for key, filename in texture_map.items():
        path = os.path.join(TEXTURES_FOLDER, filename)
        try:
            # Load PNG file using pygame
            if atlas is not None:
                col, row = atlas_order[key]
                cell_w, cell_h = atlas.get_width() // 3, atlas.get_height() // 3
                img_surface = atlas.subsurface((col*cell_w, row*cell_h, cell_w, cell_h)).copy()
            else:
                img_surface = pygame.image.load(str(Path(__file__).resolve().parent / path))
            # Convert to RGBA format if needed for transparency support
            if img_surface.get_alpha() is not None:
                img_surface = img_surface.convert_alpha()
            else:
                img_surface = img_surface.convert()
            # Scale image to specified tile size
            textures[key] = pygame.transform.smoothscale(img_surface, (tile_size, tile_size))
        except Exception as e:
            print(f"Warning: Could not load texture {filename}: {e}")
            # Fallback: create a colored surface
            textures[key] = pygame.Surface((tile_size, tile_size))
            colors = {"1": (34, 139, 34), "0": (144, 238, 144), "P": (255, 255, 255), 
                     "C": (255, 165, 0), "E": (139, 69, 19), "W": (0, 0, 255),
                     "L": (160, 82, 45), "F": (255, 69, 0), "R": (128, 128, 128)}
            textures[key].fill(colors.get(key, (100,100,100)))
    
    ground = Path(__file__).resolve().parent / 'textures' / 'woodland' / 'ground-day.png'
    if ground.exists():
        textures['0'] = pygame.transform.smoothscale(pygame.image.load(str(ground)).convert(), (tile_size, tile_size))
    # A gentle ambient grade keeps the sunlit meadow from looking fluorescent.
    textures['0'].fill((221, 231, 210), special_flags=pygame.BLEND_RGB_MULT)
    textures.update(create_puzzle_textures(tile_size, textures))
    return textures


def create_player_textures(textures):
    """Create player textures for all directions."""
    player_texture_base = textures["P"]
    # For the rabbit, we'll just flip it for left/right and keep same for up/down
    player_texture_right = player_texture_base
    player_texture_left = pygame.transform.flip(player_texture_base, True, False)
    player_texture_up = player_texture_base
    player_texture_down = player_texture_base
    
    return {
        "right": player_texture_right,
        "left": player_texture_left,
        "up": player_texture_up,
        "down": player_texture_down
    }


def create_puzzle_textures(size, textures):
    from puzzle_art import create_puzzle_tiles
    return create_puzzle_tiles(size, textures)

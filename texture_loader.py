"""Texture loading functions."""

import os
import pygame
from config import TILE, TEXTURES_FOLDER


def load_textures():
    """Load all texture images and scale them to TILE size."""
    return load_textures_with_size(TILE)


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
    
    for key, filename in texture_map.items():
        path = os.path.join(TEXTURES_FOLDER, filename)
        try:
            # Load PNG file using pygame
            img_surface = pygame.image.load(path)
            # Convert to RGBA format if needed for transparency support
            if img_surface.get_alpha() is not None:
                img_surface = img_surface.convert_alpha()
            else:
                img_surface = img_surface.convert()
            # Scale image to specified tile size
            textures[key] = pygame.transform.scale(img_surface, (tile_size, tile_size))
        except Exception as e:
            print(f"Warning: Could not load texture {filename}: {e}")
            # Fallback: create a colored surface
            textures[key] = pygame.Surface((tile_size, tile_size))
            colors = {"1": (34, 139, 34), "0": (144, 238, 144), "P": (255, 255, 255), 
                     "C": (255, 165, 0), "E": (139, 69, 19), "W": (0, 0, 255),
                     "L": (160, 82, 45), "F": (255, 69, 0), "R": (128, 128, 128)}
            textures[key].fill(colors.get(key, (100,100,100)))
    
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

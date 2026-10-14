"""Texture loading functions."""

import os
import pygame
from config import TEXTURES_FOLDER


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
    """Draw readable puzzle tiles using existing art and simple shapes."""
    tiles = {}
    gold, blue = (255, 200, 65), (120, 205, 255)
    font = pygame.font.SysFont("Arial", max(12, size // 4), bold=True)

    def blank():
        return pygame.Surface((size, size), pygame.SRCALPHA)

    def label(surface, text, color=(255, 255, 255)):
        rendered = font.render(text, True, color)
        surface.blit(rendered, rendered.get_rect(center=(size // 2, size // 2)))

    switch = blank()
    pygame.draw.rect(switch, (75, 55, 25), (8, 14, size - 16, size - 28), border_radius=8)
    pygame.draw.rect(switch, gold, (12, 18, size - 24, size - 36), border_radius=5)
    label(switch, "SWAP", (40, 30, 20))
    tiles["S"] = switch

    for key, color in (("G", gold), ("H", blue)):
        for opened in (False, True):
            surface = blank()
            pygame.draw.rect(surface, color, (5, 5, size - 10, size - 10), 3, border_radius=5)
            if not opened:
                for x in (size // 4, size // 2, 3 * size // 4):
                    pygame.draw.line(surface, (90, 65, 35), (x, 9), (x, size - 9), 7)
            # Sun disc / moon crescent identifies the gate independently of color.
            pygame.draw.circle(surface, color, (size // 2, size // 2), size // 7)
            if key == "H":
                pygame.draw.circle(surface, (40, 65, 75), (size // 2 + 5, size // 2 - 3), size // 8)
            tiles[key + ("_open" if opened else "")] = surface

    for keys, number, color in (("AB", "1", (200, 105, 255)), ("UV", "2", (65, 230, 235))):
        surface = blank()
        pygame.draw.ellipse(surface, (35, 25, 65), (6, 4, size - 12, size - 8))
        pygame.draw.ellipse(surface, color, (6, 4, size - 12, size - 8), 5)
        label(surface, number)
        for key in keys:
            tiles[key] = surface

    plank = textures["W"].copy()
    plank.blit(textures["L"], (0, 0))
    pygame.draw.rect(plank, (255, 185, 75), (3, 8, size - 6, size - 16), 3)
    pygame.draw.lines(plank, (65, 35, 20), False,
                      [(size // 2, 10), (size // 2 - 7, size // 2),
                       (size // 2 + 5, size // 2 + 5), (size // 2, size - 10)], 3)
    tiles["X"] = plank
    tiles["T"] = blank()
    # Permanent lane marking stays visible during the safe part of a cycle.
    pygame.draw.rect(tiles["T"], (145, 115, 40), (3, 3, size - 6, size - 6), 2)
    for key, color in (("T", (255, 190, 35)), ("X", (70, 200, 255))):
        for phase in ("warning", "active"):
            surface = blank()
            surface.fill((*color, 75 if phase == "warning" else 190))
            pygame.draw.rect(surface, color, (2, 2, size - 4, size - 4), 3)
            if key == "T":
                pygame.draw.lines(surface, (255, 255, 230), False,
                                  [(size // 2 + 8, 6), (size // 2 - 7, size // 2),
                                   (size // 2 + 5, size // 2), (size // 2 - 8, size - 6)],
                                  3 if phase == "warning" else 7)
            else:
                for y in (size // 3, 2 * size // 3):
                    pygame.draw.lines(surface, (220, 250, 255), False,
                                      [(4, y), (size // 3, y - 5),
                                       (2 * size // 3, y + 5), (size - 4, y)], 3)
            tiles[key + "_" + phase] = surface
    return tiles

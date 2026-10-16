"""Active-only storm and tide effects, independent of rendering FPS."""
import math
import pygame
from config import (LIGHTNING_SAFE_MS, LIGHTNING_ACTIVE_MS,
                    TIDE_SAFE_MS, TIDE_ACTIVE_MS, PLANK_LIFETIME_MS)

LIGHTNING_CYCLE_MS = LIGHTNING_SAFE_MS + LIGHTNING_ACTIVE_MS
TIDE_CYCLE_MS = TIDE_SAFE_MS + TIDE_ACTIVE_MS


def phase_at(elapsed, safe, active, offset=0):
    phase = (elapsed + offset) % (safe + active)
    return ('safe', safe-phase) if phase < safe else ('active', safe+active-phase)


def hazard_phase(level, tile, position, elapsed):
    if level == 3 and tile == 'T':
        return phase_at(elapsed, LIGHTNING_SAFE_MS, LIGHTNING_ACTIVE_MS,
                        LIGHTNING_CYCLE_MS//2 if position[1] == 8 else 0)
    if level == 5 and tile == 'X':
        return phase_at(elapsed, TIDE_SAFE_MS, TIDE_ACTIVE_MS)
    return 'safe', 0


def deadly_tile(level, tile, position, elapsed, plank_age=0):
    phase, _ = hazard_phase(level, tile, position, elapsed)
    return phase == "active" or (level == 5 and tile == "X" and plank_age >= PLANK_LIFETIME_MS)


class HazardField:
    def __init__(self, level, grid):
        self.level, self.grid = level, grid
        self.elapsed = 0
        self.plank_started = 0
        self._effect_surface = None
        self.tiles = [(x, y) for y, row in enumerate(grid) for x, char in enumerate(row)
                      if (level == 3 and char == "T") or (level == 5 and char == "X")]

    def advance(self, dt):
        self.elapsed += dt

    def arrive(self, position):
        self.plank_started = self.elapsed

    def deadly(self, position):
        x, y = position
        return deadly_tile(self.level, self.grid[y][x], position, self.elapsed,
                           self.elapsed - self.plank_started)

    def status(self, position):
        # Only report an event while it is happening. No advance countdowns.
        if self.level == 3 and any(hazard_phase(3, 'T', (0, row), self.elapsed)[0] == 'active' for row in (5, 8)):
            return 'Lightning'
        if self.level == 5 and hazard_phase(5, 'X', position, self.elapsed)[0] == 'active':
            return 'Tidal surge'
        return ''

    def draw(self, screen, textures, size, mechanics, state):
        phase = self.elapsed / 1000
        active = [(x,y) for x,y in self.tiles
                  if not mechanics.fragile.get((x,y),0) & state.collapsed
                  and hazard_phase(self.level,self.grid[y][x],(x,y),self.elapsed)[0] == 'active']
        if not active:
            return
        if self._effect_surface is None or self._effect_surface.get_size() != screen.get_size():
            self._effect_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay = self._effect_surface
        overlay.fill((0,0,0,0))
        for x, y in active:
            tile = self.grid[y][x]
            left, top = x*size, y*size
            if tile == 'T':
                # A connected electrical ribbon follows the full stone lane.
                points = [(left+step*size/8, top+size*.5+
                           math.sin((x*8+step)*1.7+int(phase*12))*size*.12)
                          for step in range(9)]
                pygame.draw.lines(overlay, (100, 175, 219, 55), False, points, 21)
                pygame.draw.lines(overlay, (141, 206, 238, 160), False, points, 8)
                pygame.draw.lines(overlay, (247, 251, 223, 255), False, points, 2)
                cx = left+size*.5
                bolt = [(cx+8,top+9),(cx-7,top+size*.45),
                        (cx+5,top+size*.48),(cx-9,top+size-9)]
                pygame.draw.lines(overlay, (117, 192, 239, 95), False, bolt, 13)
                pygame.draw.lines(overlay, (235, 250, 244, 255), False, bolt, 3)
            else:
                pygame.draw.rect(overlay, (38, 134, 159, 105), (left,top,size,size))
                for row in range(3):
                    points = [(left+step*size/12,
                               top+(row+.5)*size/3+math.sin(step*.6+phase*7+x)*4)
                              for step in range(13)]
                    pygame.draw.lines(overlay, (131, 221, 227, 160), False, points, 7)
                    pygame.draw.lines(overlay, (227, 246, 224, 230), False, points, 2)
        screen.blit(overlay, (0,0))

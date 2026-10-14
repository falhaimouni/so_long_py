"""Telegraphed lethal storms and sinking bridges, independent of rendering FPS."""

from math import ceil

from config import (LIGHTNING_SAFE_MS, LIGHTNING_WARNING_MS, LIGHTNING_ACTIVE_MS,
                    TIDE_SAFE_MS, TIDE_WARNING_MS, TIDE_ACTIVE_MS, PLANK_LIFETIME_MS)

LIGHTNING_CYCLE_MS = LIGHTNING_SAFE_MS + LIGHTNING_WARNING_MS + LIGHTNING_ACTIVE_MS
TIDE_CYCLE_MS = TIDE_SAFE_MS + TIDE_WARNING_MS + TIDE_ACTIVE_MS


def phase_at(elapsed, safe, warning, active, offset=0):
    phase = (elapsed + offset) % (safe + warning + active)
    if phase < safe:
        return "safe", safe - phase
    if phase < safe + warning:
        return "warning", safe + warning - phase
    return "active", safe + warning + active - phase


def hazard_phase(level, tile, position, elapsed):
    if level == 3 and tile == "T":
        # Separate lanes strike half a cycle apart.
        return phase_at(elapsed, LIGHTNING_SAFE_MS, LIGHTNING_WARNING_MS,
                        LIGHTNING_ACTIVE_MS, LIGHTNING_CYCLE_MS // 2 if position[1] == 8 else 0)
    if level == 5 and tile == "X":
        return phase_at(elapsed, TIDE_SAFE_MS, TIDE_WARNING_MS, TIDE_ACTIVE_MS)
    return "safe", 0


def deadly_tile(level, tile, position, elapsed, plank_age=0):
    phase, _ = hazard_phase(level, tile, position, elapsed)
    return phase == "active" or (level == 5 and tile == "X" and plank_age >= PLANK_LIFETIME_MS)


class HazardField:
    def __init__(self, level, grid):
        self.level, self.grid = level, grid
        self.elapsed = 0
        self.plank_started = 0
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
        if self.level == 3:
            phases = [hazard_phase(self.level, "T", (0, row), self.elapsed) for row in (5, 8)]
            if any(stage == "active" for stage, _ in phases):
                return "LIGHTNING LIVE - leave the bright storm lane!"
            remaining = min(time for _, time in phases)
            return f"Lightning warning: {ceil(remaining / 100) / 10:.1f}s" if any(
                stage == "warning" for stage, _ in phases) else "Storm lanes quiet - amber means move away"
        if self.level == 5:
            stage, remaining = hazard_phase(self.level, "X", position, self.elapsed)
            if stage == "safe":
                remaining += TIDE_WARNING_MS
            message = (f"{('WAVE LIVE' if stage == 'active' else 'Wave warning' if stage == 'warning' else 'Next wave')}: "
                       f"{ceil(remaining / 100) / 10:.1f}s")
            x, y = position
            if self.grid[y][x] == "X":
                lifetime = max(0, PLANK_LIFETIME_MS - (self.elapsed - self.plank_started))
                message += f" | Plank sinks in {ceil(lifetime / 100) / 10:.1f}s"
            return message
        return ""

    def draw(self, screen, textures, size, mechanics, state):
        for x, y in self.tiles:
            if mechanics.fragile.get((x, y), 0) & state.collapsed:
                continue
            tile = self.grid[y][x]
            stage, _ = hazard_phase(self.level, tile, (x, y), self.elapsed)
            if stage != "safe":
                screen.blit(textures[tile + "_" + stage], (x * size, y * size))

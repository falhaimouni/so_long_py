"""Deterministic puzzle rules shared by gameplay and route checks."""

from collections import deque
from dataclasses import dataclass


PORTAL_PAIRS = (("A", "B"), ("U", "V"))
LEVEL_GUIDES = (
    ('Carrot Trail', 'Collect the carrots, then find the burrow.'),
    ('River Ride', 'Cross the river on the moving logs.'),
    ('Fox Forest', 'Collect the carrots. Stay ahead of the fox.'),
    ('Storm Switchyard', 'Step on switches to swap gates. Avoid lightning.'),
    ('Portal Hunt', 'Matching portals connect the gardens. The fox can follow.'),
    ('Sinking Causeway', 'Cross the planks quickly. Watch for waves.'),
)


@dataclass(frozen=True)
class PuzzleState:
    sun_open: bool = False
    collapsed: int = 0


class LevelMechanics:
    def __init__(self, grid):
        self.grid = grid
        self.portals = {}
        self.fragile = {}
        self.gates = []
        endpoints = {}
        for y, row in enumerate(grid):
            for x, char in enumerate(row):
                if char in "ABUV":
                    endpoints[char] = (x, y)
                elif char == "X":
                    self.fragile[x, y] = 1 << len(self.fragile)
                elif char in "GH":
                    self.gates.append((x, y))
        for first, second in PORTAL_PAIRS:
            if first in endpoints and second in endpoints:
                a, b = endpoints[first], endpoints[second]
                self.portals[a], self.portals[b] = b, a

    def blocked(self, position, state):
        x, y = position
        if not (0 <= y < len(self.grid) and 0 <= x < len(self.grid[y])):
            return True
        char = self.grid[y][x]
        return (char in "1R" or (char == "G" and not state.sun_open)
                or (char == "H" and state.sun_open)
                or bool(self.fragile.get(position, 0) & state.collapsed))

    def enter(self, origin, destination, state):
        """Resolve one tile move. Arrival never immediately retriggers a portal."""
        if self.blocked(destination, state):
            return None
        x, y = destination
        char = self.grid[y][x]
        collapsed = state.collapsed | self.fragile.get(origin, 0)
        sun_open = not state.sun_open if char == "S" else state.sun_open
        return self.portals.get(destination, destination), PuzzleState(sun_open, collapsed)

    def texture_key(self, position, state):
        x, y = position
        char = self.grid[y][x]
        if self.fragile.get(position, 0) & state.collapsed:
            return "W"
        if (char == "G" and state.sun_open) or (char == "H" and not state.sun_open):
            return char + "_open"
        return char


def next_fox_position(grid, origin, target, mechanics, state, use_portals=False):
    """Follow the shortest walkable route, including portals in the portal hunt."""
    queue = deque([(origin, None)])
    visited = {origin}
    while queue:
        position, first_step = queue.popleft()
        if position == target:
            return first_step or origin
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            candidate = (position[0] + dx, position[1] + dy)
            if mechanics.blocked(candidate, state):
                continue
            x, y = candidate
            if grid[y][x] in "WE":
                continue
            landing = mechanics.portals.get(candidate, candidate) if use_portals else candidate
            if landing not in visited:
                visited.add(landing)
                queue.append((landing, landing if first_step is None else first_step))
    return origin

"""Time-aware route search for regression playthroughs, including wait actions."""

from collections import deque
from functools import lru_cache
from heapq import heappop, heappush
from itertools import count

from config import FOX_INTERVAL_MS, PORTAL_FOX_INTERVAL_MS, PORTAL_FOX_GRACE_MS
from hazards import deadly_tile, LIGHTNING_CYCLE_MS, TIDE_CYCLE_MS
from level_mechanics import LevelMechanics, PuzzleState, next_fox_position

DIRECTIONS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


def solve(grid, level):
    mechanics = LevelMechanics(grid)
    carrots, spawns = {}, []
    for y, row in enumerate(grid):
        for x, char in enumerate(row):
            if char == "P":
                start = (x, y)
            elif char == "E":
                exit_position = (x, y)
            elif char == "C":
                carrots[x, y] = 1 << len(carrots)
            elif char == "F":
                spawns.append((x, y))
    all_carrots = (1 << len(carrots)) - 1
    fox_interval = PORTAL_FOX_INTERVAL_MS if level == 4 else FOX_INTERVAL_MS
    grace = PORTAL_FOX_GRACE_MS if level == 4 else 0

    def canonical_time(elapsed):
        if level == 3:
            return elapsed % LIGHTNING_CYCLE_MS
        if level == 5:
            return elapsed % TIDE_CYCLE_MS
        return elapsed if elapsed < grace else grace + (elapsed - grace) % fox_interval

    @lru_cache(None)
    def fox_step(origin, target):
        return next_fox_position(grid, origin, target, mechanics, PuzzleState(), level == 4)

    @lru_cache(None)
    def distances(origin):
        distances = {origin: 0}
        queue = deque([origin])
        while queue:
            position = queue.popleft()
            for dx, dy in DIRECTIONS.values():
                x, y = position[0] + dx, position[1] + dy
                if not (0 <= y < len(grid) and 0 <= x < len(grid[y])) or grid[y][x] in "1RW":
                    continue
                landing = mechanics.portals.get((x, y), (x, y))
                if landing not in distances:
                    distances[landing] = distances[position] + 1
                    queue.append(landing)
        return distances

    @lru_cache(None)
    def tree_cost(mask):
        targets = [position for position, bit in carrots.items() if not mask & bit] + [exit_position]
        reached = [targets.pop()]
        cost = 0
        while targets:
            distance, target = min((min(distances(a).get(b, 10000), distances(b).get(a, 10000)), b)
                                   for a in reached for b in targets)
            cost += distance
            targets.remove(target)
            reached.append(target)
        return cost

    def heuristic(position, mask):
        targets = [p for p, bit in carrots.items() if not mask & bit] + [exit_position]
        return tree_cost(mask) + min(distances(position).get(p, 10000) for p in targets)

    def transition(node, action):
        position, state, collected, foxes, elapsed, plank_age = node
        foxes = list(foxes)
        # Game updates at 50 ms; issue one directional action every 150 ms.
        for substep in range(3):
            elapsed += 50
            x, y = position
            plank_age = plank_age + 50 if grid[y][x] == "X" else 0
            if deadly_tile(level, grid[y][x], position, elapsed, plank_age):
                return None
            if substep == 2 and action is not None:
                dx, dy = DIRECTIONS[action]
                destination = (x + dx, y + dy)
                if mechanics.blocked(destination, state):
                    return None
                nx, ny = destination
                if grid[ny][nx] == "W":
                    return None
                position, state = mechanics.enter(position, destination, state)
                plank_age = 0
                x, y = position
                if deadly_tile(level, grid[y][x], position, elapsed, plank_age) or position in foxes:
                    return None
                collected |= carrots.get(position, 0)
            if collected == all_carrots and position == exit_position:
                return position, state, collected, tuple(foxes), canonical_time(elapsed), plank_age
            for index, fox in enumerate(foxes):
                if position == fox:
                    return None
                if elapsed > grace and (elapsed - grace) % fox_interval == 0:
                    foxes[index] = fox_step(fox, position)
                    if foxes[index] == position:
                        return None
        return position, state, collected, tuple(foxes), canonical_time(elapsed), plank_age

    initial = (start, PuzzleState(), 0, tuple(spawns), 0, 0)
    sequence = count()
    queue = [(heuristic(start, 0), next(sequence), 0, initial)]
    costs, parents = {initial: 0}, {initial: None}
    expanded = 0
    while queue:
        _, _, cost, node = heappop(queue)
        if costs[node] != cost:
            continue
        if node[0] == exit_position and node[2] == all_carrots:
            route = []
            while parents[node] is not None:
                node, action = parents[node]
                route.append(action)
            return list(reversed(route))
        expanded += 1
        if expanded > 250000:
            raise AssertionError(f"Level {level + 1}: route search exceeded 250000 states")
        for action in (*DIRECTIONS, None):
            successor = transition(node, action)
            if successor is None or costs.get(successor, float("inf")) <= cost + 1:
                continue
            costs[successor] = cost + 1
            parents[successor] = node, action
            score = cost + 1 + heuristic(successor[0], successor[2])
            heappush(queue, (score, next(sequence), cost + 1, successor))
    raise AssertionError(f"Level {level + 1}: no surviving route to all carrots and the burrow")

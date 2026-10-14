"""Check winning routes and real deaths using timed, simulated hand input."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from collections import defaultdict
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame

import game
from hand_tracking import TrackingSnapshot
from level_mechanics import LevelMechanics, PuzzleState
from map_validator import validate_map
from hazard_routes import solve
from hazards import deadly_tile, hazard_phase
from config import (PLANK_LIFETIME_MS, MOVE_INTERVAL_MS, LIGHTNING_SAFE_MS,
                    LIGHTNING_WARNING_MS, TIDE_SAFE_MS, TIDE_WARNING_MS)
from level_mechanics import next_fox_position


class NewLevelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.routes = {index: solve(game.LEVELS[index], index) for index in (2, 3, 4, 5)}

    def tearDown(self):
        pygame.quit()

    def test_six_valid_levels_with_distinct_mechanics(self):
        self.assertEqual(len(game.LEVELS), 6)
        for level in game.LEVELS:
            self.assertTrue(validate_map([list(row) for row in level])[0])
        self.assertTrue(set("SGH").issubset("".join(game.LEVELS[3])))
        self.assertTrue(set("ABUV").issubset("".join(game.LEVELS[4])))
        self.assertEqual("".join(game.LEVELS[4]).count("F"), 1)
        self.assertIn("X", "".join(game.LEVELS[5]))
        self.assertTrue(all(len(route) > 40 for route in self.routes.values()))

    def test_gate_swaps_and_portals_do_not_bounce(self):
        grid = [list(row) for row in game.LEVELS[3]]
        mechanics = LevelMechanics(grid)
        state = PuzzleState()
        self.assertTrue(mechanics.blocked((3, 4), state))
        self.assertFalse(mechanics.blocked((3, 7), state))
        _, state = mechanics.enter((3, 2), (3, 3), state)
        self.assertFalse(mechanics.blocked((3, 4), state))
        self.assertTrue(mechanics.blocked((3, 7), state))
        mechanics = LevelMechanics(game.LEVELS[4])
        landing, state = mechanics.enter((5, 4), (6, 4), PuzzleState())
        self.assertEqual(landing, (9, 2))
        landing, _ = mechanics.enter(landing, (9, 3), state)
        self.assertEqual(landing, (9, 3))

    def test_bridge_collapses_only_after_departure_and_cannot_be_reused(self):
        mechanics = LevelMechanics(game.LEVELS[5])
        position, state = mechanics.enter((5, 2), (6, 2), PuzzleState())
        self.assertFalse(mechanics.blocked((6, 2), state))
        _, state = mechanics.enter(position, (7, 2), state)
        self.assertTrue(mechanics.blocked((6, 2), state))
        self.assertIsNone(mechanics.enter((7, 2), (6, 2), state))
        self.assertEqual(mechanics.texture_key((6, 2), state), "W")

    def test_incomplete_or_duplicate_portals_are_rejected(self):
        grid = [list(row) for row in game.LEVELS[4]]
        grid[2][9] = "0"
        self.assertFalse(validate_map(grid)[0])
        grid[2][9] = "B"
        grid[1][2] = "A"
        self.assertFalse(validate_map(grid)[0])

    def replay(self, index, route, expect_death=False):
        dt = MOVE_INTERVAL_MS // 3
        frame = [0]
        death_seen = [False]
        victory_at = [None]
        victory_quit = [False]

        class Clock:
            def tick(self, fps):
                frame[0] += 1
                return dt

            def get_fps(self):
                return 1000 / dt

        def gesture(timestamp=None):
            step = frame[0] // 3 - 1
            direction = route[step] if 0 <= step < len(route) and frame[0] % 3 == 0 else None
            return TrackingSnapshot(direction=direction, status="Camera active")

        def events():
            surface = pygame.display.get_surface()
            if not expect_death and index == 5 and frame[0] > 1 and surface is not None:
                sample = (surface.get_width() // 2 - 230, surface.get_height() // 2 - 100)
                if surface.get_at(sample)[:3] == (255, 255, 150):
                    if victory_at[0] is None:
                        victory_at[0] = frame[0]
                    if (frame[0] - victory_at[0]) * dt >= 4000:
                        victory_quit[0] = True
                        return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q)]
            if expect_death and frame[0] > 1 and surface is not None:
                # The red game-over box is rendered before its event loop starts.
                sample = (surface.get_width() // 2 - 280, surface.get_height() // 2 - 80)
                if surface.get_at(sample)[:3] == (139, 0, 0):
                    death_seen[0] = True
                    return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)]
            if frame[0] > len(route) * 3 + (600 if expect_death else 100):
                return [pygame.event.Event(pygame.QUIT)]
            return []

        tracker = SimpleNamespace(snapshot=gesture, show_preview=lambda: False)
        with patch("game.pygame.time.Clock", Clock), \
             patch("game.pygame.event.get", side_effect=events), \
             patch("game.pygame.key.get_pressed", return_value=defaultdict(bool)), \
             patch("game.now_ms", side_effect=lambda: frame[0] * dt):
            outcome = game._run_level(index, tracker)
        if expect_death:
            self.assertTrue(death_seen[0], f"Level {index + 1} did not kill the rabbit")
            self.assertEqual(outcome, "restart")
        else:
            self.assertEqual(outcome, "next" if index < 5 else "quit")
            if index == 5:
                self.assertTrue(victory_quit[0], "Victory screen should stay open until Q")

    def prefix_to_tile(self, index, tile):
        grid = game.LEVELS[index]
        mechanics, state = LevelMechanics(grid), PuzzleState()
        position = next((x, y) for y, row in enumerate(grid) for x, char in enumerate(row) if char == "P")
        for step, action in enumerate(self.routes[index]):
            if action is not None:
                dx, dy = game.DIRECTIONS[action]
                position, state = mechanics.enter(position, (position[0] + dx, position[1] + dy), state)
            if grid[position[1]][position[0]] == tile:
                return self.routes[index][:step + 1]
        self.fail(f"Route did not visit tile {tile}")

    def test_complete_levels_three_through_six_using_only_hand_directions(self):
        for index, route in self.routes.items():
            with self.subTest(level=index + 1, actions=len(route)):
                self.replay(index, route)
                print(f"Level {index + 1}: survived {len(route)} timed hand actions (including waits)")

    def test_storm_warns_then_kills_a_rabbit_that_stays_in_a_lane(self):
        strike_at = LIGHTNING_SAFE_MS + LIGHTNING_WARNING_MS
        self.assertEqual(hazard_phase(3, "T", (1, 5), LIGHTNING_SAFE_MS)[0], "warning")
        self.assertFalse(deadly_tile(3, "T", (1, 5), strike_at - 1))
        self.assertTrue(deadly_tile(3, "T", (1, 5), strike_at))
        self.replay(3, self.prefix_to_tile(3, "T"), expect_death=True)

    def test_foxes_follow_portals_and_catch_an_idle_rabbit(self):
        grid = game.LEVELS[4]
        mechanics = LevelMechanics(grid)
        self.assertEqual(next_fox_position(grid, (5, 4), (9, 3), mechanics, PuzzleState(), True), (9, 2))
        self.assertEqual(next_fox_position(grid, (5, 4), (9, 3), mechanics, PuzzleState(), False), (5, 4))
        self.replay(4, [], expect_death=True)
        self.replay(2, [], expect_death=True)

    def test_water_and_waiting_on_a_sinking_plank_cause_game_over(self):
        self.assertFalse(deadly_tile(5, "X", (6, 2), 0, PLANK_LIFETIME_MS - 1))
        self.assertTrue(deadly_tile(5, "X", (6, 2), 0, PLANK_LIFETIME_MS))
        self.replay(5, ["right"] * 5, expect_death=True)
        self.replay(5, self.prefix_to_tile(5, "X"), expect_death=True)

    def test_tidal_wave_warns_before_killing_on_bridges(self):
        wave_at = TIDE_SAFE_MS + TIDE_WARNING_MS
        self.assertEqual(hazard_phase(5, "X", (6, 2), TIDE_SAFE_MS)[0], "warning")
        self.assertFalse(deadly_tile(5, "X", (6, 2), wave_at - 1, 0))
        self.assertTrue(deadly_tile(5, "X", (6, 2), wave_at, 0))
        self.assertFalse(deadly_tile(5, "0", (5, 2), wave_at, 0))


if __name__ == "__main__":
    unittest.main()

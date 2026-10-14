"""Regression checks for timing, stale gestures, and the headless game loop."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from collections import defaultdict
from dataclasses import replace
from types import SimpleNamespace
import unittest
from threading import Event
from time import monotonic

import numpy as np
from unittest.mock import patch

import pygame

import game
from hand_tracking import HandTracker, TrackingSnapshot, GestureController, draw_control_preview
from motion import AnimatedPosition, MoveRepeater
from config import FOX_INTERVAL_MS, LOG_INTERVAL_MS, MOVE_INTERVAL_MS


def hand_result(direction="right", fist=False, open_palm=False, offset=(0, 0), scale=1):
    # A palm with fingers curled toward their bases, rotated in camera space.
    coords = [(0, 0)] * 21
    coords[0] = (0, 0.18)
    for base, x in zip((5, 9, 13, 17), (-0.08, -0.025, 0.035, 0.09)):
        straight = (base == 5 and not fist) or open_palm
        coords[base:base + 4] = [(x, 0), (x, -0.06),
                                 (x, -0.11 if straight else -0.03),
                                 (x, -0.17 if straight else 0.02)]
    rotations = {"up": (1, 0), "right": (0, 1), "down": (-1, 0), "left": (0, -1)}
    c, t = rotations[direction]
    hand = [SimpleNamespace(x=0.5 + offset[0] + scale * (c*x - t*y) / (640/480),
                            y=0.5 + offset[1] + scale * (t*x + c*y)) for x, y in coords]
    return SimpleNamespace(hand_landmarks=[hand])


class MovementTests(unittest.TestCase):
    def test_immediate_activation_repeat_release_and_no_catchup_burst(self):
        repeat = MoveRepeater(150)
        self.assertEqual(repeat.poll("right", 1000), "right")
        self.assertIsNone(repeat.poll("right", 1149))
        self.assertEqual(repeat.poll("right", 1150), "right")
        self.assertIsNone(repeat.poll("up", 1160))
        self.assertIsNone(repeat.poll(None, 1170))
        self.assertIsNone(repeat.poll("up", 1171))
        self.assertEqual(repeat.poll("up", 1300), "up")
        self.assertEqual(repeat.poll("up", 5000), "up")
        self.assertIsNone(repeat.poll("up", 5000))

    def test_gesture_jitter_cannot_bypass_movement_interval(self):
        repeat = MoveRepeater(MOVE_INTERVAL_MS)
        self.assertEqual(repeat.poll("right", 0), "right")
        for timestamp in range(10, MOVE_INTERVAL_MS, 10):
            direction = ("up", None, "right")[timestamp // 10 % 3]
            self.assertIsNone(repeat.poll(direction, timestamp))
        self.assertEqual(repeat.poll("left", MOVE_INTERVAL_MS), "left")

    def test_interpolation_retargets_without_jump_and_wrap_snaps(self):
        position = AnimatedPosition(1, 1, 120)
        position.move_to(2, 1, 1000)
        self.assertEqual(position.position(1060), (1.5, 1))
        position.move_to(2, 2, 1060)
        self.assertEqual(position.position(1060), (1.5, 1))
        self.assertEqual(position.position(1180), (2, 2))
        position.move_to(2, 8, 1200, snap=True)
        self.assertEqual(position.position(1200), (2, 8))


class TrackingTests(unittest.TestCase):
    def setUp(self):
        self.tracker = HandTracker()
        self.tracker._snapshot = TrackingSnapshot(status="Camera active")

    def publish(self, result, timestamp):
        with patch("hand_tracking.now_ms", return_value=timestamp + 10):
            self.tracker._on_result(result, None, timestamp)

    def test_direction_expires_and_empty_result_stops_movement(self):
        self.publish(hand_result(), 930)
        self.publish(hand_result(), 1000)
        self.assertEqual(self.tracker.snapshot(1100).direction, "right")
        self.assertEqual(self.tracker.snapshot(1100).latency_ms, 10)
        self.assertIsNone(self.tracker.snapshot(1251).direction)
        self.publish(SimpleNamespace(hand_landmarks=[]), 1100)
        self.assertIsNone(self.tracker.snapshot(1100).direction)

    def test_holding_a_fist_only_pauses_and_never_requests_quit(self):
        fist = hand_result(fist=True)
        for timestamp in range(1000, 5001, 200):
            self.publish(fist, timestamp)
            state = self.tracker.snapshot(timestamp)
            self.assertIsNone(state.direction)
            self.assertFalse(hasattr(state, "quit_requested"))
            self.assertFalse(self.tracker._stop.is_set())
        self.publish(hand_result(), 5030)
        self.publish(hand_result(), 5100)
        self.assertEqual(self.tracker.snapshot(5100).direction, "right")

    def test_preview_only_quits_for_q(self):
        self.tracker._frame = np.zeros((48, 64, 3), dtype=np.uint8)
        self.tracker._snapshot = replace(self.tracker._snapshot, frame_at=1000)
        with patch("hand_tracking.cv2.imshow"), \
             patch("hand_tracking.cv2.waitKey", side_effect=[27, ord("r"), ord("q"), ord("Q")]):
            self.assertFalse(self.tracker.show_preview())
            self.assertFalse(self.tracker.show_preview())
            self.assertTrue(self.tracker.show_preview())
            self.assertTrue(self.tracker.show_preview())

    def test_late_callback_cannot_reactivate_failed_or_closed_camera(self):
        self.tracker._snapshot = replace(self.tracker._snapshot, status="Camera read failed")
        self.publish(hand_result(), 1000)
        self.assertIsNone(self.tracker.snapshot(1000).direction)
        self.tracker._snapshot = replace(self.tracker._snapshot, status="Camera active")
        self.tracker._stop.set()
        self.publish(hand_result(), 1100)
        self.assertIsNone(self.tracker.snapshot(1100).direction)

    def test_camera_open_failure_exits_worker_and_releases_camera(self):
        with patch("hand_tracking.cv2.VideoCapture") as capture:
            capture.return_value.isOpened.return_value = False
            self.tracker.start()
            self.tracker._thread.join(2)
            self.tracker.close()
            self.assertFalse(self.tracker._thread.is_alive())
            capture.return_value.release.assert_called_once()
            self.assertIn("camera did not open", self.tracker.snapshot().status)

    def test_snapshot_does_not_wait_for_blocked_capture_and_worker_cleans_up(self):
        entered, release = Event(), Event()
        def read():
            entered.set()
            release.wait(2)
            return False, None
        with patch("hand_tracking.cv2.VideoCapture") as capture, \
             patch("hand_tracking.mp.tasks.vision.HandLandmarker.create_from_options") as create:
            capture.return_value.isOpened.return_value = True
            capture.return_value.read.side_effect = read
            self.tracker.start()
            try:
                self.assertTrue(entered.wait(2))
                started = monotonic()
                self.tracker.snapshot()
                self.assertLess(monotonic() - started, 0.1)
            finally:
                self.tracker._stop.set()
                release.set()
                self.tracker.close()
            self.assertFalse(self.tracker._thread.is_alive())
            capture.return_value.release.assert_called_once()
            create.return_value.close.assert_called_once()

    def test_capture_at_30_fps_is_not_halved_by_timestamp_rounding(self):
        timestamps = [1000 + round(frame * 1000 / 30) for frame in range(31)]
        frame_index = [-1]
        def read():
            frame_index[0] += 1
            if frame_index[0] == len(timestamps):
                self.tracker._stop.set()
                return False, None
            return True, np.zeros((48, 64, 3), dtype=np.uint8)
        with patch("hand_tracking.cv2.VideoCapture") as capture, \
             patch("hand_tracking.mp.tasks.vision.HandLandmarker.create_from_options") as create, \
             patch("hand_tracking.now_ms", side_effect=lambda: timestamps[frame_index[0]]):
            capture.return_value.isOpened.return_value = True
            capture.return_value.read.side_effect = read
            self.tracker._capture()
            self.assertEqual(create.return_value.detect_async.call_count, 31)
            submitted = [call.args[1] for call in create.return_value.detect_async.call_args_list]
            self.assertEqual(submitted, timestamps)



class GestureTests(unittest.TestCase):
    def test_pointing_works_in_all_directions_at_different_positions_and_sizes(self):
        for direction in ("up", "down", "left", "right"):
            for offset, scale in (((0, 0), 1), ((0.2, -0.15), 0.6), ((-0.15, 0.1), 1.4)):
                with self.subTest(direction=direction, offset=offset, scale=scale):
                    controller = GestureController()
                    hand = hand_result(direction, offset=offset, scale=scale).hand_landmarks[0]
                    self.assertIsNone(controller.update(hand, 1000)[0])
                    self.assertEqual(controller.update(hand, 1070)[0], direction)

    def test_open_hand_fist_and_lost_hand_stop_immediately(self):
        for stop in (hand_result(fist=True).hand_landmarks[0],
                     hand_result(open_palm=True).hand_landmarks[0], None):
            controller = GestureController()
            hand = hand_result().hand_landmarks[0]
            controller.update(hand, 1000)
            self.assertEqual(controller.update(hand, 1070)[0], "right")
            self.assertIsNone(controller.update(stop, 1080)[0])
            self.assertIsNone(controller.update(hand, 1090)[0])

    def test_brief_wrong_direction_does_not_turn_and_sustained_turn_does(self):
        controller = GestureController()
        right = hand_result().hand_landmarks[0]
        up = hand_result("up").hand_landmarks[0]
        controller.update(right, 1000)
        self.assertEqual(controller.update(right, 1070)[0], "right")
        self.assertEqual(controller.update(up, 1100)[0], "right")
        self.assertEqual(controller.update(right, 1130)[0], "right")
        for timestamp in range(1160, 1401, 30):
            direction = controller.update(up, timestamp)[0]
        self.assertEqual(direction, "up")

    def test_long_detection_gap_requires_a_fresh_stable_gesture(self):
        controller = GestureController()
        hand = hand_result().hand_landmarks[0]
        controller.update(hand, 1000)
        self.assertEqual(controller.update(hand, 1070)[0], "right")
        self.assertIsNone(controller.update(hand, 1500)[0])

    def test_diagonal_noise_keeps_current_axis(self):
        controller = GestureController()
        hand = hand_result().hand_landmarks[0]
        controller.update(hand, 1000)
        controller.update(hand, 1070)
        # Rotate a right-pointing hand slightly past 45 degrees, inside hysteresis.
        from math import cos, sin, radians
        angle = radians(-48)
        for point in hand:
            x, y = (point.x - 0.5) * (640/480), point.y - 0.5
            point.x = 0.5 + (x*cos(angle) - y*sin(angle)) / (640/480)
            point.y = 0.5 + x*sin(angle) + y*cos(angle)
        for timestamp in range(1100, 1401, 30):
            self.assertEqual(controller.update(hand, timestamp)[0], "right")

    def test_preview_draws_detected_hand_and_arrow(self):
        hand = hand_result().hand_landmarks[0]
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        state = TrackingSnapshot(status="Camera active", direction="right", gesture="Pointing",
                                 landmarks=tuple((p.x, p.y) for p in hand), vector=(1, 0))
        preview = draw_control_preview(frame, state)
        self.assertEqual(preview.shape, frame.shape)
        self.assertTrue(preview[150:350].any())
        self.assertFalse(frame.any())


class GameLoopTests(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_escape_is_ignored_and_q_quits_gameplay(self):
        batches = iter(([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)],
                        [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q)]))
        with patch("game.pygame.event.get", side_effect=lambda: next(batches)) as events, \
             patch("game.pygame.key.get_pressed", return_value=defaultdict(bool)):
            self.assertEqual(game.run_game(), "quit")
        self.assertEqual(events.call_count, 2)

    def test_q_quits_intro_instead_of_starting_the_game(self):
        from main import show_intro
        pygame.init()
        screen = pygame.display.set_mode((960, 704))
        with patch("main.pygame.event.get", return_value=[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q)]):
            self.assertFalse(show_intro(screen))

    def simulate(self, level=0, dt=16, hold=False, gesture=False):
        frame = [0]
        animations = []
        key_state = defaultdict(bool)

        class RecordedPosition(AnimatedPosition):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.moves = []
                animations.append(self)

            def move_to(self, x, y, timestamp, snap=False):
                self.moves.append((x, y, timestamp, snap))
                super().move_to(x, y, timestamp, snap)

        class Clock:
            def tick(self, fps):
                frame[0] += 1
                return dt

            def get_fps(self):
                return 1000 / dt

        def events():
            timestamp = frame[0] * dt
            if timestamp >= 2 * max(LOG_INTERVAL_MS, FOX_INTERVAL_MS) + dt:
                return [pygame.event.Event(pygame.QUIT)]
            result = []
            if frame[0] == 1:
                result.append(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F3))
                if hold:
                    key_state[pygame.K_RIGHT] = True
                    result.append(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
            if timestamp >= 4 * MOVE_INTERVAL_MS:
                key_state[pygame.K_RIGHT] = False
            return result

        tracker = None
        if gesture:
            tracker = SimpleNamespace(
                show_preview=lambda: False,
                snapshot=lambda now: TrackingSnapshot(direction="right" if now < 4 * MOVE_INTERVAL_MS else None,
                                                       status="Camera active"))
        with patch("game.AnimatedPosition", RecordedPosition), \
             patch("game.pygame.time.Clock", Clock), \
             patch("game.pygame.event.get", side_effect=events), \
             patch("game.pygame.key.get_pressed", return_value=key_state), \
             patch("game.now_ms", side_effect=lambda: frame[0] * dt):
            self.assertEqual(game.run_game(level, tracker), "quit")
        return animations

    def test_held_keyboard_and_hand_repeat_then_stop(self):
        for options in ({"hold": True}, {"gesture": True}):
            with self.subTest(options=options):
                player, = self.simulate(**options)
                self.assertEqual([(x, y) for x, y, _, _ in player.moves],
                                 [(2, 1), (3, 1), (4, 1), (5, 1)])
                self.assertTrue(all(b[2] - a[2] >= MOVE_INTERVAL_MS
                                    for a, b in zip(player.moves, player.moves[1:])))

    def test_hazards_keep_intervals_at_different_render_rates(self):
        for dt in (10, 16, 100, 250):
            with self.subTest(dt=dt):
                logs = self.simulate(level=1, dt=dt)[:-1]
                self.assertEqual(len(logs), 6)
                for log in logs:
                    self.assertEqual(len(log.moves), 2)
                    self.assertGreaterEqual(log.moves[0][2], LOG_INTERVAL_MS)
                    self.assertGreaterEqual(log.moves[1][2], 2 * LOG_INTERVAL_MS)
                fox, player = self.simulate(level=2, dt=dt)
                self.assertEqual(len(fox.moves), 2)
                self.assertGreaterEqual(fox.moves[0][2], FOX_INTERVAL_MS)
                self.assertGreaterEqual(fox.moves[1][2], 2 * FOX_INTERVAL_MS)
                self.assertFalse(player.moves)


if __name__ == "__main__":
    unittest.main()

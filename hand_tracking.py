"""Independent webcam capture with asynchronous, latest-result hand tracking.

Only the main thread renders the embedded preview. The capture thread owns the camera and
landmarker; callbacks publish small snapshots under a lock, never game state.
"""

from dataclasses import dataclass, replace
from math import exp, hypot
from pathlib import Path
from threading import Event, Lock, Thread
from time import monotonic

import cv2
import mediapipe as mp
import pygame

from config import (CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS, TRACKING_STALE_MS,
                    GESTURE_SMOOTHING_MS, GESTURE_SETTLE_MS,
                    GESTURE_AXIS_HYSTERESIS)


def now_ms():
    return int(monotonic() * 1000)


# Explicit connections keep drawing independent of MediaPipe's legacy solutions API.
HAND_CONNECTIONS = ((0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6),
                    (6, 7), (7, 8), (5, 9), (9, 10), (10, 11), (11, 12),
                    (9, 13), (13, 14), (14, 15), (15, 16), (13, 17),
                    (0, 17), (17, 18), (18, 19), (19, 20))


def finger_extended(hand, base, joint, tip, aspect):
    """Recognize straight fingers geometrically, regardless of hand rotation."""
    a = ((hand[base].x - hand[joint].x) * aspect, hand[base].y - hand[joint].y)
    b = ((hand[tip].x - hand[joint].x) * aspect, hand[tip].y - hand[joint].y)
    lengths = hypot(*a) * hypot(*b)
    if lengths < 1e-6:
        return False
    cosine = (a[0] * b[0] + a[1] * b[1]) / lengths
    return cosine < -0.65 and hypot(*b) > hypot(*a) * 0.45


class GestureController:
    """Smooth a pointing vector and debounce turns; stop gestures act immediately."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.vector = None
        self.last_at = 0
        self.direction = self.candidate = None
        self.candidate_at = 0

    def update(self, hand, timestamp, aspect=CAMERA_WIDTH / CAMERA_HEIGHT):
        if not hand:
            self.reset()
            return None, "No hand", None
        extended = [finger_extended(hand, base, base + 1, base + 3, aspect)
                    for base in (5, 9, 13, 17)]
        if not extended[0] or any(extended[1:]):
            self.reset()
            gesture = "Fist / rest" if not any(extended) else "Open hand / rest"
            return None, gesture, None
        dx = (hand[8].x - hand[5].x) * aspect
        dy = hand[8].y - hand[5].y
        length = hypot(dx, dy)
        if length < 0.025:
            self.reset()
            return None, "Point across the camera", None
        vector = (dx / length, dy / length)
        if self.vector is None or timestamp - self.last_at > TRACKING_STALE_MS:
            self.reset()
            self.vector = vector
        else:
            alpha = 1 - exp(-max(1, timestamp - self.last_at) / GESTURE_SMOOTHING_MS)
            self.vector = tuple(old + alpha * (new - old)
                                for old, new in zip(self.vector, vector))
        self.last_at = timestamp
        x, y = self.vector
        horizontal = abs(x) > abs(y)
        # Keep the current axis near diagonals instead of flickering between turns.
        if self.direction in ("left", "right") and abs(y) < abs(x) * GESTURE_AXIS_HYSTERESIS:
            horizontal = True
        elif self.direction in ("up", "down") and abs(x) < abs(y) * GESTURE_AXIS_HYSTERESIS:
            horizontal = False
        candidate = ("right" if x > 0 else "left") if horizontal else ("down" if y > 0 else "up")
        if candidate != self.candidate:
            self.candidate, self.candidate_at = candidate, timestamp
        if timestamp - self.candidate_at >= GESTURE_SETTLE_MS:
            self.direction = candidate
        return self.direction, "Pointing", self.vector


@dataclass(frozen=True)
class TrackingSnapshot:
    direction: str | None = None
    result_at: int = 0
    frame_at: int = 0
    status: str = "Starting camera"
    landmarks: tuple = ()
    gesture: str = "No hand"
    vector: tuple | None = None


def draw_control_preview(frame, state):
    """Render detected geometry and gesture feedback on the mirrored camera."""
    preview = frame.copy()
    height, width = preview.shape[:2]
    color = (90, 240, 120) if state.direction else (0, 210, 255)

    def point(landmark):
        return (int(landmark[0] * width), int(landmark[1] * height))

    if state.landmarks:
        points = [point(p) for p in state.landmarks]
        for a, b in HAND_CONNECTIONS:
            cv2.line(preview, points[a], points[b], color, 2, cv2.LINE_AA)
        for p in points:
            cv2.circle(preview, p, 4, (255, 255, 255), -1, cv2.LINE_AA)
        if state.vector is not None:
            origin = points[5]
            vx, vy = state.vector
            end = (int(origin[0] + vx * 90), int(origin[1] + vy * 90))
            cv2.arrowedLine(preview, origin, end, color, 4, cv2.LINE_AA, tipLength=0.25)
            cv2.circle(preview, points[8], 9, color, 2, cv2.LINE_AA)

    return preview


class HandTracker:
    def __init__(self, camera_index=0, model_path=None):
        self.camera_index = camera_index
        self.model_path = str(model_path or Path(__file__).with_name("hand_landmarker.task"))
        self._lock = Lock()
        self._stop = Event()
        self._snapshot = TrackingSnapshot()
        self._frame = None
        self._thread = Thread(target=self._capture, name="hand-camera", daemon=True)
        self._preview_key = None
        self._preview_surface = None
        self._gestures = GestureController()

    def start(self):
        self._thread.start()
        return self

    def snapshot(self, timestamp_ms=None):
        timestamp_ms = now_ms() if timestamp_ms is None else timestamp_ms
        with self._lock:
            state = self._snapshot
        if (self._stop.is_set() or state.status != "Camera active" or not state.result_at
                or timestamp_ms - state.result_at > TRACKING_STALE_MS):
            return replace(state, direction=None, landmarks=(),
                           vector=None, gesture="No hand" if state.status == "Camera active" else state.status)
        return state

    def _on_result(self, result, output_image, timestamp_ms):
        with self._lock:
            previous = self._snapshot
            if self._stop.is_set() or previous.status != "Camera active":
                return
            hand = result.hand_landmarks[0] if result.hand_landmarks else None
            aspect = (self._frame.shape[1] / self._frame.shape[0]
                      if self._frame is not None else CAMERA_WIDTH / CAMERA_HEIGHT)
            direction, gesture, vector = self._gestures.update(hand, timestamp_ms, aspect)
            landmarks = tuple((p.x, p.y) for p in hand) if hand else ()
            self._snapshot = replace(previous, direction=direction,
                                     landmarks=landmarks, gesture=gesture, vector=vector,
                                     result_at=timestamp_ms)

    def _capture(self):
        cap = detector = None
        try:
            cap = cv2.VideoCapture(self.camera_index)
            if not cap.isOpened():
                raise RuntimeError("camera did not open")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Backend may ignore this hint.
            options = mp.tasks.vision.HandLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=self.model_path),
                running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
                num_hands=1, min_hand_detection_confidence=0.6,
                min_hand_presence_confidence=0.6, min_tracking_confidence=0.6,
                result_callback=self._on_result)
            detector = mp.tasks.vision.HandLandmarker.create_from_options(options)
            last_timestamp = 0
            next_submission = 0.0
            submission_interval = 1000 / CAMERA_FPS
            failures = 0
            while not self._stop.is_set():
                ok, frame = cap.read()
                if not ok or frame is None:
                    failures += 1
                    with self._lock:
                        self._snapshot = replace(self._snapshot, direction=None,
                                                 result_at=0, status="Camera read failed")
                    if failures >= 10:
                        raise RuntimeError("camera stopped delivering frames")
                    self._stop.wait(0.05)
                    continue
                failures = 0
                timestamp = max(now_ms(), last_timestamp + 1)
                last_timestamp = timestamp
                frame = cv2.flip(frame, 1)
                with self._lock:
                    self._frame = frame
                    self._snapshot = replace(self._snapshot, frame_at=timestamp,
                                             status="Camera active")
                # Drain capture continuously, targeting CAMERA_FPS. MediaPipe
                # drops submissions while busy, so no queue of stale frames develops.
                # Allow 1 ms for integer timestamp rounding at e.g. 30 FPS.
                if timestamp + 1 >= next_submission:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    detector.detect_async(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb),
                                          timestamp)
                    if next_submission == 0:
                        next_submission = float(timestamp)
                    intervals = int(max(0, timestamp - next_submission) / submission_interval) + 1
                    next_submission += intervals * submission_interval
        except Exception as exc:
            message = f"Hand tracking unavailable: {exc}"
            print(f"{message}; keyboard controls remain available")
            with self._lock:
                self._snapshot = replace(self._snapshot, status=message,
                                         direction=None, result_at=0)
        finally:
            try:
                if detector is not None:
                    detector.close()
            finally:
                if cap is not None:
                    cap.release()

    def preview_surface(self, size):
        """Return a cached Pygame preview and fresh tracking state without blocking."""
        timestamp = now_ms()
        with self._lock:
            frame, frame_at = self._frame, self._snapshot.frame_at
        state = self.snapshot(timestamp)
        if frame is None or timestamp - frame_at > TRACKING_STALE_MS:
            return None, state
        key = (frame_at, state.result_at, state.direction, state.gesture, state.status, size)
        if key != self._preview_key:
            preview = draw_control_preview(frame, state)
            rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
            surface = pygame.image.frombuffer(rgb.tobytes(), (rgb.shape[1], rgb.shape[0]), 'RGB').convert()
            self._preview_surface = pygame.transform.smoothscale(surface, size)
            self._preview_key = key
        return self._preview_surface, state

    def close(self):
        self._stop.set()
        # A broken webcam driver must not hold up application shutdown indefinitely.
        self._thread.join(timeout=2)
        if self._thread.is_alive():
            print("Camera driver is still shutting down")

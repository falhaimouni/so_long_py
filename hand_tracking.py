"""Independent webcam capture with asynchronous, latest-result hand tracking.

Only the main thread displays windows. The capture thread owns the camera and
landmarker; callbacks publish small snapshots under a lock, never game state.
"""

from dataclasses import dataclass, replace
from pathlib import Path
from threading import Event, Lock, Thread
from time import monotonic

import cv2
import mediapipe as mp

from config import (CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS, TRACKING_STALE_MS,
                    ZONE_LOW, ZONE_HIGH)


def now_ms():
    return int(monotonic() * 1000)


def is_fist(hand):
    return all(hand[tip].y > hand[pip].y
               for tip, pip in zip((8, 12, 16, 20), (6, 10, 14, 18)))


def hand_direction(hand):
    tip = hand[8]
    if tip.y < ZONE_LOW:
        return "up"
    if tip.y > ZONE_HIGH:
        return "down"
    if tip.x < ZONE_LOW:
        return "left"
    if tip.x > ZONE_HIGH:
        return "right"
    return None


@dataclass(frozen=True)
class TrackingSnapshot:
    direction: str | None = None
    tip: tuple | None = None
    result_at: int = 0
    latency_ms: int | None = None
    frame_at: int = 0
    capture_fps: float = 0.0
    status: str = "Starting camera"


def draw_control_preview(frame, state):
    """Show the same direction zones used by hand_direction on the mirrored frame."""
    preview = frame.copy()
    height, width = preview.shape[:2]
    left, right = int(width * ZONE_LOW), int(width * ZONE_HIGH)
    top, bottom = int(height * ZONE_LOW), int(height * ZONE_HIGH)
    # Vertical directions take priority in the corners, matching hand_direction.
    zones = {
        "up": (0, 0, width - 1, top),
        "down": (0, bottom, width - 1, height - 1),
        "left": (0, top, left, bottom),
        "right": (right, top, width - 1, bottom),
        "center": (left, top, right, bottom),
    }
    active = state.direction or ("center" if state.tip is not None and
                                ZONE_LOW <= state.tip[0] <= ZONE_HIGH and
                                ZONE_LOW <= state.tip[1] <= ZONE_HIGH else None)
    if active in zones:
        x1, y1, x2, y2 = zones[active]
        tint = preview.copy()
        cv2.rectangle(tint, (x1, y1), (x2, y2), (80, 190, 80), -1)
        cv2.addWeighted(tint, 0.2, preview, 0.8, 0, dst=preview)

    font = cv2.FONT_HERSHEY_SIMPLEX

    def label(text, x, y, scale=0.65, color=(255, 255, 255)):
        cv2.putText(preview, text, (x, y), font, scale, (15, 15, 15), 4, cv2.LINE_AA)
        cv2.putText(preview, text, (x, y), font, scale, color, 1, cv2.LINE_AA)

    cv2.line(preview, (0, top), (width - 1, top), (220, 220, 220), 1)
    cv2.line(preview, (0, bottom), (width - 1, bottom), (220, 220, 220), 1)
    for x in (left, right):
        cv2.line(preview, (x, top), (x, bottom), (220, 220, 220), 1)
    for direction, (x1, y1, x2, y2) in zones.items():
        text = "CENTER / REST" if direction == "center" else direction.upper()
        text_width = cv2.getTextSize(text, font, 0.65, 1)[0][0]
        color = (100, 255, 100) if direction == active else (255, 255, 255)
        label(text, max(4, (x1 + x2 - text_width) // 2), (y1 + y2) // 2 + 8,
              color=color)

    if state.tip is not None:
        x = max(0, min(width - 1, int(state.tip[0] * width)))
        y = max(0, min(height - 1, int(state.tip[1] * height)))
        cv2.circle(preview, (x, y), 12, (15, 15, 15), 3)
        cv2.circle(preview, (x, y), 10, (0, 255, 255), 2)
        cv2.circle(preview, (x, y), 3, (0, 255, 255), -1)
        text = "FINGER: " + (state.direction.upper() if state.direction else "REST")
        text_width = cv2.getTextSize(text, font, 0.55, 1)[0][0]
        label(text, max(4, min(x + 16, width - text_width - 4)),
              max(22, min(y - 16, height - 8)), scale=0.55, color=(0, 255, 255))
    else:
        label("No finger detected", 12, 28, scale=0.55)
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
        self._preview_at = 0

    def start(self):
        self._thread.start()
        return self

    def snapshot(self, timestamp_ms=None):
        timestamp_ms = now_ms() if timestamp_ms is None else timestamp_ms
        with self._lock:
            state = self._snapshot
        if (self._stop.is_set() or state.status != "Camera active" or not state.result_at
                or timestamp_ms - state.result_at > TRACKING_STALE_MS):
            return replace(state, direction=None, tip=None)
        return state

    def _on_result(self, result, output_image, timestamp_ms):
        with self._lock:
            previous = self._snapshot
            if self._stop.is_set() or previous.status != "Camera active":
                return
            direction, tip = None, None
            if result.hand_landmarks:
                hand = result.hand_landmarks[0]
                tip = (hand[8].x, hand[8].y)
                # A closed hand pauses movement; gestures never request shutdown.
                if not is_fist(hand):
                    direction = hand_direction(hand)
            self._snapshot = replace(previous, direction=direction, tip=tip,
                                     result_at=timestamp_ms,
                                     latency_ms=max(0, now_ms() - timestamp_ms))

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
                num_hands=1, result_callback=self._on_result)
            detector = mp.tasks.vision.HandLandmarker.create_from_options(options)
            last_timestamp = 0
            next_submission = 0.0
            submission_interval = 1000 / CAMERA_FPS
            fps_started = monotonic()
            frames = failures = 0
            while not self._stop.is_set():
                ok, frame = cap.read()
                if not ok or frame is None:
                    failures += 1
                    with self._lock:
                        self._snapshot = replace(self._snapshot, direction=None,
                                                 tip=None,
                                                 result_at=0, status="Camera read failed")
                    if failures >= 10:
                        raise RuntimeError("camera stopped delivering frames")
                    self._stop.wait(0.05)
                    continue
                failures = 0
                timestamp = max(now_ms(), last_timestamp + 1)
                last_timestamp = timestamp
                frame = cv2.flip(frame, 1)
                frames += 1
                elapsed = monotonic() - fps_started
                with self._lock:
                    self._frame = frame
                    self._snapshot = replace(self._snapshot, frame_at=timestamp,
                                             status="Camera active")
                    if elapsed >= 1:
                        self._snapshot = replace(self._snapshot, capture_fps=frames / elapsed)
                if elapsed >= 1:
                    fps_started, frames = monotonic(), 0
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

    def show_preview(self):
        """Display at camera pace on the UI thread, without waiting for capture."""
        with self._lock:
            frame, frame_at = self._frame, self._snapshot.frame_at
        if frame is not None and frame_at != self._preview_at:
            state = self.snapshot()
            preview = draw_control_preview(frame, state)
            cv2.imshow("Camera Preview", preview)
            self._preview_at = frame_at
        return (cv2.waitKey(1) & 0xFF) in (ord("q"), ord("Q")) if frame is not None else False

    def close(self):
        self._stop.set()
        # A broken webcam driver must not hold up application shutdown indefinitely.
        self._thread.join(timeout=2)
        if self._thread.is_alive():
            print("Camera driver is still shutting down")

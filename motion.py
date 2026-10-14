"""Time-based input repetition and drawing positions, independent of rendering FPS."""


class MoveRepeater:
    def __init__(self, interval_ms):
        self.interval_ms = interval_ms
        self.direction = None
        self.next_move_at = 0

    def poll(self, direction, now_ms):
        """Move immediately on activation/change, then repeat without catch-up bursts."""
        changed = direction != self.direction
        self.direction = direction
        if direction is None:
            return None
        if changed or now_ms >= self.next_move_at:
            self.next_move_at = now_ms + self.interval_ms
            return direction
        return None


class AnimatedPosition:
    def __init__(self, x, y, duration_ms=120):
        self.start = self.target = (x, y)
        self.started_at = 0
        self.duration_ms = duration_ms

    def position(self, now_ms):
        progress = min(1.0, max(0.0, (now_ms - self.started_at) / self.duration_ms))
        return tuple(a + (b - a) * progress for a, b in zip(self.start, self.target))

    def move_to(self, x, y, now_ms, snap=False):
        self.start = (x, y) if snap else self.position(now_ms)
        self.target = (x, y)
        self.started_at = now_ms

"""Configuration constants for the so_long game."""

TEXTURES_FOLDER = "textures"

# Rendering and gameplay timings (milliseconds unless noted)
TARGET_FPS = 60
# Give hand gestures time to settle while preserving the relative game pace.
GAMEPLAY_TIME_SCALE = 2.8
# Slightly quicker player steps; animation fills each interval for continuous motion.
MOVE_INTERVAL_MS = round(150 * GAMEPLAY_TIME_SCALE * 6 / 7)
ANIMATION_MS = MOVE_INTERVAL_MS
LOG_INTERVAL_MS = round(500 * GAMEPLAY_TIME_SCALE)
FOX_INTERVAL_MS = round(450 * GAMEPLAY_TIME_SCALE)
PORTAL_FOX_INTERVAL_MS = round(600 * GAMEPLAY_TIME_SCALE)
PORTAL_FOX_GRACE_MS = round(1200 * GAMEPLAY_TIME_SCALE)

# Hazards switch directly from quiet to active; keep the original strike cadence.
LIGHTNING_SAFE_MS = round(2700 * GAMEPLAY_TIME_SCALE)
LIGHTNING_ACTIVE_MS = round(600 * GAMEPLAY_TIME_SCALE)
TIDE_SAFE_MS = round(5400 * GAMEPLAY_TIME_SCALE)
TIDE_ACTIVE_MS = round(900 * GAMEPLAY_TIME_SCALE)
PLANK_LIFETIME_MS = round(900 * GAMEPLAY_TIME_SCALE)

# Camera settings are requests; actual support depends on the webcam/backend.
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
TRACKING_STALE_MS = 250
# Time-based vector filtering and turn confirmation reduce landmark jitter.
GESTURE_SMOOTHING_MS = 45
GESTURE_SETTLE_MS = 30
GESTURE_AXIS_HYSTERESIS = 1.25

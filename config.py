"""Configuration constants for the so_long game."""

TEXTURES_FOLDER = "textures"

# Rendering and gameplay timings (milliseconds unless noted)
TARGET_FPS = 60
# Give hand gestures time to settle while preserving the relative game pace.
GAMEPLAY_TIME_SCALE = 2.8
MOVE_INTERVAL_MS = round(150 * GAMEPLAY_TIME_SCALE)
ANIMATION_MS = round(120 * GAMEPLAY_TIME_SCALE)
LOG_INTERVAL_MS = round(500 * GAMEPLAY_TIME_SCALE)
FOX_INTERVAL_MS = round(450 * GAMEPLAY_TIME_SCALE)
PORTAL_FOX_INTERVAL_MS = round(600 * GAMEPLAY_TIME_SCALE)
PORTAL_FOX_GRACE_MS = round(1200 * GAMEPLAY_TIME_SCALE)

# Amber/blue warnings precede lethal lightning and tidal surges.
LIGHTNING_SAFE_MS = round(1800 * GAMEPLAY_TIME_SCALE)
LIGHTNING_WARNING_MS = round(900 * GAMEPLAY_TIME_SCALE)
LIGHTNING_ACTIVE_MS = round(600 * GAMEPLAY_TIME_SCALE)
TIDE_SAFE_MS = round(4200 * GAMEPLAY_TIME_SCALE)
TIDE_WARNING_MS = round(1200 * GAMEPLAY_TIME_SCALE)
TIDE_ACTIVE_MS = round(900 * GAMEPLAY_TIME_SCALE)
PLANK_LIFETIME_MS = round(900 * GAMEPLAY_TIME_SCALE)

# Camera settings are requests; actual support depends on the webcam/backend.
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
TRACKING_STALE_MS = 250
ZONE_LOW = 0.30
ZONE_HIGH = 0.70

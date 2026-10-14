"""Configuration constants for the so_long game."""

TEXTURES_FOLDER = "textures"

# Rendering and gameplay timings (milliseconds unless noted)
TARGET_FPS = 60
MOVE_INTERVAL_MS = 150
ANIMATION_MS = 120
LOG_INTERVAL_MS = 500
FOX_INTERVAL_MS = 450
PORTAL_FOX_INTERVAL_MS = 600
PORTAL_FOX_GRACE_MS = 1200

# Amber/blue warnings precede lethal lightning and tidal surges.
LIGHTNING_SAFE_MS = 1800
LIGHTNING_WARNING_MS = 900
LIGHTNING_ACTIVE_MS = 600
TIDE_SAFE_MS = 4200
TIDE_WARNING_MS = 1200
TIDE_ACTIVE_MS = 900
PLANK_LIFETIME_MS = 900

# Camera settings are requests; actual support depends on the webcam/backend.
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
TRACKING_STALE_MS = 250
ZONE_LOW = 0.35
ZONE_HIGH = 0.65

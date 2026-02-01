"""
Constants and configuration values for the smart traffic system.
"""

# Traffic light timing defaults (in seconds)
DEFAULT_GREEN_TIME = 30
DEFAULT_YELLOW_TIME = 3
DEFAULT_RED_TIME = 30

# Video processing
DEFAULT_FPS = 30
VIDEO_FRAME_SKIP = 2

# Detection thresholds
MIN_VEHICLE_CONFIDENCE = 0.5
MAX_TRACKING_DISTANCE = 50

# System settings
LOG_LEVEL = "INFO"
ENABLE_DEBUG_MODE = False

# Traffic density thresholds
LOW_DENSITY_THRESHOLD = 5
MEDIUM_DENSITY_THRESHOLD = 15
HIGH_DENSITY_THRESHOLD = 30

# Colors for visualization (RGB)
COLOR_GREEN = (0, 255, 0)
COLOR_YELLOW = (255, 255, 0)
COLOR_RED = (255, 0, 0)
COLOR_BLUE = (0, 0, 255)
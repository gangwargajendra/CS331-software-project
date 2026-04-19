"""Configuration for traffic simulation and API runtime."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


def _load_env_file_fallback(path: str):
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ[key] = value


if load_dotenv is not None:
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    _load_env_file_fallback(ENV_PATH)


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return default if value is None else value


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# ========================
# Paths
# ========================
PHOTO_DIR = os.path.join(BASE_DIR, 'photo')

# ========================
# Signal Timing (seconds)
# ========================
GREEN_LIGHT_DURATION = _env_int("GREEN_LIGHT_DURATION", 15)
YELLOW_LIGHT_DURATION = _env_int("YELLOW_LIGHT_DURATION", 4)

# ========================
# Traffic Generation
# ========================
# Min seconds between spawns per side
SPAWN_INTERVAL_MIN = _env_float("SPAWN_INTERVAL_MIN", 2.0)
# Max seconds between spawns per side
SPAWN_INTERVAL_MAX = _env_float("SPAWN_INTERVAL_MAX", 4.0)
MAX_VEHICLES_PER_SIDE = _env_int("MAX_VEHICLES_PER_SIDE", 8)
# Seconds to wait after green before vehicles move
GREEN_START_DELAY = _env_float("GREEN_START_DELAY", 2.0)

# ========================
# Vehicle Properties
# ========================
# Pixels per frame (smooth movement)
VEHICLE_SPEED = _env_int("VEHICLE_SPEED", 2)

# Display sizes (width x length) for scaling images
VEHICLE_DISPLAY_SIZES = {
    'CAR': (35, 55),
    'TRUCK': (38, 65),
    'AMBULANCE': (35, 58)
}

# Vehicle type spawn probabilities (must sum to 1.0)
VEHICLE_PROBABILITIES = {
    'CAR': 0.67,
    'TRUCK': 0.28,
    'AMBULANCE': 0.05
}

# Vehicle image files (inside photo/ folder)
VEHICLE_IMAGES = {
    'CAR': ['car.jpg', 'car1.png', 'car2.jpg', 'car3.jpg', 'car4.png'],
    'TRUCK': ['truck.png', 'truck1.jpg', 'truck3.jpg', 'truck4.png', 'truck5.jpg'],
    'AMBULANCE': ['ambulance.jpg']
}

# Image base direction: "UP" if images face north, "RIGHT" if they face east
IMAGE_FACES = "UP"

# Per-image facing direction (the direction the raw image points).
# After loading, each image is pre-rotated so it faces UP.
# Options: "UP", "DOWN", "LEFT", "RIGHT"
IMAGE_DIRECTION = {
    'car.jpg':       'RIGHT',    # wide side-view, faces right
    'car1.png':      'LEFT',     # square, faces left
    'car2.jpg':      'RIGHT',    # wide side-view, faces right
    'car3.jpg':      'UP',       # square, faces up
    'car4.png':      'RIGHT',    # wide side-view, faces right
    'truck.png':     'UP',       # tall, faces up
    'truck1.jpg':    'LEFT',     # wide side-view, faces left
    'truck3.jpg':    'UP',       # tall, faces up
    'truck4.png':    'RIGHT',    # wide side-view, faces right
    'truck5.jpg':    'LEFT',     # wide side-view, faces left
    'ambulance.jpg': 'UP',       # square, faces up
}

# ========================
# License Plate
# ========================
LICENSE_PLATE_STATES = ['UP', 'DL', 'MH',
                        'KA', 'TN', 'HR', 'RJ', 'GJ', 'MP', 'WB']
LICENSE_PLATE_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

# ========================
# Display Settings
# ========================
FULLSCREEN = _env_bool("FULLSCREEN", False)
RESIZABLE_WINDOW = _env_bool("RESIZABLE_WINDOW", True)
WINDOW_WIDTH = _env_int("WINDOW_WIDTH", 1400)
WINDOW_HEIGHT = _env_int("WINDOW_HEIGHT", 850)
MIN_WINDOW_WIDTH = _env_int("MIN_WINDOW_WIDTH", 900)
MIN_WINDOW_HEIGHT = _env_int("MIN_WINDOW_HEIGHT", 650)
FPS = _env_int("FPS", 60)

# ========================
# Colors (RGB)
# ========================
COLOR_BACKGROUND = (34, 40, 49)
COLOR_ROAD = (68, 68, 68)
COLOR_ROAD_LINE = (255, 255, 255)
COLOR_ROAD_MARKING = (255, 255, 100)
COLOR_SIGNAL_RED = (231, 76, 60)
COLOR_SIGNAL_YELLOW = (241, 196, 15)
COLOR_SIGNAL_GREEN = (46, 204, 113)
COLOR_TEXT = (255, 255, 255)

# ========================
# Intersection Layout
# ========================
ROAD_WIDTH = _env_int("ROAD_WIDTH", 220)
# Center of each lane from road center (~55px)
LANE_OFFSET = ROAD_WIDTH // 4
SIGNAL_SIZE = _env_int("SIGNAL_SIZE", 25)
# Distance from center to stop line
STOP_LINE_OFFSET = _env_int("STOP_LINE_OFFSET", 130)
# Distance from center to spawn point (near screen edge)
SPAWN_DISTANCE = _env_int("SPAWN_DISTANCE", 550)

# ========================
# Vehicle Spacing
# ========================
# Minimum gap between vehicles in queue
MIN_FOLLOWING_DISTANCE = _env_int("MIN_FOLLOWING_DISTANCE", 70)

# ========================
# Emergency Vehicle Settings
# ========================
# Pixels before stop-line to trigger preemption
EMERGENCY_DETECTION_DISTANCE = _env_int("EMERGENCY_DETECTION_DISTANCE", 350)

# ========================
# Traffic Violation Settings
# ========================
# ~1 in 67 vehicles (cars/trucks only)
SIDE_LANE_VIOLATION_RATE = _env_float("SIDE_LANE_VIOLATION_RATE", 0.015)

# ========================
# MySQL Settings (Traffic Violations)
# ========================
DB_HOST = _env_str("DB_HOST", "localhost")
DB_PORT = _env_int("DB_PORT", 3306)
DB_NAME = _env_str("DB_NAME", "smart_traffic_db")
DB_USER = _env_str("DB_USER", "root")
DB_PASSWORD = _env_str("DB_PASSWORD", "123Candle123@")

# ========================
# API Server Settings
# ========================
API_HOST = _env_str("API_HOST", "0.0.0.0")
API_PORT = _env_int("API_PORT", _env_int("PORT", 5000))
API_DEBUG = _env_bool("API_DEBUG", False)
ALLOWED_ORIGIN = _env_str("ALLOWED_ORIGIN", "*")
SESSION_TIMEOUT_SECONDS = _env_int("SESSION_TIMEOUT_SECONDS", 15 * 60)
ENABLE_DESKTOP_SIM_UI = _env_bool("ENABLE_DESKTOP_SIM_UI", False)
QUIET_HTTP_LOGS = _env_bool("QUIET_HTTP_LOGS", True)

"""
Configuration file for Smart Traffic Signal System
Contains all timing parameters, thresholds, and paths
"""

import os

# ==================== PROJECT PATHS ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_DIR = os.path.join(BASE_DIR, "video")
LOGS_DIR = os.path.join(BASE_DIR, "smart_traffic_system", "logs")
MODEL_PATH = os.path.join(BASE_DIR, "yolov8n.pt")

# ==================== VIDEO SOURCES ====================
VIDEO_SOURCES = {
    "NORTH": os.path.join(VIDEO_DIR, "north_side.mp4"),
    "SOUTH": os.path.join(VIDEO_DIR, "south_side.mp4"),
    "EAST": os.path.join(VIDEO_DIR, "east_side.mp4"),
    "WEST": os.path.join(VIDEO_DIR, "west_side.mp4")
}

# ==================== TRAFFIC SIGNAL TIMING (seconds) ====================
# Maximum green light duration
MAX_GREEN_TIME = 30

# Minimum green light duration (safety requirement)
MIN_GREEN_TIME = 10

# Yellow/Orange light duration
YELLOW_TIME = 5

# All red time (safety buffer between signals)
ALL_RED_TIME = 2

# ==================== VEHICLE DETECTION ====================
# YOLO model confidence threshold
DETECTION_CONFIDENCE = 0.4

# YOLO class IDs for different vehicle types
VEHICLE_CLASSES = {
    "car": 2,
    "motorcycle": 3,
    "bus": 5,
    "truck": 7
}

# Emergency vehicle class IDs
EMERGENCY_CLASSES = {
    "ambulance": 6,  # Note: May need custom training for accurate detection
    "fire_truck": 6
}

# ==================== TRAFFIC CLEARANCE ====================
# Vehicle count threshold for considering a lane "clear"
CLEARANCE_THRESHOLD = 3

# Time (in seconds) to wait with low traffic before early signal switch
CLEARANCE_WAIT_TIME = 5

# ==================== SIGNAL SEQUENCING ====================
# Order of signal activation (clockwise)
SIGNAL_SEQUENCE = ["NORTH", "EAST", "SOUTH", "WEST"]

# ==================== GUI SETTINGS ====================
# Window dimensions
GUI_WIDTH = 1200
GUI_HEIGHT = 700

# Video display size
VIDEO_DISPLAY_WIDTH = 480
VIDEO_DISPLAY_HEIGHT = 270

# Signal light colors
SIGNAL_COLORS = {
    "RED": "#FF0000",
    "YELLOW": "#FFFF00",
    "GREEN": "#00FF00",
    "OFF": "#333333"
}

# ==================== LOGGING ====================
# Enable/disable logging
ENABLE_LOGGING = True

# Log file name
LOG_FILE = os.path.join(LOGS_DIR, "traffic_system.log")

# CSV log file for data analysis
CSV_LOG_FILE = os.path.join(LOGS_DIR, "traffic_data.csv")

# ==================== SYSTEM MODES ====================
# Automatic mode: System controls signals based on traffic
AUTO_MODE = True

# Manual override: Officer can manually control signals
MANUAL_OVERRIDE = False

# Fail-safe mode: If camera fails, use fixed timing
FAILSAFE_MODE = False
FAILSAFE_TIMER = 30  # Fixed green time in fail-safe mode

# ==================== PERFORMANCE ====================
# Frame processing rate (process every Nth frame)
FRAME_SKIP = 2  # Process every 2nd frame for better performance

# Video FPS (for timing calculations)
VIDEO_FPS = 30

# ==================== EMERGENCY VEHICLE PRIORITY ====================
# Enable emergency vehicle detection
ENABLE_EMERGENCY_DETECTION = True

# Time to give green signal when emergency vehicle detected
EMERGENCY_GREEN_TIME = 60

# ==================== STATISTICS ====================
# Enable real-time statistics tracking
ENABLE_STATISTICS = True

# Statistics update interval (seconds)
STATS_UPDATE_INTERVAL = 5

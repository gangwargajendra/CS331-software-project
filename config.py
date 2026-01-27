"""
Configuration file for Smart Traffic Signal System
"""

# Video Configuration
VIDEO_PATH = 'traffic_video.mp4'
CAMERA_ID = 0  # Use 0 for webcam, or video file path

# YOLO Model Configuration
MODEL_PATH = 'yolov8n.pt'
CONFIDENCE_THRESHOLD = 0.4

# Vehicle Class IDs (COCO dataset)
VEHICLE_CLASSES = {
    'car': 2,
    'motorcycle': 3,
    'bus': 5,
    'truck': 7
}

EMERGENCY_CLASSES = [6]  # Fire truck, ambulance

# Traffic Signal Timing (in seconds)
MIN_GREEN_TIME = 5
MAX_GREEN_TIME = 60
YELLOW_TIME = 3
RED_TIME = 2
EMERGENCY_GREEN_TIME = 30

# Traffic Density Calculation
VEHICLE_WEIGHTS = {
    'car': 1.0,
    'motorcycle': 0.5,
    'bus': 2.0,
    'truck': 2.0
}

# Display Settings
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720
FPS = 30

# Logging
LOG_FILE = 'traffic_logs.csv'
LOG_ENABLED = True

# API Settings (for frontend)
API_HOST = '127.0.0.1'
API_PORT = 5000

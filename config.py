# config.py
"""
Configuration file for Traffic Signal System
Contains all timing parameters and detection settings
"""

# Video Settings
VIDEO_PATH = 'test_videos/traffic_video.mp4'
CAMERA_ID = 0  # Use 0 for webcam, or path for video file

# Detection Settings
YOLO_MODEL = 'yolov8n.pt'  # nano model (fastest)
CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence to count vehicle
VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck

# Traffic Signal Timing (seconds)
MIN_GREEN_TIME = 5          # Minimum green light duration
MAX_GREEN_TIME = 60         # Maximum green light duration
YELLOW_TIME = 3             # Yellow light duration
RED_TIME = 2                # All-red safety time

# Dynamic Timer Calculation
TIME_PER_VEHICLE = 2        # Extra seconds per vehicle

# Emergency Settings
EMERGENCY_CLASSES = [9]     # Add emergency vehicle class if trained
EMERGENCY_GREEN_TIME = 30   # Green time for emergency vehicles

# Display Settings
WINDOW_NAME = 'Smart Traffic Signal System'
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
"""
Configuration file for traffic simulation
Contains all timing and display settings
"""

# Signal Timing (in seconds)
GREEN_LIGHT_DURATION = 10      # How long signal stays green
YELLOW_LIGHT_DURATION = 3      # How long signal stays yellow

# Traffic Generation
VEHICLE_SPAWN_RATE = 0.4       # Probability of spawning vehicle per update (0-1)
MAX_VEHICLES_PER_SIDE = 15     # Maximum vehicles waiting on each side

# Vehicle Properties
VEHICLE_SPEED = 3              # Pixels per frame

# Vehicle Type Sizes (Width x Height)
VEHICLE_SIZES = {
    'CAR': (60, 35),
    'TRUCK': (80, 45),
    'BUS': (90, 40)
}

# Vehicle Type Colors (RGB)
VEHICLE_COLORS = {
    'CAR': (52, 152, 219),      # Blue
    'TRUCK': (230, 126, 34),    # Orange
    'BUS': (46, 204, 113)       # Green
}

# License Plate Configuration
LICENSE_PLATE_STATES = ['UP', 'DL', 'MH', 'KA', 'TN', 'HR', 'RJ', 'GJ', 'MP', 'WB']
LICENSE_PLATE_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

# Vehicle Type Probabilities (must sum to 1.0)
VEHICLE_PROBABILITIES = {
    'CAR': 0.6,      # 60% cars
    'TRUCK': 0.25,   # 25% trucks
    'BUS': 0.15      # 15% buses
}

# Display Settings
FULLSCREEN = True              # Start in fullscreen mode
FPS = 60                       # Frames per second

# Colors (RGB)
COLOR_BACKGROUND = (34, 40, 49)
COLOR_ROAD = (68, 68, 68)
COLOR_ROAD_LINE = (255, 255, 255)
COLOR_ROAD_MARKING = (255, 255, 100)
COLOR_SIGNAL_RED = (231, 76, 60)
COLOR_SIGNAL_YELLOW = (241, 196, 15)
COLOR_SIGNAL_GREEN = (46, 204, 113)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DARK = (0, 0, 0)
COLOR_VEHICLE_NUMBER = (255, 255, 255)

# Intersection Layout
ROAD_WIDTH = 250               # Width of each road
SIGNAL_SIZE = 30               # Size of signal light circle

"""
Vehicle Module
Represents individual vehicles with types and IDs
"""

import config
import random

class Vehicle:
    """
    Represents a single vehicle at the intersection
    """
    
    # Class variable to track used license plates
    _used_plates = set()
    
    @staticmethod
    def generate_license_plate():
        """Generate a unique license plate number"""
        while True:
            state = random.choice(config.LICENSE_PLATE_STATES)
            district = random.randint(10, 99)
            letter = random.choice(config.LICENSE_PLATE_LETTERS)
            number = random.randint(1000, 9999)
            plate = f"{state}{district}{letter}{number}"
            
            if plate not in Vehicle._used_plates:
                Vehicle._used_plates.add(plate)
                return plate
    
    def __init__(self, side, position, vehicle_type):
        """
        Initialize a vehicle
        
        Args:
            side (str): Which side the vehicle is on ("NORTH", "SOUTH", "EAST", "WEST")
            position (int): Position in queue (0 = front of line)
            vehicle_type (str): Type of vehicle ("CAR", "TRUCK", "BUS")
        """
        self.side = side
        self.position = position
        self.vehicle_type = vehicle_type
        self.vehicle_id = Vehicle.generate_license_plate()
        
        self.x = 0
        self.y = 0
        self.speed = config.VEHICLE_SPEED
        self.crossed = False
        self.crossed_signal = False  # Has vehicle crossed the signal line?
        
        # Get size based on vehicle type
        self.width, self.height = config.VEHICLE_SIZES.get(vehicle_type, (60, 35))
        self.color = config.VEHICLE_COLORS.get(vehicle_type, (100, 100, 100))
        
        # Random direction: 0=straight, 1=left, 2=right
        self.turn_direction = random.choice([0, 0, 0, 1, 2])  # 60% straight, 20% left, 20% right
        self.is_turning = False
        self.original_side = side
        
        # Calculate initial position
        self._calculate_initial_position()
    
    def _calculate_initial_position(self, window_size=(1920, 1080)):
        """Calculate vehicle's x, y coordinates based on side and position"""
        center_x = window_size[0] // 2
        center_y = window_size[1] // 2
        spacing = 60  # Space between vehicles
        
        if self.side == "NORTH":
            self.x = center_x - 80
            self.y = center_y - 300 - (self.position * spacing)
            
        elif self.side == "SOUTH":
            self.x = center_x + 80
            self.y = center_y + 300 + (self.position * spacing)
            
        elif self.side == "EAST":
            self.x = center_x + 300 + (self.position * spacing)
            self.y = center_y + 80
            
        elif self.side == "WEST":
            self.x = center_x - 300 - (self.position * spacing)
            self.y = center_y - 80
    
    def update_position_for_screen(self, window_size):
        """Update position calculation based on actual window size"""
        self._calculate_initial_position(window_size)
    
    def move(self, window_size=(1920, 1080)):
        """Move vehicle forward in its direction"""
        if self.crossed:
            return
        
        # Check if at intersection center for turning
        center_x = window_size[0] // 2
        center_y = window_size[1] // 2
        
        # Check if vehicle should start turning
        if not self.is_turning and self._at_intersection_center(center_x, center_y):
            self.is_turning = True
            self._execute_turn()
        
        # Move in current direction
        if self.side == "NORTH":
            self.y += self.speed
        elif self.side == "SOUTH":
            self.y -= self.speed
        elif self.side == "EAST":
            self.x -= self.speed
        elif self.side == "WEST":
            self.x += self.speed
        
        # Check if vehicle has crossed intersection
        self._check_if_crossed(window_size)
        
        # Update crossed_signal status
        self._check_if_crossed_signal(window_size)
    
    def _at_intersection_center(self, center_x, center_y):
        """Check if vehicle is at intersection center"""
        threshold = 30
        
        if self.original_side == "NORTH" and abs(self.y - center_y) < threshold:
            return True
        elif self.original_side == "SOUTH" and abs(self.y - center_y) < threshold:
            return True
        elif self.original_side == "EAST" and abs(self.x - center_x) < threshold:
            return True
        elif self.original_side == "WEST" and abs(self.x - center_x) < threshold:
            return True
        return False
    
    def _execute_turn(self):
        """Execute the turn by changing side/direction"""
        if self.turn_direction == 0:
            # Go straight - no change
            pass
        elif self.turn_direction == 1:
            # Turn left
            if self.side == "NORTH":
                self.side = "WEST"
            elif self.side == "WEST":
                self.side = "SOUTH"
            elif self.side == "SOUTH":
                self.side = "EAST"
            elif self.side == "EAST":
                self.side = "NORTH"
        elif self.turn_direction == 2:
            # Turn right
            if self.side == "NORTH":
                self.side = "EAST"
            elif self.side == "EAST":
                self.side = "SOUTH"
            elif self.side == "SOUTH":
                self.side = "WEST"
            elif self.side == "WEST":
                self.side = "NORTH"
    
    def _check_if_crossed(self, window_size=(1920, 1080)):
        """Check if vehicle has completely crossed the intersection"""
        center_x = window_size[0] // 2
        center_y = window_size[1] // 2
        crossing_distance = 400
        
        if self.side == "NORTH" and self.y > center_y + crossing_distance:
            self.crossed = True
        elif self.side == "SOUTH" and self.y < center_y - crossing_distance:
            self.crossed = True
        elif self.side == "EAST" and self.x < center_x - crossing_distance:
            self.crossed = True
        elif self.side == "WEST" and self.x > center_x + crossing_distance:
            self.crossed = True
    
    def _check_if_crossed_signal(self, window_size=(1920, 1080)):
        """Check if vehicle has crossed the signal line"""
        if self.crossed_signal:
            return
        
        center_x = window_size[0] // 2
        center_y = window_size[1] // 2
        stop_distance = 150
        
        # Once vehicle crosses signal line, mark it
        if self.original_side == "NORTH" and self.y > center_y - stop_distance:
            self.crossed_signal = True
        elif self.original_side == "SOUTH" and self.y < center_y + stop_distance:
            self.crossed_signal = True
        elif self.original_side == "EAST" and self.x < center_x + stop_distance:
            self.crossed_signal = True
        elif self.original_side == "WEST" and self.x > center_x - stop_distance:
            self.crossed_signal = True
    
    def should_stop(self, signal_is_red, vehicles_ahead, window_size=(1920, 1080)):
        """
        Determine if vehicle should stop at signal or behind another vehicle
        
        Args:
            signal_is_red (bool): Is the signal red for this side?
            vehicles_ahead (list): List of vehicles ahead in same lane
            window_size (tuple): Current window size
            
        Returns:
            bool: Should vehicle stop?
        """
        # If already crossed signal line, don't stop for signal
        if self.crossed_signal:
            return False
        
        # Check if need to stop behind another vehicle
        if vehicles_ahead:
            min_distance = 50  # Minimum distance to maintain
            for other_vehicle in vehicles_ahead:
                distance = self._calculate_distance_to(other_vehicle)
                if distance < min_distance:
                    return True
        
        # Check signal only if haven't crossed signal line yet
        if not signal_is_red:
            return False
        
        # Check if vehicle is approaching the stop line
        center_x = window_size[0] // 2
        center_y = window_size[1] // 2
        stop_distance = 150
        
        if self.original_side == "NORTH" and self.y >= center_y - stop_distance - 10:
            return True
        elif self.original_side == "SOUTH" and self.y <= center_y + stop_distance + 10:
            return True
        elif self.original_side == "EAST" and self.x <= center_x + stop_distance + 10:
            return True
        elif self.original_side == "WEST" and self.x >= center_x - stop_distance - 10:
            return True
        
        return False
    
    def _calculate_distance_to(self, other_vehicle):
        """Calculate distance to another vehicle in same direction"""
        if self.original_side == "NORTH":
            return other_vehicle.y - self.y
        elif self.original_side == "SOUTH":
            return self.y - other_vehicle.y
        elif self.original_side == "EAST":
            return self.x - other_vehicle.x
        elif self.original_side == "WEST":
            return other_vehicle.x - self.x
        return 999

import random
from .vehicle import Vehicle
import config

class TrafficGenerator:
    
    def __init__(self):
        """Initialize traffic generator"""
        self.spawn_rate = config.VEHICLE_SPAWN_RATE
        self.max_vehicles = config.MAX_VEHICLES_PER_SIDE
        self.vehicle_types = list(config.VEHICLE_PROBABILITIES.keys())
        self.probabilities = list(config.VEHICLE_PROBABILITIES.values())
    
    def should_generate_vehicle(self):
        return random.random() < self.spawn_rate
    
    def choose_vehicle_type(self):
        return random.choices(self.vehicle_types, weights=self.probabilities)[0]
    
    def generate_vehicle(self, side, current_vehicle_count):
        # Don't generate if too many vehicles already
        if current_vehicle_count >= self.max_vehicles:
            return None
        
        # Random chance to generate
        if not self.should_generate_vehicle():
            return None
        
        # Choose vehicle type
        vehicle_type = self.choose_vehicle_type()
        
        # Create vehicle at back of queue
        vehicle = Vehicle(side, current_vehicle_count, vehicle_type)
        return vehicle

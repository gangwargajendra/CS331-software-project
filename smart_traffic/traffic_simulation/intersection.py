"""
Intersection Module
Manages the 4-sided intersection and all vehicles
"""

from .traffic_generator import TrafficGenerator

class Intersection:
    """
    Manages a 4-sided intersection with vehicle traffic
    """
    
    def __init__(self, signal_controller):
        """
        Initialize intersection
        
        Args:
            signal_controller (SignalController): Traffic signal controller
        """
        self.signal_controller = signal_controller
        self.traffic_generator = TrafficGenerator()
        
        # Store vehicles for each side
        self.vehicles = {
            "NORTH": [],
            "SOUTH": [],
            "EAST": [],
            "WEST": []
        }
        
        self.window_size = (1920, 1080)
        
        # Statistics
        self.total_vehicles_crossed = 0
        self.vehicles_crossed_by_type = {"CAR": 0, "TRUCK": 0, "BUS": 0}
    
    def set_window_size(self, width, height):
        """Update window size for vehicle positioning"""
        self.window_size = (width, height)
    
    def update(self):
        """Update intersection - generate vehicles and move them"""
        # Update signal controller
        self.signal_controller.update()
        
        # Generate new vehicles for each side
        for side in self.vehicles.keys():
            new_vehicle = self.traffic_generator.generate_vehicle(
                side, 
                len(self.vehicles[side])
            )
            if new_vehicle:
                new_vehicle.update_position_for_screen(self.window_size)
                self.vehicles[side].append(new_vehicle)
        
        # Move vehicles based on signal state
        for side in self.vehicles.keys():
            signal_is_red = self.signal_controller.is_red(side)
            
            for i, vehicle in enumerate(self.vehicles[side]):
                # Get vehicles ahead of this one
                vehicles_ahead = self.vehicles[side][:i]
                
                # Check if vehicle should stop at red light or behind another vehicle
                if vehicle.should_stop(signal_is_red, vehicles_ahead, self.window_size):
                    continue  # Don't move
                else:
                    vehicle.move(self.window_size)  # Move forward
        
        # Remove vehicles that have crossed and update statistics
        self._remove_crossed_vehicles()
    
    def _remove_crossed_vehicles(self):
        """Remove vehicles that have completely crossed the intersection"""
        for side in self.vehicles.keys():
            before_count = len(self.vehicles[side])
            
            # Count crossed vehicles by type before removing
            for v in self.vehicles[side]:
                if v.crossed:
                    self.total_vehicles_crossed += 1
                    self.vehicles_crossed_by_type[v.vehicle_type] += 1
            
            # Remove crossed vehicles
            self.vehicles[side] = [v for v in self.vehicles[side] if not v.crossed]
    
    def get_all_vehicles(self):
        """
        Get all vehicles from all sides
        
        Returns:
            list: List of all Vehicle objects
        """
        all_vehicles = []
        for vehicles_list in self.vehicles.values():
            all_vehicles.extend(vehicles_list)
        return all_vehicles
    
    def get_vehicle_count(self, side):
        """
        Get number of vehicles on a specific side
        
        Args:
            side (str): Side name
            
        Returns:
            int: Number of vehicles
        """
        return len(self.vehicles[side])
    
    def get_total_vehicle_count(self):
        """Get total number of vehicles currently in system"""
        return sum(len(vehicles) for vehicles in self.vehicles.values())

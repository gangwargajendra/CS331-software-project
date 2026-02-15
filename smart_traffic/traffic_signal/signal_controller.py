import time
from .signal_state import SignalState
from config import GREEN_LIGHT_DURATION, YELLOW_LIGHT_DURATION

class SignalController:
    def __init__(self):
        self.sides = ["NORTH", "SOUTH", "EAST", "WEST"]
        self.current_side_index = 0
        self.current_side = self.sides[0]
        
        # All signals start as RED
        self.signals = {
            "NORTH": SignalState.RED,
            "SOUTH": SignalState.RED,
            "EAST": SignalState.RED,
            "WEST": SignalState.RED
        }
        
        # Set first side to GREEN
        self.signals[self.current_side] = SignalState.GREEN
        
        # Timing
        self.last_change_time = time.time()
        self.green_duration = GREEN_LIGHT_DURATION
        self.yellow_duration = YELLOW_LIGHT_DURATION
        
    def update(self):
        current_time = time.time()
        elapsed = current_time - self.last_change_time
        
        current_state = self.signals[self.current_side]
        
        # GREEN -> YELLOW transition
        if current_state == SignalState.GREEN and elapsed >= self.green_duration:
            self.signals[self.current_side] = SignalState.YELLOW
            self.last_change_time = current_time
            
        # YELLOW -> RED transition, then move to next side
        elif current_state == SignalState.YELLOW and elapsed >= self.yellow_duration:
            self.signals[self.current_side] = SignalState.RED
            
            # Move to next side
            self.current_side_index = (self.current_side_index + 1) % len(self.sides)
            self.current_side = self.sides[self.current_side_index]
            
            # Set next side to GREEN
            self.signals[self.current_side] = SignalState.GREEN
            self.last_change_time = current_time
    
    def get_signal_state(self, side):
        return self.signals.get(side, SignalState.RED)
    
    def is_green(self, side):
        return self.signals.get(side) == SignalState.GREEN
    
    def is_red(self, side):
        return self.signals.get(side) == SignalState.RED
    
    def get_remaining_time(self):
        current_time = time.time()
        elapsed = current_time - self.last_change_time
        
        current_state = self.signals[self.current_side]
        if current_state == SignalState.GREEN:
            return max(0, self.green_duration - elapsed)
        elif current_state == SignalState.YELLOW:
            return max(0, self.yellow_duration - elapsed)
        return 0

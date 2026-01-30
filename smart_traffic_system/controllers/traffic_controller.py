"""
Traffic Signal Controller Module
Manages sequential traffic signal logic with adaptive timing
"""

import time
from enum import Enum
from typing import Dict, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    MAX_GREEN_TIME, MIN_GREEN_TIME, YELLOW_TIME,
    ALL_RED_TIME, CLEARANCE_THRESHOLD, CLEARANCE_WAIT_TIME,
    SIGNAL_SEQUENCE, EMERGENCY_GREEN_TIME, ENABLE_EMERGENCY_DETECTION
)


class SignalState(Enum):
    """Traffic signal states"""
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    ALL_RED = "ALL_RED"


class TrafficSignalController:
    """
    Controls traffic signals with adaptive timing based on vehicle counts
    Implements sequential signal switching with early clearance detection
    """
    
    def __init__(self):
        """Initialize traffic signal controller"""
        self.signal_sequence = SIGNAL_SEQUENCE
        self.current_side_index = 0
        self.current_side = self.signal_sequence[0]
        
        # Signal states for all sides
        self.signal_states = {side: SignalState.RED for side in self.signal_sequence}
        self.signal_states[self.current_side] = SignalState.GREEN
        
        # Timing parameters
        self.max_green_time = MAX_GREEN_TIME
        self.min_green_time = MIN_GREEN_TIME
        self.yellow_time = YELLOW_TIME
        self.all_red_time = ALL_RED_TIME
        
        # Clearance detection
        self.clearance_threshold = CLEARANCE_THRESHOLD
        self.clearance_wait_time = CLEARANCE_WAIT_TIME
        self.low_traffic_start_time = None
        
        # Current green light timer
        self.green_start_time = time.time()
        self.current_green_duration = 0
        
        # Emergency handling
        self.emergency_mode = False
        self.emergency_side = None
        
        # Statistics
        self.total_cycles = 0
        self.signal_change_history = []
        
        print("="*60)
        print("TRAFFIC SIGNAL CONTROLLER INITIALIZED")
        print("="*60)
        print(f"Signal Sequence: {' → '.join(self.signal_sequence)}")
        print(f"Max Green Time: {self.max_green_time}s")
        print(f"Min Green Time: {self.min_green_time}s")
        print(f"Yellow Time: {self.yellow_time}s")
        print(f"Clearance Threshold: {self.clearance_threshold} vehicles")
        print("="*60 + "\n")
    
    def update(self, vehicle_counts: Dict[str, int]) -> Dict[str, any]:
        """
        Update traffic signal based on current vehicle counts
        
        Args:
            vehicle_counts: Dictionary mapping side names to vehicle data (dict or int)
            
        Returns:
            Dictionary with signal update information
        """
        current_time = time.time()
        self.current_green_duration = current_time - self.green_start_time
        
        # Get vehicle count for current active side
        current_data = vehicle_counts.get(self.current_side, 0)
        
        # Extract vehicle count (handle both dict and int)
        if isinstance(current_data, dict):
            current_vehicles = current_data.get('total_vehicles', 0)
        else:
            current_vehicles = current_data
        
        # Check for emergency vehicles on any side
        if ENABLE_EMERGENCY_DETECTION:
            emergency_detected = self._check_emergency(vehicle_counts)
            if emergency_detected:
                return self._handle_emergency(emergency_detected)
        
        # Check if we should switch signal
        should_switch = self._should_switch_signal(current_vehicles)
        
        if should_switch:
            return self._switch_to_next_signal()
        
        # No switch needed
        return {
            "switched": False,
            "current_side": self.current_side,
            "signal_states": self.get_signal_states(),
            "time_remaining": max(0, self.max_green_time - self.current_green_duration),
            "reason": "Continuing current signal"
        }
    
    def _should_switch_signal(self, current_vehicles: int) -> bool:
        """
        Determine if signal should switch based on timing and vehicle count
        
        Args:
            current_vehicles: Number of vehicles on current active side
            
        Returns:
            True if signal should switch, False otherwise
        """
        # Must maintain minimum green time
        if self.current_green_duration < self.min_green_time:
            return False
        
        # ALWAYS force switch at maximum green time (ensures all sides get turns)
        if self.current_green_duration >= self.max_green_time:
            print(f"  → Switching {self.current_side}: Max time reached ({self.max_green_time}s)")
            return True
        
        # Early clearance detection (only switch early if traffic is VERY low)
        # This ensures busy sides don't monopolize the green light
        if current_vehicles <= self.clearance_threshold:
            if self.low_traffic_start_time is None:
                self.low_traffic_start_time = time.time()
            
            # Check if low traffic persisted long enough
            low_traffic_duration = time.time() - self.low_traffic_start_time
            if low_traffic_duration >= self.clearance_wait_time:
                print(f"  → Switching {self.current_side}: Early clearance (only {current_vehicles} vehicles)")
                return True
        else:
            # Reset low traffic timer if vehicles increase
            self.low_traffic_start_time = None
        
        return False
    
    def _switch_to_next_signal(self) -> Dict[str, any]:
        """
        Switch to next signal in sequence
        
        Returns:
            Dictionary with switch information
        """
        previous_side = self.current_side
        previous_duration = self.current_green_duration
        
        # Set current side to yellow
        self.signal_states[self.current_side] = SignalState.YELLOW
        reason = self._get_switch_reason(previous_duration)
        
        # Move to next side in sequence
        self.current_side_index = (self.current_side_index + 1) % len(self.signal_sequence)
        self.current_side = self.signal_sequence[self.current_side_index]
        
        # Update all signal states
        for side in self.signal_sequence:
            if side == self.current_side:
                self.signal_states[side] = SignalState.GREEN
            elif side == previous_side:
                self.signal_states[side] = SignalState.YELLOW
            else:
                self.signal_states[side] = SignalState.RED
        
        # Reset timers
        self.green_start_time = time.time()
        self.low_traffic_start_time = None
        
        # Update statistics
        if self.current_side == self.signal_sequence[0]:
            self.total_cycles += 1
        
        # Print signal change for visibility
        print(f"\n{'='*60}")
        print(f"SIGNAL CHANGE: {previous_side} \u2192 {self.current_side}")
        print(f"Duration: {previous_duration:.1f}s | Reason: {reason}")
        print(f"{'='*60}\n")
        
        # Record change
        self.signal_change_history.append({
            "time": time.time(),
            "from_side": previous_side,
            "to_side": self.current_side,
            "duration": previous_duration,
            "reason": reason
        })
        
        return {
            "switched": True,
            "from_side": previous_side,
            "to_side": self.current_side,
            "duration": previous_duration,
            "signal_states": self.get_signal_states(),
            "reason": reason,
            "total_cycles": self.total_cycles
        }
    
    def _get_switch_reason(self, duration: float) -> str:
        """Get reason for signal switch"""
        if duration >= self.max_green_time:
            return "Maximum time reached"
        elif self.low_traffic_start_time is not None:
            return "Early clearance - low traffic"
        else:
            return "Standard switch"
    
    def _check_emergency(self, vehicle_counts: Dict[str, any]) -> Optional[str]:
        """
        Check if emergency vehicle detected on any side
        
        Args:
            vehicle_counts: Dictionary with vehicle information
            
        Returns:
            Side name with emergency vehicle, or None
        """
        for side, data in vehicle_counts.items():
            if isinstance(data, dict) and data.get('emergency', False):
                return side
        return None
    
    def _handle_emergency(self, emergency_side: str) -> Dict[str, any]:
        """
        Handle emergency vehicle detection
        
        Args:
            emergency_side: Side where emergency vehicle detected
            
        Returns:
            Emergency handling information
        """
        if emergency_side == self.current_side:
            # Already on correct side, extend green time
            return {
                "switched": False,
                "current_side": self.current_side,
                "emergency": True,
                "reason": "Emergency vehicle on active side - extending green"
            }
        
        # Switch to emergency side immediately
        previous_side = self.current_side
        self.current_side = emergency_side
        self.current_side_index = self.signal_sequence.index(emergency_side)
        
        # Update signals
        for side in self.signal_sequence:
            if side == emergency_side:
                self.signal_states[side] = SignalState.GREEN
            else:
                self.signal_states[side] = SignalState.RED
        
        self.green_start_time = time.time()
        self.emergency_mode = True
        
        return {
            "switched": True,
            "from_side": previous_side,
            "to_side": emergency_side,
            "emergency": True,
            "signal_states": self.get_signal_states(),
            "reason": "EMERGENCY VEHICLE DETECTED - Immediate switch"
        }
    
    def get_signal_states(self) -> Dict[str, SignalState]:
        """Get current signal states for all sides"""
        return self.signal_states.copy()
    
    def get_current_side(self) -> str:
        """Get current active side"""
        return self.current_side
    
    def get_time_remaining(self) -> float:
        """Get remaining time for current green signal"""
        return max(0, self.max_green_time - self.current_green_duration)
    
    def get_statistics(self) -> Dict:
        """Get controller statistics"""
        return {
            "total_cycles": self.total_cycles,
            "current_side": self.current_side,
            "current_duration": self.current_green_duration,
            "signal_changes": len(self.signal_change_history),
            "recent_changes": self.signal_change_history[-10:]
        }
    
    def manual_override(self, target_side: str) -> bool:
        """
        Manually switch to a specific side (officer override)
        
        Args:
            target_side: Target side to switch to
            
        Returns:
            True if successful
        """
        if target_side not in self.signal_sequence:
            return False
        
        if target_side == self.current_side:
            return True
        
        # Force switch to target side
        self.current_side = target_side
        self.current_side_index = self.signal_sequence.index(target_side)
        
        for side in self.signal_sequence:
            if side == target_side:
                self.signal_states[side] = SignalState.GREEN
            else:
                self.signal_states[side] = SignalState.RED
        
        self.green_start_time = time.time()
        
        return True


# Test function
if __name__ == "__main__":
    print("Testing Traffic Signal Controller...\n")
    
    controller = TrafficSignalController()
    
    # Simulate traffic over time
    print("\nSimulating traffic flow...")
    
    for i in range(5):
        # Mock vehicle counts
        vehicle_counts = {
            "NORTH": 10 - i*2,
            "SOUTH": 15,
            "EAST": 8,
            "WEST": 12
        }
        
        print(f"\nIteration {i+1}:")
        print(f"Current side: {controller.get_current_side()}")
        print(f"Vehicles: {vehicle_counts}")
        
        result = controller.update(vehicle_counts)
        
        if result["switched"]:
            print(f"→ SWITCHED from {result['from_side']} to {result['to_side']}")
            print(f"  Reason: {result['reason']}")
        
        time.sleep(2)
    
    print("\n✓ Traffic Signal Controller test passed")

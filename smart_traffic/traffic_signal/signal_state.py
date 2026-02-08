"""
Signal State Enum
Defines the three possible states of a traffic signal
"""

from enum import Enum

class SignalState(Enum):
    """
    Three states of a traffic signal
    """
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    
    def __str__(self):
        return self.value

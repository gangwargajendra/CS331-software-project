from enum import Enum

class SignalState(Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    
    def __str__(self):
        return self.value

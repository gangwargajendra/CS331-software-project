"""
Traffic Simulation Module
Handles vehicles, traffic generation, and intersection management
"""

from .vehicle import Vehicle
from .traffic_generator import TrafficGenerator
from .intersection import Intersection

__all__ = ['Vehicle', 'TrafficGenerator', 'Intersection']

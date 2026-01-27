"""
Unit tests for Smart Traffic Signal System
"""
import unittest
from engine import SmartTrafficSignal
from utils import calculate_traffic_density, calculate_green_time


class TestSmartTrafficSignal(unittest.TestCase):
    """Test cases for SmartTrafficSignal class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.traffic_signal = SmartTrafficSignal()
    
    def test_initialization(self):
        """Test traffic signal initialization"""
        self.assertEqual(self.traffic_signal.min_green_time, 5)
        self.assertEqual(self.traffic_signal.max_green_time, 60)
        self.assertTrue(self.traffic_signal.camera_working)
    
    def test_detect_vehicles(self):
        """Test vehicle detection"""
        result = self.traffic_signal.detect_vehicles()
        
        if result is not None:
            self.assertIn('cars', result)
            self.assertIn('trucks', result)
            self.assertIn('bikes', result)
            self.assertIn('emergency', result)


class TestUtilityFunctions(unittest.TestCase):
    """Test cases for utility functions"""
    
    def test_calculate_traffic_density(self):
        """Test traffic density calculation"""
        vehicle_counts = {
            'cars': 10,
            'trucks': 2,
            'bikes': 5
        }
        
        density = calculate_traffic_density(vehicle_counts)
        self.assertGreater(density, 0)
    
    def test_calculate_green_time_zero_vehicles(self):
        """Test green time calculation with zero vehicles"""
        green_time = calculate_green_time(0)
        self.assertEqual(green_time, 5)  # Should return minimum time
    
    def test_calculate_green_time_normal(self):
        """Test green time calculation with normal traffic"""
        green_time = calculate_green_time(10)
        self.assertGreaterEqual(green_time, 5)
        self.assertLessEqual(green_time, 60)
    
    def test_calculate_green_time_max(self):
        """Test green time calculation doesn't exceed maximum"""
        green_time = calculate_green_time(100)
        self.assertEqual(green_time, 60)  # Should not exceed max_time


class TestEmergencyMode(unittest.TestCase):
    """Test cases for emergency vehicle detection"""
    
    def test_emergency_override(self):
        """Test that emergency vehicles get priority"""
        # This would test emergency vehicle detection logic
        pass


if __name__ == '__main__':
    unittest.main()

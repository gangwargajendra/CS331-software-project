"""
Vehicle Detector Module
Uses YOLOv8 to detect and count vehicles in video frames
"""

import cv2
from ultralytics import YOLO
import numpy as np
from typing import Dict, Tuple, List
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    MODEL_PATH, DETECTION_CONFIDENCE,
    VEHICLE_CLASSES, EMERGENCY_CLASSES
)


class VehicleDetector:
    """
    Detects and counts vehicles using YOLOv8
    """
    
    def __init__(self, model_path: str = MODEL_PATH):
        """
        Initialize the vehicle detector
        
        Args:
            model_path: Path to YOLOv8 model file
        """
        try:
            self.model = YOLO(model_path)
            print(f"✓ YOLOv8 model loaded from: {model_path}")
        except Exception as e:
            print(f"✗ Error loading YOLO model: {e}")
            raise
        
        self.vehicle_classes = VEHICLE_CLASSES
        self.emergency_classes = EMERGENCY_CLASSES
        self.confidence_threshold = DETECTION_CONFIDENCE
        
    def detect_vehicles(self, frame: np.ndarray) -> Dict[str, any]:
        """
        Detect vehicles in a single frame
        
        Args:
            frame: Input video frame (BGR format)
            
        Returns:
            Dictionary containing:
                - total_vehicles: Total count of all vehicles
                - cars: Number of cars detected
                - trucks: Number of trucks/buses detected
                - motorcycles: Number of motorcycles detected
                - emergency: Boolean indicating emergency vehicle presence
                - detections: List of detection boxes for visualization
        """
        results = {
            "total_vehicles": 0,
            "cars": 0,
            "trucks": 0,
            "motorcycles": 0,
            "emergency": False,
            "detections": []
        }
        
        if frame is None or frame.size == 0:
            return results
        
        try:
            # Run YOLO detection
            yolo_results = self.model(frame, stream=True, verbose=False)
            
            for result in yolo_results:
                boxes = result.boxes
                
                for box in boxes:
                    # Extract box information
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    coords = box.xyxy[0].cpu().numpy()  # [x1, y1, x2, y2]
                    
                    # Only process detections above confidence threshold
                    if conf < self.confidence_threshold:
                        continue
                    
                    # Count vehicles by type
                    if cls == self.vehicle_classes["car"]:
                        results["cars"] += 1
                        results["total_vehicles"] += 1
                        vehicle_type = "Car"
                        
                    elif cls in [self.vehicle_classes["truck"], 
                                self.vehicle_classes["bus"]]:
                        results["trucks"] += 1
                        results["total_vehicles"] += 1
                        vehicle_type = "Truck/Bus"
                        
                    elif cls == self.vehicle_classes["motorcycle"]:
                        results["motorcycles"] += 1
                        results["total_vehicles"] += 1
                        vehicle_type = "Motorcycle"
                        
                    elif cls in self.emergency_classes.values():
                        results["emergency"] = True
                        vehicle_type = "EMERGENCY"
                        
                    else:
                        continue
                    
                    # Store detection for visualization
                    results["detections"].append({
                        "coords": coords,
                        "type": vehicle_type,
                        "confidence": conf
                    })
                    
        except Exception as e:
            print(f"Error in vehicle detection: {e}")
        
        return results
    
    def draw_detections(self, frame: np.ndarray, 
                       detections: List[Dict]) -> np.ndarray:
        """
        Draw bounding boxes and labels on frame
        
        Args:
            frame: Input frame
            detections: List of detection dictionaries
            
        Returns:
            Frame with drawn detections
        """
        annotated_frame = frame.copy()
        
        for detection in detections:
            coords = detection["coords"]
            vehicle_type = detection["type"]
            confidence = detection["confidence"]
            
            x1, y1, x2, y2 = map(int, coords)
            
            # Color based on vehicle type
            if vehicle_type == "EMERGENCY":
                color = (0, 0, 255)  # Red for emergency
                thickness = 3
            elif vehicle_type == "Truck/Bus":
                color = (255, 165, 0)  # Orange for trucks
                thickness = 2
            elif vehicle_type == "Car":
                color = (0, 255, 0)  # Green for cars
                thickness = 2
            else:
                color = (255, 255, 0)  # Cyan for motorcycles
                thickness = 2
            
            # Draw bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), 
                         color, thickness)
            
            # Draw label
            label = f"{vehicle_type} {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 
                                           0.5, 1)
            label_y = max(y1, label_size[1] + 10)
            
            cv2.rectangle(annotated_frame, 
                         (x1, label_y - label_size[1] - 10),
                         (x1 + label_size[0], label_y),
                         color, -1)
            
            cv2.putText(annotated_frame, label, 
                       (x1, label_y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        return annotated_frame
    
    def add_stats_overlay(self, frame: np.ndarray, 
                         vehicle_counts: Dict[str, int],
                         side_name: str) -> np.ndarray:
        """
        Add vehicle count statistics overlay to frame
        
        Args:
            frame: Input frame
            vehicle_counts: Dictionary with vehicle counts
            side_name: Name of the traffic side (NORTH, SOUTH, etc.)
            
        Returns:
            Frame with statistics overlay
        """
        overlay = frame.copy()
        height, width = frame.shape[:2]
        
        # Semi-transparent background for stats
        cv2.rectangle(overlay, (10, 10), (300, 150), 
                     (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
        
        # Add text information
        y_offset = 35
        cv2.putText(frame, f"{side_name} SIDE", (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        y_offset += 30
        total = vehicle_counts.get('total_vehicles', 0)
        cv2.putText(frame, 
                   f"Total Vehicles: {total}", 
                   (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        y_offset += 25
        cars = vehicle_counts.get('cars', 0)
        cv2.putText(frame, f"Cars: {cars}", 
                   (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        y_offset += 25
        trucks = vehicle_counts.get('trucks', 0)
        cv2.putText(frame, f"Trucks/Buses: {trucks}", 
                   (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 165, 0), 1)
        
        y_offset += 25
        bikes = vehicle_counts.get('motorcycles', 0)
        cv2.putText(frame, 
                   f"Motorcycles: {bikes}", 
                   (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        # Emergency indicator
        if vehicle_counts.get('emergency', False):
            cv2.rectangle(frame, (10, height - 50), (300, height - 10),
                         (0, 0, 255), -1)
            cv2.putText(frame, "! EMERGENCY VEHICLE DETECTED !", 
                       (20, height - 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame


# Test function
if __name__ == "__main__":
    print("Testing Vehicle Detector...")
    
    try:
        detector = VehicleDetector()
        print("✓ Vehicle Detector initialized successfully")
        
        # Test with a dummy frame
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        results = detector.detect_vehicles(test_frame)
        print(f"✓ Detection test passed: {results}")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")

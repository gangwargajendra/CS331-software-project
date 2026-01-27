"""
Utility functions for traffic detection system
"""
import cv2
import csv
from datetime import datetime
import os


def calculate_traffic_density(vehicle_counts, weights=None):
    """
    Calculate traffic density based on vehicle counts and weights.
    
    Args:
        vehicle_counts (dict): Dictionary with vehicle types and counts
        weights (dict): Weight for each vehicle type
    
    Returns:
        float: Traffic density score
    """
    if weights is None:
        weights = {'cars': 1.0, 'trucks': 2.0, 'bikes': 0.5}
    
    density = 0
    for vehicle_type, count in vehicle_counts.items():
        if vehicle_type in weights:
            density += count * weights[vehicle_type]
    
    return density


def calculate_green_time(vehicle_count, min_time=5, max_time=60):
    """
    Calculate green light duration based on vehicle count.
    
    Args:
        vehicle_count (int): Number of vehicles detected
        min_time (int): Minimum green light duration
        max_time (int): Maximum green light duration
    
    Returns:
        int: Green light duration in seconds
    """
    if vehicle_count == 0:
        return min_time
    
    # Linear scaling: 1 vehicle = 2 seconds
    calculated_time = min_time + (vehicle_count * 2)
    
    return min(calculated_time, max_time)


def log_traffic_data(log_file, timestamp, vehicle_count, green_duration, emergency_mode=False):
    """
    Log traffic data to CSV file.
    
    Args:
        log_file (str): Path to log file
        timestamp (str): Current timestamp
        vehicle_count (int): Number of vehicles detected
        green_duration (int): Green light duration
        emergency_mode (bool): Whether emergency mode is active
    """
    file_exists = os.path.isfile(log_file)
    
    with open(log_file, mode='a', newline='') as f:
        writer = csv.writer(f)
        
        # Write header if file is new
        if not file_exists:
            writer.writerow(['Timestamp', 'Vehicle_Count', 'Green_Duration', 'Emergency_Mode'])
        
        writer.writerow([timestamp, vehicle_count, green_duration, emergency_mode])


def draw_bounding_boxes(frame, boxes, class_names):
    """
    Draw bounding boxes on the frame.
    
    Args:
        frame: Video frame
        boxes: Detection boxes from YOLO
        class_names: List of class names
    
    Returns:
        frame: Frame with bounding boxes drawn
    """
    for box in boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        
        # Draw rectangle
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Add label
        label = f'{class_names[cls]}: {conf:.2f}'
        cv2.putText(frame, label, (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    return frame


def add_info_overlay(frame, vehicle_counts, green_time, emergency_mode=False):
    """
    Add information overlay to video frame.
    
    Args:
        frame: Video frame
        vehicle_counts (dict): Dictionary with vehicle counts
        green_time (int): Current green light duration
        emergency_mode (bool): Whether emergency mode is active
    
    Returns:
        frame: Frame with info overlay
    """
    # Create semi-transparent overlay
    overlay = frame.copy()
    h, w = frame.shape[:2]
    
    # Draw background rectangle
    cv2.rectangle(overlay, (10, 10), (300, 180), (0, 0, 0), -1)
    frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
    
    # Add text information
    y_offset = 40
    cv2.putText(frame, "Traffic Statistics", (20, y_offset), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    y_offset += 30
    cv2.putText(frame, f"Cars: {vehicle_counts.get('cars', 0)}", (20, y_offset), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    y_offset += 25
    cv2.putText(frame, f"Trucks: {vehicle_counts.get('trucks', 0)}", (20, y_offset), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    y_offset += 25
    cv2.putText(frame, f"Bikes: {vehicle_counts.get('bikes', 0)}", (20, y_offset), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    y_offset += 30
    status = "EMERGENCY!" if emergency_mode else f"Green Time: {green_time}s"
    color = (0, 0, 255) if emergency_mode else (0, 255, 0)
    cv2.putText(frame, status, (20, y_offset), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    return frame


def get_timestamp():
    """Get current timestamp in formatted string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

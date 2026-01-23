import cv2
from ultralytics import YOLO
import config

class VehicleDetector:
    def __init__(self):
        print("Loading YOLO model.")
        self.model = YOLO(config.YOLO_MODEL)
        print("Model loaded successfully!")
        
        
    def detect_vehicles(self, frame):
        results = self.model(frame, stream=True, verbose=False)
        
        vehicle_count = 0
        detections = []

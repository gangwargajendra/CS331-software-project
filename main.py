import cv2
from ultralytics import YOLO
import time
from engine import SmartTrafficSignal

model = YOLO('yolov8n.pt')
traffic_engine = SmartTrafficSignal()

vehicle_classes = [2, 3, 5, 7]
emergency_classes = [6] 

cap = cv2.VideoCapture('traffic_video.mp4')

print("--- Smart Traffic System with YOLO Integration Started ---")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    results = model(frame, stream=True)
    
    counts = {
        "cars": 0,
        "trucks": 0,
        "bikes": 0,
        "emergency": False
    }
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            
            if conf > 0.4:
                if cls == 2:
                    counts["cars"] += 1
                elif cls in [5, 7]:
                    counts["trucks"] += 1
                elif cls == 3:
                    counts["bikes"] += 1
                elif cls in emergency_classes:
                    counts["emergency"] = True
                
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = (0, 0, 255) if cls in emergency_classes else (0, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    green_light_duration = traffic_engine.calculate_duration(counts)

    cv2.rectangle(frame, (0, 0), (350, 150), (30, 30, 30), -1)
    cv2.putText(frame, f"Detected Vehicles: {counts['cars'] + counts['trucks'] + counts['bikes']}", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    status_color = (0, 0, 255) if counts["emergency"] else (0, 255, 0)
    cv2.putText(frame, f"Suggested Green: {green_light_duration}s", 
                (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    
    if counts["emergency"]:
        cv2.putText(frame, "!!! EMERGENCY PRIORITY !!!", 
                    (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow('Smart Traffic Automation System', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
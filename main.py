import cv2
from ultralytics import YOLO

model = YOLO('yolov8n.pt')  

vehicle_classes = [2, 3, 5, 7]  

cap = cv2.VideoCapture('./test_videos/traffic2.mp4')

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    results = model(frame, stream=True)
    
    vehicle_count = 0
   
    for result in results:
        boxes = result.boxes
        for box in boxes:
            cls = int(box.cls[0])
            if cls in vehicle_classes:
                vehicle_count += 1
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                confidence = box.conf[0]
                
                label = f'Vehicle {confidence:.2f}'
                cv2.putText(frame, label, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    cv2.putText(frame, f'Vehicles: {vehicle_count}', (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
    
    cv2.imshow('Traffic Feed', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
import time
import random

class SmartTrafficSignal:
    def __init__(self):
        self.min_green_time = 5  # Seconds [cite: 64]
        self.max_green_time = 60
        self.camera_working = True
        
    def detect_vehicles(self):
        """
        Simulates the camera counting vehicles. 
        In the real project, this would use OpenCV/YOLO.
        """
        if not self.camera_working:
            return None # Simulates camera failure
            
        # [cite_start]Simulating random counts for demo purposes [cite: 61]
        cars = random.randint(0, 20)
        trucks = random.randint(0, 5)
        bikes = random.randint(0, 10)
        ambulance = random.choice([True, False, False, False, False]) # 20% chance
        
        return {
            "cars": cars, 
            "trucks": trucks, 
            "bikes": bikes, 
            "emergency": ambulance
        }

    def calculate_duration(self, counts):
        """
        [cite_start]Decides how long the green light stays on. [cite: 62]
        """
        if counts is None:
            return 30 # Failsafe Mode: Fixed timer if camera fails [cite: 71]
            
        if counts["emergency"]:
            print("!!! EMERGENCY VEHICLE DETECTED !!!")
            return 10 # Emergency Mode: Quick pass [cite: 63]
            
        # Logic: 2 seconds per car, 3 per truck, 1 per bike
        total_time = (counts["cars"] * 2) + (counts["trucks"] * 3) + (counts["bikes"] * 1)
        
        # [cite_start]Ensure time is within safe limits (min 5s, max 60s) [cite: 64]
        if total_time < self.min_green_time:
            return self.min_green_time
        elif total_time > self.max_green_time:
            return self.max_green_time
        
        return total_time

    def run_system(self):
        """
        Main loop that runs the traffic light.
        """
        print("--- Smart Traffic Signal System Started ---")
        
        # Simulating 5 cycles of traffic light changes
        for i in range(5):
            print(f"\n[Cycle {i+1}] Scanning road...")
            
            # Step 1: Get data from camera
            vehicle_data = self.detect_vehicles()
            
            # [cite_start]Step 2: Show what the camera saw [cite: 65]
            if vehicle_data:
                print(f"Detected: {vehicle_data['cars']} Cars, {vehicle_data['trucks']} Trucks, {vehicle_data['bikes']} Bikes")
            else:
                print("Error: Camera not working! Switching to Failsafe Mode.")

            # Step 3: Calculate Time
            green_light_duration = self.calculate_duration(vehicle_data)
            
            # Step 4: Change Light
            print(f">> GREEN LIGHT ON for {green_light_duration} seconds")
            time.sleep(1)
            print(">> RED LIGHT")

if __name__ == "__main__":
    system = SmartTrafficSignal()
    system.run_system()
# 🚦 Smart Traffic Signal Automation System

## CS331 - Software Engineering Lab Project

### Complete Implementation with 4-Side Sequential Control

---

## 📋 Project Overview

This system implements an **intelligent traffic signal controller** that:
- Monitors traffic from **4 directions** simultaneously (North, South, East, West)
- Uses **YOLOv8 AI model** for real-time vehicle detection
- Implements **sequential signal control** with adaptive timing
- Provides **early clearance** when traffic is low
- Detects and prioritizes **emergency vehicles**
- Features a **real-time GUI** showing all 4 sides

---

## 🎯 Key Features

### ✅ Intelligent Traffic Control
- **Sequential Signaling**: One side gets green at a time, rotating clockwise
- **Adaptive Timing**: 
  - Maximum green time: **45 seconds**
  - Minimum green time: **15 seconds** (safety)
  - Early clearance: Switches early when traffic is low
- **Yellow Light Transition**: 5 seconds yellow before red

### ✅ Vehicle Detection
- Detects **cars, trucks, buses, motorcycles**
- Real-time vehicle counting
- Emergency vehicle detection (ambulances, fire trucks)

### ✅ Visual Interface
- Live video display from all 4 sides
- Traffic signal indicators (Red, Yellow, Green)
- Vehicle count statistics
- Countdown timers
- Emergency alerts

### ✅ Data Logging
- All signal changes logged with timestamps
- Vehicle count data saved to CSV
- Emergency events tracked
- Session statistics

---

## 📁 Project Structure

```
smart_traffic_system/
├── main.py                          # Main application entry point
├── config.py                        # Configuration settings
│
├── models/                          # Core detection models
│   ├── vehicle_detector.py         # YOLOv8 vehicle detection
│   └── video_manager.py             # Multi-camera video handler
│
├── controllers/                     # Control logic
│   └── traffic_controller.py       # Sequential signal controller
│
├── views/                          # User interface
│   └── traffic_gui.py              # Tkinter GUI
│
├── utils/                          # Utilities
│   └── logger.py                   # Event and data logging
│
└── logs/                           # Log files (auto-generated)
    ├── traffic_system.log          # Text event log
    └── traffic_data.csv            # CSV data log
```

---

## 🚀 How to Run

### Prerequisites
```bash
# Ensure Python 3.8+ is installed
python --version

# Install required packages
pip install ultralytics opencv-python pillow numpy
```

### Running the System
```bash
# Navigate to the smart_traffic_system folder
cd smart_traffic_system

# Run the main application
python main.py
```

### What Happens:
1. System loads YOLOv8 model
2. Opens 4 video files (north_side.mp4, south_side.mp4, east_side.mp4, west_side.mp4)
3. Starts vehicle detection on all sides
4. Opens GUI window showing all 4 feeds
5. Begins sequential traffic signal control

---

## ⚙️ How It Works

### Sequential Signal Control Algorithm

```
1. NORTH side gets GREEN (up to 45 seconds)
   ├─ Continuously counts vehicles
   ├─ If vehicles < 3 for 5 seconds → Early switch
   └─ If 45 seconds reached → Force switch

2. NORTH goes YELLOW (5 seconds)

3. EAST side gets GREEN (up to 45 seconds)
   └─ Same logic as above

4. SOUTH side gets GREEN

5. WEST side gets GREEN

6. Back to NORTH (cycle repeats)
```

### Early Clearance Logic
- If vehicle count drops below **3 vehicles**
- And stays low for **5 seconds**
- And minimum time (15s) has passed
- → **Switch early** to next side

### Emergency Override
- If emergency vehicle detected on any side
- → **Immediate switch** to that side
- → Green for 60 seconds

---

## 🎨 GUI Interface

### Layout:
```
┌─────────────────────────────────────────────────────┐
│    🚦 SMART TRAFFIC SIGNAL AUTOMATION SYSTEM        │
├──────────────────┬──────────────────────────────────┤
│  NORTH SIDE      │      SOUTH SIDE                  │
│  [Video Feed]    │      [Video Feed]                │
│  🔴 Red          │      🟢 Green                    │
│  🟡 Yellow       │      🟡 Yellow                   │
│  🟢 Green        │      🔴 Red                      │
│  Vehicles: 15    │      Vehicles: 8                 │
│  Time: 35s       │      Time: --s                   │
├──────────────────┼──────────────────────────────────┤
│  EAST SIDE       │      WEST SIDE                   │
│  [Video Feed]    │      [Video Feed]                │
│  🔴 Red          │      🔴 Red                      │
│  Vehicles: 12    │      Vehicles: 20                │
│  Time: --s       │      Time: --s                   │
├──────────────────┴──────────────────────────────────┤
│  Status: Signal: NORTH → EAST | Early clearance     │
└──────────────────────────────────────────────────────┘
```

---

## 📊 Configuration

Edit [`config.py`](config.py) to customize:

```python
# Timing (seconds)
MAX_GREEN_TIME = 45          # Maximum green duration
MIN_GREEN_TIME = 15          # Minimum green duration
YELLOW_TIME = 5              # Yellow light duration

# Traffic Clearance
CLEARANCE_THRESHOLD = 3      # Vehicles to consider "clear"
CLEARANCE_WAIT_TIME = 5      # Wait time before early switch

# Detection
DETECTION_CONFIDENCE = 0.4   # YOLO confidence threshold

# Signal Sequence
SIGNAL_SEQUENCE = ["NORTH", "EAST", "SOUTH", "WEST"]  # Can be changed
```

---

## 📈 Logging and Analytics

### Log Files Created:

1. **`logs/traffic_system.log`** - Event log
   ```
   [2026-01-30 10:15:23] [SYSTEM] Traffic system started
   [2026-01-30 10:15:58] [SIGNAL] Signal Changed: NORTH → EAST | Duration: 35.2s | Reason: Early clearance
   [2026-01-30 10:16:15] [EMERGENCY] 🚨 EMERGENCY VEHICLE DETECTED on SOUTH side!
   ```

2. **`logs/traffic_data.csv`** - Data for analysis
   ```csv
   Timestamp,Event_Type,Side,Signal_State,Total_Vehicles,Cars,Trucks,Motorcycles,Emergency,Duration,Reason
   2026-01-30 10:15:23,VEHICLE_COUNT,NORTH,,15,10,3,2,False,,
   2026-01-30 10:15:58,SIGNAL_CHANGE,EAST,GREEN,,,,,False,35.2,Early clearance
   ```

---

## 🧪 Testing Checklist

- [x] All 4 videos load successfully
- [x] Vehicle detection works on all sides
- [x] Signals rotate sequentially (North → East → South → West)
- [x] Green light lasts 15-45 seconds
- [x] Early clearance activates with low traffic
- [x] Emergency vehicle detection works
- [x] GUI displays all information correctly
- [x] Logs are created and updated
- [x] System handles video loops properly

---

## 🛠️ Troubleshooting

### Issue: Videos not loading
**Solution:** Check that video files are in correct location:
```
CS331-software-project/
└── video/
    ├── north_side.mp4
    ├── south_side.mp4
    ├── east_side.mp4
    └── west_side.mp4
```

### Issue: YOLO model not found
**Solution:** Ensure `yolov8n.pt` is in project root:
```
CS331-software-project/
├── yolov8n.pt
└── smart_traffic_system/
```

### Issue: Import errors
**Solution:** Always run from `smart_traffic_system/` folder:
```bash
cd smart_traffic_system
python main.py
```

---

## 📚 Technologies Used

| Component | Technology |
|-----------|-----------|
| Language | Python 3.8+ |
| AI Model | YOLOv8 (Ultralytics) |
| Computer Vision | OpenCV |
| GUI | Tkinter |
| Video Processing | OpenCV + Threading |
| Data Logging | CSV + Text logs |

---

## 👥 Project Team

**CS331 - Software Engineering Lab**  
Smart Traffic Signal Automation System

---

## 📄 License

This is an academic project for CS331 Software Engineering Lab.

---

## 🎓 Assignment Requirements Met

✅ Vehicle detection and counting  
✅ Dynamic traffic light control  
✅ Emergency vehicle prioritization  
✅ Safety timers (min/max green time)  
✅ Real-time display with countdown  
✅ Offline operation  
✅ Multi-camera input support  
✅ Sequential signal switching  
✅ Adaptive timing based on traffic density  

---

## 📞 Support

For issues or questions:
1. Check logs in `logs/` folder
2. Verify video files are present
3. Ensure all dependencies installed
4. Check console output for errors

---

**🚦 End of Documentation**

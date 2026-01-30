# 🚀 QUICK START GUIDE
## Smart Traffic Signal Automation System

### ✅ Installation Complete!

All components are ready to run.

---

## 📋 How to Run

### 1. Navigate to the project folder
```bash
cd smart_traffic_system
```

### 2. Run the system
```bash
python main.py
```

### 3. What You'll See

The system will:
1. ✅ Load all 4 video files (North, South, East, West)
2. ✅ Initialize YOLOv8 vehicle detection model
3. ✅ Start traffic signal controller
4. ✅ Open GUI window showing all 4 camera feeds

---

## 🖥️ Using the System

### GUI Layout:
- **Top Left**: NORTH side video + signal + stats
- **Top Right**: SOUTH side video + signal + stats  
- **Bottom Left**: EAST side video + signal + stats
- **Bottom Right**: WEST side video + signal + stats

### Signal Indicators:
- 🔴 **RED**: Stop
- 🟡 **YELLOW**: Caution (5 seconds)
- 🟢 **GREEN**: Go (15-45 seconds)

### Information Displayed:
- Live video with vehicle detection boxes
- Total vehicle count
- Cars, Trucks, Motorcycles breakdown
- Countdown timer for active signal
- System status messages

---

## 🎮 System Behavior

### Automatic Signal Control:
1. **NORTH** gets green first (up to 45 seconds)
2. If traffic clears (< 3 vehicles for 5 seconds), switches early
3. Yellow light for 5 seconds
4. **EAST** gets green next
5. Then **SOUTH**
6. Then **WEST**
7. Cycle repeats

### Key Features:
- ⏱️ **Min Green Time**: 15 seconds (safety)
- ⏱️ **Max Green Time**: 45 seconds
- 🚗 **Early Clearance**: Switches early when traffic is low
- 🚑 **Emergency Priority**: Detects emergency vehicles (if present)

---

## 📊 Logs and Data

After running, check these files:

### 1. Event Log
**Location**: `logs/traffic_system.log`
- All system events
- Signal changes with timestamps
- Emergency detections

### 2. Data CSV
**Location**: `logs/traffic_data.csv`
- Vehicle counts over time
- Signal change history
- Useful for analysis

---

## ⚙️ Configuration

Edit `config.py` to customize:

```python
MAX_GREEN_TIME = 45          # Maximum green duration
MIN_GREEN_TIME = 15          # Minimum green duration  
CLEARANCE_THRESHOLD = 3      # Vehicles to consider "clear"
CLEARANCE_WAIT_TIME = 5      # Wait before early switch
```

---

## 🛑 How to Stop

- **Close the GUI window**, or
- **Press Ctrl+C** in terminal

The system will:
1. Stop all video captures
2. Save all logs
3. Display session statistics

---

## 📈 Expected Results

### Vehicle Detection:
- ✅ Cars: Green bounding boxes
- ✅ Trucks/Buses: Orange bounding boxes
- ✅ Motorcycles: Cyan bounding boxes
- ✅ Emergency Vehicles: Red bounding boxes (if detected)

### Signal Sequencing:
- ✅ Only ONE side has green at a time
- ✅ Signals rotate: N → E → S → W → N...
- ✅ Green time adjusts based on traffic (15-45s)
- ✅ Yellow transition (5s) between changes

---

## 🔧 Troubleshooting

### Issue: GUI doesn't open
**Solution**: Check if all videos are in correct location
```
CS331-software-project/
└── video/
    ├── north_side.mp4
    ├── south_side.mp4
    ├── east_side.mp4
    └── west_side.mp4
```

### Issue: Slow performance
**Solution**: Reduce video resolution or adjust FRAME_SKIP in config.py

### Issue: No vehicle detection
**Solution**: Check if yolov8n.pt model file exists in parent directory

---

## 📸 Screenshots of Expected Output

### Console Output:
```
======================================================================
  SMART TRAFFIC SIGNAL AUTOMATION SYSTEM
  CS331 - Software Engineering Lab Project
======================================================================

Initializing system components...

[1/5] Initializing Video Manager...
✓ NORTH: Loaded successfully (34.1 min)
✓ SOUTH: Loaded successfully (10.5 min)
✓ EAST: Loaded successfully (14.0 min)
✓ WEST: Loaded successfully (15.7 min)

[2/5] Loading Vehicle Detection Model...
✓ YOLOv8 model loaded

[3/5] Initializing Traffic Signal Controller...
✓ Signal Sequence: NORTH → EAST → SOUTH → WEST

✓ ALL COMPONENTS INITIALIZED SUCCESSFULLY
✓ System started successfully
```

### GUI Display:
- 4 video panels showing live traffic
- Traffic lights illuminated (one green, others red)
- Vehicle counts updating in real-time
- Countdown timer on active side

---

## 🎯 Project Requirements Met

✅ 4-side traffic monitoring  
✅ Sequential signal control  
✅ Adaptive timing (15-45s)  
✅ Early clearance detection  
✅ Vehicle detection (cars, trucks, bikes)  
✅ Real-time GUI display  
✅ Signal status indicators  
✅ Countdown timers  
✅ Data logging  
✅ Emergency vehicle support  

---

## 💡 Tips

1. **Let it run for 2-3 minutes** to see full signal cycle
2. **Watch the console** for signal change messages
3. **Check logs folder** for data analysis
4. **Observe vehicle counts** changing as traffic flows
5. **Notice early switches** when traffic is low

---

## 📞 Support

If you encounter issues:
1. Check that all 4 video files exist
2. Verify yolov8n.pt model is in parent directory
3. Check console output for error messages
4. Review logs in `logs/` folder

---

**🎉 Enjoy your Smart Traffic Signal System!**

**Project**: CS331 Software Engineering Lab  
**System**: Smart Traffic Signal Automation  
**Status**: ✅ FULLY OPERATIONAL

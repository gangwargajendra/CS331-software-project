# Smart Traffic Signal Simulation

## Project Structure

```
traffic_simulation_implementation/
├── main.py                          # Run this file to start simulation
├── config.py                        # Configuration settings
├── traffic_signal/
│   ├── __init__.py
│   ├── signal_state.py              # Signal states (RED, YELLOW, GREEN)
│   └── signal_controller.py         # Signal timing control
├── traffic_simulation/
│   ├── __init__.py
│   ├── vehicle.py                   # Vehicle class with types
│   ├── traffic_generator.py         # Random vehicle generation
│   └── intersection.py              # Intersection management
└── visualization/
    ├── __init__.py
    └── traffic_display.py           # Fullscreen GUI display
```

## How to Run

```bash
cd traffic_simulation_implementation
python main.py
```

## Controls

- **ESC** or **Q** - Exit simulation
- **F** - Toggle fullscreen/windowed mode

## Features

✓ Fullscreen display
✓ Different vehicle types (Car, Truck, Bus) with distinct appearances
✓ Each vehicle has unique number ID
✓ Sequential traffic signal control
✓ Vehicles stop at red signals
✓ Vehicles move when signal is green
✓ Real-time statistics display

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

## Run API Backend For React UI

```bash
cd smart_traffic
pip install -r requirements.txt
python api_server.py
```

The deployed backend is API-first and serves browser-based simulation data. It does not open a desktop pygame window on Azure.

For optional local desktop simulation UI support, install:

```bash
pip install -r requirements-desktop.txt
```

API server starts on `http://127.0.0.1:5000` and exposes:

- `GET /api/state` - live simulation state
- `POST /api/control/running` - pause/resume simulation
- `POST /api/control/reset` - reset simulation
- `POST /api/control/speed` - update simulation speed
- `POST /api/control/timings` - update green/yellow timings
- `POST /api/control/manual-override` - force one side GREEN
- `POST /api/control/emergency` - trigger emergency priority by side

## Environment Variables

Create `.env` from `.env.example` in `smart_traffic/`:

```bash
copy .env.example .env
```

Important keys:

- `API_HOST`, `API_PORT`, `API_DEBUG`
- `ALLOWED_ORIGIN` (set this to your Vercel frontend URL in production)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `SESSION_TIMEOUT_SECONDS`
- `ENABLE_DESKTOP_SIM_UI` (`false` for cloud, `true` only for local desktop UI usage)

For Azure App Service, the app also supports `PORT` automatically.

## Azure Deployment Notes

1. Deploy `smart_traffic/` as the app root.
2. Ensure startup command runs the server, for example: `python api_server.py`.
3. Set App Settings for all required env vars (especially DB and `ALLOWED_ORIGIN`).
4. If your Azure MySQL is remote, allow outbound connection and whitelist Azure IPs/firewall.
5. Keep `API_DEBUG=false` in production.
6. Keep `ENABLE_DESKTOP_SIM_UI=false` in Azure.

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

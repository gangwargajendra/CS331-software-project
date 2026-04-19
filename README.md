# Smart Traffic Signal Automation

Software Engineering lab project with a Python backend simulation and a React frontend dashboard.

Important clarification: this project does not use YOLO, live camera feeds, OpenCV video processing, or external traffic cameras. It is a software simulation with generated vehicle traffic and role-based control/monitoring.

## Current Project Structure

```text
Traffic-Signal-Automation/
├─ assignment/                    # Lab assignment files
├─ smart_traffic/                 # Backend (Python + Flask + Socket.IO)
└─ smart_traffic_signal_ui/       # Frontend (React + Vite + Tailwind)
```

## System Overview

### Backend (smart_traffic)

- Simulates a 4-side intersection: NORTH, EAST, SOUTH, WEST.
- Uses signal phases (RED, YELLOW, GREEN) with configurable timings.
- Supports emergency preemption and manual override.
- Streams live state updates over Socket.IO.
- Exposes REST APIs for auth, state, controls, and admin reports.
- Stores users and traffic violations in MySQL.

### Frontend (smart_traffic_signal_ui)

- Role-based dashboard for:
  - TRAFFIC_PERSONNEL
  - SYSTEM_ADMIN
  - VIEW_ONLY
- Login/signup with token-based session usage.
- Live traffic monitor and control panel.
- Admin screens for system health, audit trail, and violation reports.

## Main Features Implemented

- 4-side smart traffic simulation.
- Manual controls: pause/resume, reset, speed, timings.
- Emergency trigger per side.
- Role-based API authorization.
- Audit trail logging for sensitive actions.
- Violation report actions (mark taken, delete when allowed).
- Environment-variable based configuration for local/dev/prod.

## Tech Stack

- Backend: Python, Flask, Flask-SocketIO, MySQL connector, pygame simulation layer.
- Frontend: React, Vite, Tailwind CSS, socket.io-client.
- Database: MySQL.

## Local Setup

### 1) Backend setup

```bash
cd smart_traffic
pip install -r requirements.txt
copy .env.example .env
python api_server.py
```

Backend default URL: http://127.0.0.1:5000

### 2) Frontend setup

```bash
cd smart_traffic_signal_ui
npm install
copy .env.example .env
npm run dev
```

Frontend default URL: http://127.0.0.1:5173

## Environment Variables

### Backend env file

Use smart_traffic/.env (based on smart_traffic/.env.example).

Common keys:

- API_HOST
- API_PORT
- API_DEBUG
- ALLOWED_ORIGIN
- DB_HOST
- DB_PORT
- DB_NAME
- DB_USER
- DB_PASSWORD
- SESSION_TIMEOUT_SECONDS

### Frontend env file

Use smart_traffic_signal_ui/.env (based on smart_traffic_signal_ui/.env.example).

Common keys:

- VITE_API_BASE_URL
- VITE_SOCKET_BASE_URL

## Deployment Summary

### Backend on Azure App Service

- Deploy from smart_traffic folder.
- Install dependencies from requirements.txt.
- Startup command: python api_server.py
- Set App Settings for DB credentials and CORS origin.
- Set ALLOWED_ORIGIN to your Vercel frontend URL.
- Keep API_DEBUG=false in production.

### Frontend on Vercel

- Root directory: smart_traffic_signal_ui
- Build command: npm run build
- Output directory: dist
- Add Vercel env vars:
  - VITE_API_BASE_URL=https://<azure-backend>/api
  - VITE_SOCKET_BASE_URL=https://<azure-backend>

## Demo Credentials

- officer / officer123
- admin / admin123
- viewer / viewer123

Change default credentials before public production use.

## Notes

- Assignment documentation remains under assignment/.
- Folder-level readmes for backend and frontend provide deeper module-specific details.

# Smart Traffic Signal UI

Role-based React + Tailwind dashboard for Smart Traffic Signal Automation.

## Start Backend API

1. Open terminal in the `smart_traffic` folder.
2. Run:

```bash
python api_server.py
```

Backend API runs on `http://127.0.0.1:5000`.

## Start Frontend

1. Open terminal in the `smart_traffic_signal_ui` folder.
2. Run:

```bash
npm install
npm run dev
```

Frontend runs on `http://127.0.0.1:5173`.

## Environment Variables

Create `.env` from `.env.example` in `smart_traffic_signal_ui/`:

```bash
copy .env.example .env
```

Set these values:

- `VITE_API_BASE_URL` (example: `https://<your-azure-app>.azurewebsites.net/api`)
- `VITE_SOCKET_BASE_URL` (example: `https://<your-azure-app>.azurewebsites.net`)

## Vercel Deployment Notes

1. Set Root Directory to `smart_traffic_signal_ui`.
2. Framework preset: `Vite`.
3. Build command: `npm run build`.
4. Output directory: `dist`.
5. Add Vercel Environment Variables for `VITE_API_BASE_URL` and `VITE_SOCKET_BASE_URL`.

## Demo Accounts

- `officer / officer123` -> `TRAFFIC_PERSONNEL`
- `admin / admin123` -> `SYSTEM_ADMIN`
- `viewer / viewer123` -> `VIEW_ONLY`

## Implemented Security/Admin Sections

- Username/password login form.
- Role-based access control in both UI and backend endpoints.
- Menu-based admin screens:
  - System Health
  - Audit Trail
  - Violation Reports
- Direct manipulation operator screen for live intersection controls.
- Open Simulation Page button (opens browser route `#/simulation` in a new tab).

"""
REST + Socket.IO API server for Smart Traffic simulation.
Provides role-based auth, realtime state streaming, and control endpoints.
"""

from __future__ import annotations

import atexit
import functools
import logging
import threading
import time
import uuid
from typing import Any

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from werkzeug.security import check_password_hash, generate_password_hash

import config
from smart_traffic_system import SmartIntersection, SmartSignalController
from traffic_signal.signal_state import SignalState

try:
    import mysql.connector
except ImportError:  # pragma: no cover
    mysql = None
else:
    mysql = mysql.connector


SIDES = ["NORTH", "EAST", "SOUTH", "WEST"]
SIGNUP_ROLE_ALIASES = {
    "ADMIN": "SYSTEM_ADMIN",
    "SYSTEM_ADMIN": "SYSTEM_ADMIN",
    "OFFICER": "TRAFFIC_PERSONNEL",
    "TRAFFIC_PERSONNEL": "TRAFFIC_PERSONNEL",
    "VIEWER": "VIEW_ONLY",
    "VIEW_ONLY": "VIEW_ONLY",
}


class MySQLRepository:
    """Small repository for users and violation report data."""

    def __init__(self):
        self._available = mysql is not None
        self._last_error: str | None = None

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def _connect(self):
        if not self._available:
            raise RuntimeError("mysql-connector-python is not installed")

        return mysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
        )

    def initialize(self):
        if not self._available:
            self._last_error = "MySQL connector unavailable"
            return

        conn = None
        cursor = None
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS app_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(64) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(32) NOT NULL,
                    display_name VARCHAR(120) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS traffic_violations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    vehicle_id VARCHAR(32) NOT NULL,
                    vehicle_type VARCHAR(16) NOT NULL,
                    side VARCHAR(8) NOT NULL,
                    violation_type VARCHAR(32) NOT NULL,
                    in_middle TINYINT(1) NOT NULL,
                    out_middle TINYINT(1) NOT NULL,
                    action_taken TINYINT(1) NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._ensure_action_taken_column(cursor)
            conn.commit()
            self._seed_default_users(cursor)
            conn.commit()
            self._last_error = None
        except Exception as exc:  # pragma: no cover - depends on local DB setup
            self._last_error = str(exc)
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _ensure_action_taken_column(self, cursor):
        try:
            cursor.execute(
                """
                ALTER TABLE traffic_violations
                ADD COLUMN action_taken TINYINT(1) NOT NULL DEFAULT 0
                """
            )
        except Exception as exc:
            # Ignore duplicate-column errors so existing schemas stay compatible.
            if "Duplicate column name" not in str(exc):
                raise

    def _seed_default_users(self, cursor):
        defaults = [
            ("officer", "officer123", "TRAFFIC_PERSONNEL", "Traffic Officer"),
            ("admin", "admin123", "SYSTEM_ADMIN", "System Administrator"),
            ("viewer", "viewer123", "VIEW_ONLY", "Read-Only Viewer"),
        ]

        for username, password, role, display_name in defaults:
            cursor.execute(
                "SELECT id FROM app_users WHERE username = %s", (username,))
            if cursor.fetchone():
                continue

            cursor.execute(
                """
                INSERT INTO app_users (username, password_hash, role, display_name)
                VALUES (%s, %s, %s, %s)
                """,
                (username, generate_password_hash(password), role, display_name),
            )

    def get_user(self, username: str) -> dict[str, Any] | None:
        conn = None
        cursor = None
        try:
            conn = self._connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT username, password_hash, role, display_name
                FROM app_users
                WHERE username = %s
                """,
                (username,),
            )
            self._last_error = None
            return cursor.fetchone()
        except Exception as exc:
            self._last_error = str(exc)
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def create_user(self, username: str, password: str, role: str, display_name: str):
        conn = None
        cursor = None
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM app_users WHERE username = %s", (username,))
            if cursor.fetchone():
                raise ValueError("Username already exists")

            cursor.execute(
                """
                INSERT INTO app_users (username, password_hash, role, display_name)
                VALUES (%s, %s, %s, %s)
                """,
                (username, generate_password_hash(password), role, display_name),
            )
            conn.commit()
            self._last_error = None
        except ValueError:
            raise
        except Exception as exc:
            self._last_error = str(exc)
            raise RuntimeError(str(exc)) from exc
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def list_violations(self) -> list[dict[str, Any]]:
        conn = None
        cursor = None
        try:
            conn = self._connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    id,
                    vehicle_id,
                    vehicle_type,
                    side,
                    violation_type,
                    in_middle,
                    out_middle,
                    action_taken,
                    created_at
                FROM traffic_violations
                ORDER BY id DESC
                """
            )
            rows = cursor.fetchall()
            self._last_error = None
            return rows or []
        except Exception as exc:
            self._last_error = str(exc)
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def update_violation_action(self, violation_id: int, action_taken: bool) -> bool:
        conn = None
        cursor = None
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE traffic_violations
                SET action_taken = %s
                WHERE id = %s
                """,
                (1 if action_taken else 0, violation_id),
            )
            conn.commit()
            self._last_error = None
            return cursor.rowcount > 0
        except Exception as exc:
            self._last_error = str(exc)
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def delete_violation_if_action_taken(self, violation_id: int) -> tuple[bool, str]:
        conn = None
        cursor = None
        try:
            conn = self._connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT action_taken FROM traffic_violations WHERE id = %s",
                (violation_id,),
            )
            row = cursor.fetchone()
            if row is None:
                self._last_error = None
                return False, "NOT_FOUND"

            if not bool(row.get("action_taken")):
                self._last_error = None
                return False, "ACTION_NOT_TAKEN"

            cursor.execute(
                "DELETE FROM traffic_violations WHERE id = %s",
                (violation_id,),
            )
            conn.commit()
            self._last_error = None
            return True, "DELETED"
        except Exception as exc:
            self._last_error = str(exc)
            return False, "DB_ERROR"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


class SimulationService:
    """Runs simulation loop and emits realtime updates."""

    def __init__(self, socketio_server: SocketIO | None = None):
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._socketio = socketio_server
        self._next_state_emit_at = 0.0

        self.running = True
        self.speed = 1.0
        self.events: list[str] = ["Backend simulation service started."]
        self.audit_logs: list[dict[str, Any]] = []

        self.signal_controller = SmartSignalController()
        self.intersection = SmartIntersection(self.signal_controller)
        self.intersection.set_window_size(1920, 1080)

        self._accumulator = 0.0
        self._manual_emergency: dict[str, Any] | None = None
        self._sessions: dict[str, dict[str, Any]] = {}
        self._display_stop_event = threading.Event()
        self._display_thread: threading.Thread | None = None

        self.repository = MySQLRepository()
        self.repository.initialize()

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

        self.add_audit_log(
            actor="system",
            role="SYSTEM",
            action="SERVICE_START",
            details="Simulation service initialized.",
        )

    def shutdown(self):
        self._stop_event.set()
        self._thread.join(timeout=2)

        self._display_stop_event.set()
        if self._display_thread and self._display_thread.is_alive():
            self._display_thread.join(timeout=2)

    def _log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        self.events = [f"[{timestamp}] {message}", *self.events][:10]

    def add_audit_log(self, actor: str, role: str, action: str, details: str):
        entry = {
            "timestamp": time.time(),
            "actor": actor,
            "role": role,
            "action": action,
            "details": details,
        }
        self.audit_logs = [entry, *self.audit_logs][:200]

    def _loop(self):
        target_fps = 60.0
        interval = 1.0 / target_fps
        last_t = time.time()

        while not self._stop_event.is_set():
            now = time.time()
            dt = now - last_t
            last_t = now
            state_payload = None

            with self._lock:
                self._update_manual_emergency(now)

                if self.running:
                    self._accumulator += dt * target_fps * self.speed
                    steps = int(self._accumulator)
                    self._accumulator -= steps
                    steps = min(steps, 10)

                    for _ in range(steps):
                        self.intersection.update()

                if now >= self._next_state_emit_at:
                    state_payload = self._get_state_locked(now)
                    self._next_state_emit_at = now + 0.10

            if state_payload is not None:
                self._broadcast_state(state_payload)

            time.sleep(interval)

    def _broadcast_state(self, state_payload: dict[str, Any]):
        if not self._socketio:
            return
        self._socketio.emit("state_update", {"state": state_payload})

    def emit_state_now(self):
        with self._lock:
            payload = self._get_state_locked(time.time())
        self._broadcast_state(payload)

    def _update_manual_emergency(self, now: float):
        if not self._manual_emergency:
            return

        if now < self._manual_emergency["ends_at"]:
            return

        sc = self.signal_controller
        if sc.emergency_mode:
            sc.end_emergency(
                resume_side_index=self._manual_emergency["resume_side_index"],
                resume_side=self._manual_emergency["resume_side"],
                resume_green_remaining=self._manual_emergency["resume_green_remaining"],
            )

        self._manual_emergency = None
        self._log("Manual emergency finished.")

    def _remaining_green(self) -> float:
        sc = self.signal_controller
        current_state = sc.signals.get(sc.current_side)
        if current_state != SignalState.GREEN:
            return 0.0
        elapsed = time.time() - sc.last_change_time
        return max(0.0, sc.green_duration - elapsed)

    def reset(self):
        with self._lock:
            green = self.signal_controller.green_duration
            yellow = self.signal_controller.yellow_duration

            self.signal_controller = SmartSignalController()
            self.signal_controller.set_durations(green, yellow)
            self.intersection = SmartIntersection(self.signal_controller)
            self.intersection.set_window_size(1920, 1080)
            self._manual_emergency = None
            self._accumulator = 0.0
            self._log("Simulation reset requested.")

    def set_running(self, running: bool):
        with self._lock:
            self.running = bool(running)
            self._log(
                "Simulation resumed." if self.running else "Simulation paused.")

    def set_speed(self, speed: float):
        with self._lock:
            self.speed = max(0.2, min(3.0, float(speed)))
            self._log(f"Speed changed to {self.speed:.1f}x.")

    def set_timings(self, green_duration: float, yellow_duration: float):
        with self._lock:
            self.signal_controller.set_durations(
                green_duration, yellow_duration)
            self._log(
                "Signal timings updated: "
                f"green={self.signal_controller.green_duration:.0f}s, "
                f"yellow={self.signal_controller.yellow_duration:.0f}s."
            )

    def manual_override(self, side: str):
        side = side.upper()
        if side not in SIDES:
            raise ValueError(f"Invalid side: {side}")

        with self._lock:
            self.signal_controller.set_manual_green(side)
            self._manual_emergency = None
            self._log(f"Manual green override applied to {side}.")

    def trigger_manual_emergency(self, side: str, duration: float = 12.0):
        side = side.upper()
        if side not in SIDES:
            raise ValueError(f"Invalid side: {side}")

        with self._lock:
            sc = self.signal_controller
            self._manual_emergency = {
                "side": side,
                "ends_at": time.time() + max(3.0, float(duration)),
                "resume_side_index": sc.current_side_index,
                "resume_side": sc.current_side,
                "resume_green_remaining": self._remaining_green(),
            }

            sc.start_emergency(side)
            self._log(f"Manual emergency triggered for {side}.")

    def _display_loop(self):
        display = None
        try:
            from visualization import TrafficDisplay
            display = TrafficDisplay()
            self._log("Shared simulation UI window opened.")

            while not self._display_stop_event.is_set():
                if display.check_events():
                    break

                with self._lock:
                    display.draw(self.intersection)
        except Exception as exc:  # pragma: no cover - display is environment-specific
            self._log(f"Desktop UI could not start: {exc}")
        finally:
            if display is not None:
                display.cleanup()
            self._log("Shared simulation UI window closed.")

    def launch_backend_ui(self) -> dict[str, Any]:
        if not config.ENABLE_DESKTOP_SIM_UI:
            return {
                "ok": False,
                "alreadyRunning": False,
                "message": "Desktop simulation UI is disabled in this environment.",
            }

        if self._display_thread and self._display_thread.is_alive():
            return {
                "ok": True,
                "alreadyRunning": True,
                "message": "Simulation UI is already running.",
            }

        self._display_stop_event.clear()
        self._display_thread = threading.Thread(
            target=self._display_loop, daemon=True)
        self._display_thread.start()
        return {
            "ok": True,
            "alreadyRunning": False,
            "message": "Simulation UI launched (live-synced with API).",
        }

    def _get_state_locked(self, now: float) -> dict[str, Any]:
        sc = self.signal_controller
        inter = self.intersection
        handler = inter.emergency_handler

        signals = {side: sc.get_signal_state(side).name for side in SIDES}
        vehicle_counts = {
            side: inter.get_vehicle_count(side) for side in SIDES}

        manual_emergency_active = self._manual_emergency is not None
        manual_remaining = (
            max(0.0, self._manual_emergency["ends_at"] - now)
            if manual_emergency_active
            else 0.0
        )

        emergency_active = handler.active or manual_emergency_active
        emergency_side = (
            handler.emergency_side
            if handler.active
            else (self._manual_emergency["side"] if manual_emergency_active else None)
        )

        return {
            "running": self.running,
            "speed": self.speed,
            "greenDuration": sc.green_duration,
            "yellowDuration": sc.yellow_duration,
            "currentSide": sc.current_side,
            "currentSideIndex": sc.current_side_index,
            "phase": sc.get_signal_state(sc.current_side).name,
            "remainingTime": sc.get_remaining_time(),
            "signals": signals,
            "vehicleCounts": vehicle_counts,
            "totalVehicles": inter.get_total_vehicle_count(),
            "totalCrossed": inter.total_vehicles_crossed,
            "crossedByType": dict(inter.vehicles_crossed_by_type),
            "emergency": {
                "active": emergency_active,
                "side": emergency_side,
                "queue": len(getattr(handler, "_queue", [])),
                "remaining": manual_remaining,
            },
            "events": list(self.events),
            "timestamp": now,
            "backendUiEnabled": bool(config.ENABLE_DESKTOP_SIM_UI),
            "backendUiRunning": self._display_thread is not None and self._display_thread.is_alive(),
            "vehicles": self._get_vehicles_locked(),
        }

    def _get_vehicles_locked(self) -> list[dict[str, Any]]:
        """Serialize all vehicle positions for the frontend."""
        inter = self.intersection
        result = []
        for side in SIDES:
            for v in inter.vehicles.get(side, []):
                result.append({
                    "id": v.vehicle_id,
                    "type": v.vehicle_type,
                    "side": v.original_side,
                    "x": round(v.x, 1),
                    "y": round(v.y, 1),
                    "angle": round(v.angle, 1),
                    "stopped": v.stopped,
                    "crossed": v.crossed,
                })
        return result

    def get_state(self) -> dict[str, Any]:
        with self._lock:
            return self._get_state_locked(time.time())

    def _build_session(self, user: dict[str, Any]) -> dict[str, Any]:
        token = uuid.uuid4().hex
        now = time.time()
        session = {
            "token": token,
            "username": user["username"],
            "displayName": user["display_name"],
            "role": user["role"],
            "createdAt": now,
            "lastSeen": now,
        }
        self._sessions[token] = session
        return session

    def login(self, username: str, password: str) -> dict[str, Any] | None:
        user = self.repository.get_user(username)
        if not user:
            return None

        if not check_password_hash(user["password_hash"], password):
            return None

        return self._build_session(user)

    def signup(self, username: str, password: str, display_name: str, role_input: str) -> dict[str, Any]:
        role_key = SIGNUP_ROLE_ALIASES.get(role_input.strip().upper())
        if not role_key:
            raise ValueError("Role must be admin, officer, or viewer")

        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters")

        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")

        safe_display_name = display_name.strip() or username
        self.repository.create_user(
            username, password, role_key, safe_display_name)

        created_user = self.repository.get_user(username)
        if not created_user:
            raise RuntimeError("User created but could not be read back")

        return self._build_session(created_user)

    def get_session(self, token: str | None) -> dict[str, Any] | None:
        if not token:
            return None

        session = self._sessions.get(token)
        if not session:
            return None

        now = time.time()
        if now - session["lastSeen"] > config.SESSION_TIMEOUT_SECONDS:
            self._sessions.pop(token, None)
            return None

        session["lastSeen"] = now
        return session

    def logout(self, token: str):
        self._sessions.pop(token, None)

    def get_audit_logs(self) -> list[dict[str, Any]]:
        return list(self.audit_logs)

    def get_system_health(self) -> dict[str, Any]:
        sc = self.signal_controller
        db_status = "OK" if self.repository.last_error is None else self.repository.last_error
        return {
            "simulationRunning": self.running,
            "speed": self.speed,
            "activeSessions": len(self._sessions),
            "emergencyMode": sc.emergency_mode,
            "signalControllerCurrentSide": sc.current_side,
            "serviceStatus": "OK",
            "dbStatus": db_status,
        }

    def get_violation_report(self) -> dict[str, Any]:
        rows = self.repository.list_violations()
        mapped_rows = [
            {
                "id": row["id"],
                "vehicleId": row["vehicle_id"],
                "vehicleType": row["vehicle_type"],
                "side": row["side"],
                "violationType": row["violation_type"],
                "inMiddle": bool(row["in_middle"]),
                "outMiddle": bool(row["out_middle"]),
                "actionTaken": bool(row.get("action_taken")),
                "createdAt": row["created_at"].isoformat() if row.get("created_at") else None,
            }
            for row in rows
        ]

        return {
            "status": "OK" if self.repository.last_error is None else "DB_ERROR",
            "message": "Fetched violation data from MySQL." if self.repository.last_error is None else self.repository.last_error,
            "total": len(mapped_rows),
            "rows": mapped_rows,
        }

    def update_violation_action(self, violation_id: int, action_taken: bool) -> bool:
        return self.repository.update_violation_action(violation_id, action_taken)

    def delete_violation(self, violation_id: int) -> tuple[bool, str]:
        return self.repository.delete_violation_if_action_taken(violation_id)


app = Flask(__name__)
socketio = SocketIO(
    app,
    cors_allowed_origins=config.ALLOWED_ORIGIN,
    async_mode="threading",
    logger=not config.QUIET_HTTP_LOGS,
    engineio_logger=not config.QUIET_HTTP_LOGS,
)
service = SimulationService(socketio)


if config.QUIET_HTTP_LOGS:
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    logging.getLogger("engineio").setLevel(logging.ERROR)
    logging.getLogger("socketio").setLevel(logging.ERROR)


def _extract_token() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return None


def require_auth(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if request.method == "OPTIONS":
            return ("", 204)

        token = _extract_token()
        session = service.get_session(token)
        if not session:
            return jsonify({"ok": False, "error": "Unauthorized"}), 401

        request.user_session = session
        return view(*args, **kwargs)

    return wrapper


def require_roles(*allowed_roles):
    def decorator(view):
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            session = getattr(request, "user_session", None)
            if not session:
                return jsonify({"ok": False, "error": "Unauthorized"}), 401

            if session["role"] not in allowed_roles:
                return jsonify({"ok": False, "error": "Forbidden"}), 403

            return view(*args, **kwargs)

        return wrapper

    return decorator


def _audit(action: str, details: str):
    session = getattr(request, "user_session", None)
    if session:
        service.add_audit_log(
            actor=session["username"],
            role=session["role"],
            action=action,
            details=details,
        )


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = config.ALLOWED_ORIGIN
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


@socketio.on("connect")
def socket_connect(auth):
    token = None
    if isinstance(auth, dict):
        token = auth.get("token")

    session = service.get_session(token)
    if not session:
        return False

    emit("state_update", {"state": service.get_state()})


@app.route("/", methods=["GET"])
def backend_ui():
    return """
    <!doctype html>
    <html>
      <head>
        <meta charset='utf-8' />
        <meta name='viewport' content='width=device-width, initial-scale=1' />
        <title>Smart Traffic Backend UI</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 24px; background: #0f172a; color: #e2e8f0; }
          h1 { margin-top: 0; }
          a { color: #22d3ee; }
          pre { background: #111827; padding: 12px; border-radius: 8px; overflow: auto; }
          .card { background: #1f2937; padding: 16px; border-radius: 10px; margin-bottom: 12px; }
        </style>
      </head>
      <body>
        <h1>Smart Traffic Backend UI</h1>
        <div class='card'>
          <p>This backend is running. Use the React app for operator/admin workflows.</p>
          <p>Quick links:</p>
          <ul>
            <li><a href='/api/health' target='_blank'>/api/health</a></li>
            <li><a href='/api/state' target='_blank'>/api/state</a></li>
          </ul>
        </div>
        <div class='card'>
          <p>Demo credentials (seeded in MySQL app_users table):</p>
          <pre>officer / officer123
admin / admin123
viewer / viewer123</pre>
        </div>
      </body>
    </html>
    """


@app.route("/api/auth/login", methods=["POST", "OPTIONS"])
def auth_login():
    if request.method == "OPTIONS":
        return ("", 204)

    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))

    session = service.login(username, password)
    if not session:
        return jsonify({"ok": False, "error": "Invalid username or password"}), 401

    service.add_audit_log(
        actor=session["username"],
        role=session["role"],
        action="LOGIN",
        details="User logged in successfully.",
    )

    return jsonify(
        {
            "ok": True,
            "token": session["token"],
            "user": {
                "username": session["username"],
                "displayName": session["displayName"],
                "role": session["role"],
            },
        }
    )


@app.route("/api/auth/signup", methods=["POST", "OPTIONS"])
def auth_signup():
    if request.method == "OPTIONS":
        return ("", 204)

    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    role = str(payload.get("role", "viewer"))
    display_name = str(payload.get("displayName", "")).strip()

    if not username or not password:
        return jsonify({"ok": False, "error": "Username and password are required"}), 400

    try:
        session = service.signup(username, password, display_name, role)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"ok": False, "error": f"Database error: {exc}"}), 500

    service.add_audit_log(
        actor=session["username"],
        role=session["role"],
        action="SIGNUP",
        details="User registered from signup form.",
    )

    return jsonify(
        {
            "ok": True,
            "token": session["token"],
            "user": {
                "username": session["username"],
                "displayName": session["displayName"],
                "role": session["role"],
            },
        }
    )


@app.route("/api/auth/me", methods=["GET"])
@require_auth
def auth_me():
    session = request.user_session
    return jsonify(
        {
            "ok": True,
            "user": {
                "username": session["username"],
                "displayName": session["displayName"],
                "role": session["role"],
            },
        }
    )


@app.route("/api/auth/logout", methods=["POST", "OPTIONS"])
@require_auth
def auth_logout():
    if request.method == "OPTIONS":
        return ("", 204)

    session = request.user_session
    token = _extract_token()
    service.add_audit_log(
        actor=session["username"],
        role=session["role"],
        action="LOGOUT",
        details="User logged out.",
    )
    if token:
        service.logout(token)

    return jsonify({"ok": True})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/state", methods=["GET"])
@require_auth
def get_state():
    return jsonify({"state": service.get_state()})


@app.route("/api/audit-trail", methods=["GET"])
@require_auth
@require_roles("SYSTEM_ADMIN")
def audit_trail():
    return jsonify({"ok": True, "logs": service.get_audit_logs()})


@app.route("/api/system-health", methods=["GET"])
@require_auth
@require_roles("SYSTEM_ADMIN")
def system_health():
    return jsonify({"ok": True, "health": service.get_system_health()})


@app.route("/api/violations-report", methods=["GET"])
@require_auth
@require_roles("SYSTEM_ADMIN")
def violations_report():
    return jsonify({"ok": True, "report": service.get_violation_report()})


@app.route("/api/violations/<int:violation_id>/action", methods=["POST", "OPTIONS"])
@require_auth
@require_roles("SYSTEM_ADMIN")
def update_violation_action(violation_id: int):
    if request.method == "OPTIONS":
        return ("", 204)

    payload = request.get_json(silent=True) or {}
    raw_value = payload.get("actionTaken")
    if isinstance(raw_value, bool):
        action_taken = raw_value
    elif isinstance(raw_value, (int, float)):
        action_taken = bool(raw_value)
    elif isinstance(raw_value, str):
        action_taken = raw_value.strip().lower() in {
            "1", "true", "yes", "taken"}
    else:
        return jsonify({"ok": False, "error": "actionTaken is required"}), 400

    if not service.update_violation_action(violation_id, action_taken):
        return jsonify({"ok": False, "error": "Violation not found or update failed"}), 404

    _audit(
        "VIOLATION_ACTION_UPDATED",
        f"Violation {violation_id} actionTaken set to {action_taken}.",
    )
    return jsonify({"ok": True, "report": service.get_violation_report()})


@app.route("/api/violations/<int:violation_id>/delete", methods=["POST", "OPTIONS"])
@require_auth
@require_roles("SYSTEM_ADMIN")
def delete_violation(violation_id: int):
    if request.method == "OPTIONS":
        return ("", 204)

    deleted, reason = service.delete_violation(violation_id)
    if not deleted:
        if reason == "NOT_FOUND":
            return jsonify({"ok": False, "error": "Violation not found"}), 404
        if reason == "ACTION_NOT_TAKEN":
            return jsonify({"ok": False, "error": "Action must be Taken before deletion"}), 400
        return jsonify({"ok": False, "error": "Failed to delete violation"}), 500

    _audit("VIOLATION_DELETED", f"Violation {violation_id} deleted.")
    return jsonify({"ok": True, "report": service.get_violation_report()})


@app.route("/api/system/open-backend-ui", methods=["POST", "OPTIONS"])
@require_auth
def open_backend_ui():
    if request.method == "OPTIONS":
        return ("", 204)

    result = service.launch_backend_ui()
    _audit("OPEN_BACKEND_UI", result["message"])
    return jsonify(result)


@app.route("/api/control/reset", methods=["POST", "OPTIONS"])
@require_auth
@require_roles("TRAFFIC_PERSONNEL", "SYSTEM_ADMIN")
def control_reset():
    service.reset()
    service.emit_state_now()
    _audit("CONTROL_RESET", "Simulation reset requested.")
    return jsonify({"ok": True, "state": service.get_state()})


@app.route("/api/control/running", methods=["POST", "OPTIONS"])
@require_auth
@require_roles("TRAFFIC_PERSONNEL", "SYSTEM_ADMIN")
def control_running():
    payload = request.get_json(silent=True) or {}
    if "running" not in payload:
        return jsonify({"ok": False, "error": "'running' is required"}), 400

    service.set_running(bool(payload["running"]))
    service.emit_state_now()
    _audit("CONTROL_RUNNING", f"Set running={bool(payload['running'])}.")
    return jsonify({"ok": True, "state": service.get_state()})


@app.route("/api/control/speed", methods=["POST", "OPTIONS"])
@require_auth
@require_roles("TRAFFIC_PERSONNEL", "SYSTEM_ADMIN")
def control_speed():
    payload = request.get_json(silent=True) or {}
    if "speed" not in payload:
        return jsonify({"ok": False, "error": "'speed' is required"}), 400

    try:
        service.set_speed(float(payload["speed"]))
    except ValueError:
        return jsonify({"ok": False, "error": "speed must be numeric"}), 400

    _audit("CONTROL_SPEED", f"Set speed={float(payload['speed'])}.")
    service.emit_state_now()
    return jsonify({"ok": True, "state": service.get_state()})


@app.route("/api/control/timings", methods=["POST", "OPTIONS"])
@require_auth
@require_roles("TRAFFIC_PERSONNEL", "SYSTEM_ADMIN")
def control_timings():
    payload = request.get_json(silent=True) or {}
    if "greenDuration" not in payload or "yellowDuration" not in payload:
        return (
            jsonify(
                {"ok": False, "error": "greenDuration and yellowDuration are required"}),
            400,
        )

    try:
        service.set_timings(float(payload["greenDuration"]), float(
            payload["yellowDuration"]))
    except ValueError:
        return jsonify({"ok": False, "error": "timings must be numeric"}), 400

    _audit(
        "CONTROL_TIMINGS",
        f"Set green={float(payload['greenDuration'])}, yellow={float(payload['yellowDuration'])}.",
    )
    service.emit_state_now()
    return jsonify({"ok": True, "state": service.get_state()})


@app.route("/api/control/manual-override", methods=["POST", "OPTIONS"])
@require_auth
@require_roles("TRAFFIC_PERSONNEL", "SYSTEM_ADMIN")
def control_manual_override():
    payload = request.get_json(silent=True) or {}
    side = str(payload.get("side", "")).upper()
    if side not in SIDES:
        return jsonify({"ok": False, "error": "side must be one of NORTH/EAST/SOUTH/WEST"}), 400

    service.manual_override(side)
    service.emit_state_now()
    _audit("CONTROL_MANUAL_OVERRIDE", f"Manual override to {side}.")
    return jsonify({"ok": True, "state": service.get_state()})


@app.route("/api/control/emergency", methods=["POST", "OPTIONS"])
@require_auth
@require_roles("TRAFFIC_PERSONNEL", "SYSTEM_ADMIN")
def control_emergency():
    payload = request.get_json(silent=True) or {}
    side = str(payload.get("side", "")).upper()
    duration = float(payload.get("duration", 12))

    if side not in SIDES:
        return jsonify({"ok": False, "error": "side must be one of NORTH/EAST/SOUTH/WEST"}), 400

    service.trigger_manual_emergency(side, duration)
    service.emit_state_now()
    _audit("CONTROL_EMERGENCY",
           f"Emergency triggered on {side} for {duration}s.")
    return jsonify({"ok": True, "state": service.get_state()})


def main():
    socketio.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        debug=config.API_DEBUG,
    )


atexit.register(service.shutdown)

if __name__ == "__main__":
    main()

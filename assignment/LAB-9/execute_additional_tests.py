"""
LAB-9 additional module testing after pull.
Covers API auth/control, emergency handling, vehicle logic,
traffic generation, intersection queue counting, and DB-failure resilience.
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable


@dataclass
class CaseResult:
    test_case_id: str
    module: str
    description: str
    input_data: str
    expected_output: str
    actual_output: str
    status: str  # Pass / Fail / Blocked


def _prepare_imports():
    here = os.path.abspath(os.path.dirname(__file__))
    repo_root = os.path.abspath(os.path.join(here, "..", ".."))
    smart_traffic_root = os.path.join(repo_root, "smart_traffic")
    if smart_traffic_root not in sys.path:
        sys.path.insert(0, smart_traffic_root)


def _run_case(
    results: list[CaseResult],
    test_case_id: str,
    module: str,
    description: str,
    input_data: str,
    expected_output: str,
    fn: Callable[[], tuple[bool, str]],
):
    try:
        ok, actual = fn()
        results.append(
            CaseResult(
                test_case_id,
                module,
                description,
                input_data,
                expected_output,
                actual,
                "Pass" if ok else "Fail",
            )
        )
    except Exception as exc:
        results.append(
            CaseResult(
                test_case_id,
                module,
                description,
                input_data,
                expected_output,
                f"Exception: {type(exc).__name__}: {exc}",
                "Fail",
            )
        )


class DummyAmbulance:
    def __init__(self, vehicle_id: str, side: str, distance: float):
        self.vehicle_id = vehicle_id
        self.vehicle_type = "AMBULANCE"
        self.original_side = side
        self._distance = distance
        self.crossed = False

    def get_distance_from_stop_line(self, _cx: int, _cy: int):
        return self._distance

    def has_passed_stop_line(self, _cx: int, _cy: int):
        return self._distance < 0


class DummyQueueVehicle:
    def __init__(self, passed: bool, crossed: bool):
        self._passed = passed
        self.crossed = crossed

    def has_passed_stop_line(self, _cx: int, _cy: int):
        return self._passed


class DummyViolationVehicle:
    vehicle_id = "TEST1234"
    vehicle_type = "CAR"
    original_side = "NORTH"
    in_middle = True
    out_middle = False


def run_additional_cases() -> list[CaseResult]:
    _prepare_imports()

    from smart_traffic_system.smart_signal_controller import SmartSignalController  # type: ignore[import-not-found]
    from emergency.emergency_handler import EmergencyHandler  # type: ignore[import-not-found]
    from traffic_simulation.vehicle import Vehicle  # type: ignore[import-not-found]
    from traffic_simulation.traffic_generator import TrafficGenerator  # type: ignore[import-not-found]
    from smart_traffic_system.smart_intersection import SmartIntersection  # type: ignore[import-not-found]
    import config  # type: ignore[import-not-found]

    results: list[CaseResult] = []

    # ---------------- API TESTS ----------------
    api_available = True
    try:
        import api_server  # type: ignore[import-not-found]
    except Exception as exc:
        api_available = False
        blocked_reason = f"Blocked: api_server import failed: {type(exc).__name__}: {exc}"
        for tcid, desc in [
            ("TC-API-01", "Unauthorized state endpoint"),
            ("TC-API-02", "Viewer forbidden for system-health"),
            ("TC-API-03", "Officer speed control valid request"),
            ("TC-API-04", "Invalid emergency side rejected"),
            ("TC-API-05", "String false handling for running flag"),
            ("TC-API-06", "Invalid duration type for emergency"),
        ]:
            results.append(
                CaseResult(
                    tcid,
                    "api_server",
                    desc,
                    "N/A",
                    "N/A",
                    blocked_reason,
                    "Blocked",
                )
            )

    if api_available:
        app = api_server.app
        service = api_server.service

        original_attrs = {
            "get_session": service.get_session,
            "set_running": service.set_running,
            "set_speed": service.set_speed,
            "trigger_manual_emergency": service.trigger_manual_emergency,
            "emit_state_now": service.emit_state_now,
            "get_state": service.get_state,
            "add_audit_log": service.add_audit_log,
        }

        state_snapshot: dict[str, Any] = {
            "running": True,
            "speed": 1.0,
            "currentSide": "NORTH",
            "signals": {"NORTH": "GREEN", "EAST": "RED", "SOUTH": "RED", "WEST": "RED"},
        }
        recorder: dict[str, Any] = {"running_arg": None, "speed_arg": None, "emergency": None}

        def fake_get_session(token: str | None):
            sessions = {
                "viewer-token": {
                    "username": "viewer",
                    "displayName": "Viewer",
                    "role": "VIEW_ONLY",
                    "lastSeen": time.time(),
                },
                "officer-token": {
                    "username": "officer",
                    "displayName": "Officer",
                    "role": "TRAFFIC_PERSONNEL",
                    "lastSeen": time.time(),
                },
                "admin-token": {
                    "username": "admin",
                    "displayName": "Admin",
                    "role": "SYSTEM_ADMIN",
                    "lastSeen": time.time(),
                },
            }
            return sessions.get(token)

        def fake_set_running(value: bool):
            recorder["running_arg"] = value
            state_snapshot["running"] = bool(value)

        def fake_set_speed(value: float):
            recorder["speed_arg"] = value
            state_snapshot["speed"] = float(value)

        def fake_trigger_manual_emergency(side: str, duration: float = 12.0):
            recorder["emergency"] = (side, duration)

        def fake_emit_state_now():
            return None

        def fake_get_state():
            return dict(state_snapshot)

        def fake_add_audit_log(**_kwargs):
            return None

        service.get_session = fake_get_session
        service.set_running = fake_set_running
        service.set_speed = fake_set_speed
        service.trigger_manual_emergency = fake_trigger_manual_emergency
        service.emit_state_now = fake_emit_state_now
        service.get_state = fake_get_state
        service.add_audit_log = fake_add_audit_log

        client = app.test_client()

        def _auth(token: str):
            return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            _run_case(
                results,
                "TC-API-01",
                "api_server",
                "GET /api/state returns 401 without bearer token",
                "No Authorization header",
                "HTTP 401 Unauthorized",
                lambda: (
                    (lambda r: (r.status_code == 401, f"status={r.status_code}"))(client.get("/api/state"))
                ),
            )

            _run_case(
                results,
                "TC-API-02",
                "api_server",
                "VIEW_ONLY role cannot access admin system-health endpoint",
                "GET /api/system-health with viewer token",
                "HTTP 403 Forbidden",
                lambda: (
                    (lambda r: (r.status_code == 403, f"status={r.status_code}"))(
                        client.get("/api/system-health", headers=_auth("viewer-token"))
                    )
                ),
            )

            _run_case(
                results,
                "TC-API-03",
                "api_server",
                "Officer can change speed with numeric value",
                "POST /api/control/speed speed=1.5",
                "HTTP 200 and state.speed=1.5",
                lambda: (
                    (lambda r: (
                        r.status_code == 200 and abs(float(r.get_json()["state"]["speed"]) - 1.5) < 1e-9,
                        f"status={r.status_code}, speed={r.get_json().get('state', {}).get('speed')}"
                    ))(
                        client.post(
                            "/api/control/speed",
                            headers=_auth("officer-token"),
                            json={"speed": 1.5},
                        )
                    )
                ),
            )

            _run_case(
                results,
                "TC-API-04",
                "api_server",
                "Emergency endpoint rejects invalid side values",
                "POST /api/control/emergency side=UPWARD",
                "HTTP 400",
                lambda: (
                    (lambda r: (r.status_code == 400, f"status={r.status_code}, body={r.get_json()}"))(
                        client.post(
                            "/api/control/emergency",
                            headers=_auth("officer-token"),
                            json={"side": "UPWARD", "duration": 8},
                        )
                    )
                ),
            )

            _run_case(
                results,
                "TC-API-05",
                "api_server",
                "Running flag should parse string false as False",
                'POST /api/control/running with {"running": "false"}',
                "set_running called with False",
                lambda: (
                    (lambda r: (
                        r.status_code == 200 and recorder["running_arg"] is False,
                        f"status={r.status_code}, set_running_arg={recorder['running_arg']}"
                    ))(
                        client.post(
                            "/api/control/running",
                            headers=_auth("officer-token"),
                            json={"running": "false"},
                        )
                    )
                ),
            )

            _run_case(
                results,
                "TC-API-06",
                "api_server",
                "Emergency endpoint should reject non-numeric duration safely",
                'POST /api/control/emergency with {"duration": "abc"}',
                "HTTP 400 with validation error (not 500)",
                lambda: (
                    (lambda r: (r.status_code == 400, f"status={r.status_code}"))(
                        client.post(
                            "/api/control/emergency",
                            headers=_auth("officer-token"),
                            json={"side": "NORTH", "duration": "abc"},
                        )
                    )
                ),
            )

        finally:
            for name, value in original_attrs.items():
                setattr(service, name, value)
            try:
                api_server.service.shutdown()
            except Exception:
                pass

    # ---------------- EMERGENCY HANDLER TESTS ----------------
    _run_case(
        results,
        "TC-EH-01",
        "emergency_handler",
        "Ambulance on already-green side should not require signal preemption",
        "Current side NORTH green; ambulance detected on NORTH",
        "active=True, emergency_side=NORTH, needs_signal_change=False",
        lambda: (
            (lambda sc, eh: (
                (eh.check_for_emergency(
                    {
                        "NORTH": [DummyAmbulance("AMB1", "NORTH", 100)],
                        "SOUTH": [],
                        "EAST": [],
                        "WEST": [],
                    },
                    960,
                    540,
                ),
                 eh.active is True and eh.emergency_side == "NORTH" and eh.needs_signal_change is False,
                 f"active={eh.active}, side={eh.emergency_side}, preemption={eh.needs_signal_change}")[1:]
            ))(SmartSignalController(), EmergencyHandler(SmartSignalController()))
        ),
    )

    def _eh_fcfs_case():
        sc = SmartSignalController()
        eh = EmergencyHandler(sc)
        v1 = DummyAmbulance("A1", "SOUTH", 80)
        v2 = DummyAmbulance("A2", "EAST", 80)
        eh._queue = [("SOUTH", v1, time.time()), ("EAST", v2, time.time() + 1)]
        eh._queued_ids = {"A1", "A2"}
        eh._serve_next()
        ok = eh.emergency_vehicle is v1 and eh.emergency_side == "SOUTH"
        return ok, f"served_first={eh.emergency_vehicle.vehicle_id if eh.emergency_vehicle else None}, side={eh.emergency_side}"

    _run_case(
        results,
        "TC-EH-02",
        "emergency_handler",
        "Emergency queue serves ambulances in FCFS order",
        "Queue=[A1(SOUTH), A2(EAST)]",
        "First served vehicle should be A1 on SOUTH",
        _eh_fcfs_case,
    )

    # ---------------- VEHICLE TESTS ----------------
    def _vehicle_stop_line_case():
        cx, cy = 960, 540
        sl = config.STOP_LINE_OFFSET

        v_n = Vehicle("NORTH", "CAR")
        v_n.y = (cy - sl) - 10

        v_s = Vehicle("SOUTH", "CAR")
        v_s.y = (cy + sl) + 10

        v_e = Vehicle("EAST", "CAR")
        v_e.x = (cx + sl) + 10

        v_w = Vehicle("WEST", "CAR")
        v_w.x = (cx - sl) - 10

        d_n = v_n.get_distance_from_stop_line(cx, cy)
        d_s = v_s.get_distance_from_stop_line(cx, cy)
        d_e = v_e.get_distance_from_stop_line(cx, cy)
        d_w = v_w.get_distance_from_stop_line(cx, cy)

        ok = d_n > 0 and d_s > 0 and d_e > 0 and d_w > 0
        return ok, f"N={d_n}, S={d_s}, E={d_e}, W={d_w}"

    _run_case(
        results,
        "TC-VEH-01",
        "vehicle",
        "Distance from stop line is positive while approaching for all sides",
        "Set positions 10px before each stop line",
        "All distances > 0",
        _vehicle_stop_line_case,
    )

    def _vehicle_plate_unique_case():
        generated = {Vehicle.generate_license_plate() for _ in range(250)}
        ok = len(generated) == 250
        return ok, f"unique_count={len(generated)}"

    _run_case(
        results,
        "TC-VEH-02",
        "vehicle",
        "Generated license plates remain unique in sample run",
        "Generate 250 plates",
        "250 unique values",
        _vehicle_plate_unique_case,
    )

    # ---------------- TRAFFIC GENERATOR TESTS ----------------
    _run_case(
        results,
        "TC-TG-01",
        "traffic_generator",
        "Generator returns None when side queue already at max limit",
        "current_count == MAX_VEHICLES_PER_SIDE",
        "No vehicle generated (None)",
        lambda: (
            (lambda tg: (
                tg.generate_vehicle("NORTH", tg.max_vehicles) is None,
                "returned=None",
            ))(TrafficGenerator())
        ),
    )

    def _tg_forced_spawn_case():
        tg = TrafficGenerator()
        tg._next_interval["NORTH"] = 0.1
        tg._last_spawn["NORTH"] = time.time() - 1.0
        v = tg.generate_vehicle("NORTH", 0)
        ok = v is not None and v.original_side == "NORTH"
        actual = f"generated={v is not None}, type={getattr(v, 'vehicle_type', None)}"
        return ok, actual

    _run_case(
        results,
        "TC-TG-02",
        "traffic_generator",
        "Generator spawns vehicle when cooldown elapsed",
        "Force elapsed > interval for NORTH",
        "Vehicle instance returned",
        _tg_forced_spawn_case,
    )

    # ---------------- SMART INTERSECTION TEST ----------------
    def _si_queued_count_case():
        sc = SmartSignalController()
        inter = SmartIntersection(sc)

        inter.vehicles["NORTH"] = [
            DummyQueueVehicle(passed=False, crossed=False),
            DummyQueueVehicle(passed=True, crossed=False),
            DummyQueueVehicle(passed=False, crossed=True),
        ]
        inter.vehicles["EAST"] = [DummyQueueVehicle(passed=False, crossed=False)]
        inter.vehicles["SOUTH"] = []
        inter.vehicles["WEST"] = []

        counts = inter._get_queued_counts(960, 540)
        ok = counts["NORTH"] == 1 and counts["EAST"] == 1 and counts["SOUTH"] == 0 and counts["WEST"] == 0
        return ok, f"counts={counts}"

    _run_case(
        results,
        "TC-SI-01",
        "smart_intersection",
        "Queued count excludes crossed and post-stopline vehicles",
        "Mix of queued/passed/crossed dummy vehicles",
        "NORTH=1, EAST=1, SOUTH=0, WEST=0",
        _si_queued_count_case,
    )

    # ---------------- VIOLATION LOGGER RESILIENCE ----------------
    def _violation_resilience_case():
        import traffic_violation.violation_logger as vlm  # type: ignore[import-not-found]

        original_mysql = vlm.mysql
        try:
            vlm.mysql = None
            logger = vlm.TrafficViolationLogger()
            dummy = DummyViolationVehicle()
            logger.log_violation(dummy)
            logger.log_violation(dummy)
            ok = logger._disabled is True and logger._warned is True
            return ok, f"disabled={logger._disabled}, warned={logger._warned}"
        finally:
            vlm.mysql = original_mysql

    _run_case(
        results,
        "TC-VL-01",
        "violation_logger",
        "DB logger disables itself gracefully when connector unavailable",
        "Force mysql module to None and log twice",
        "No crash; logger disabled after first failure",
        _violation_resilience_case,
    )

    return results


def main() -> int:
    started = datetime.now()
    results = run_additional_cases()
    finished = datetime.now()

    out_dir = os.path.abspath(os.path.dirname(__file__))
    txt_path = os.path.join(out_dir, "additional_test_execution_log.txt")
    json_path = os.path.join(out_dir, "additional_test_results.json")

    passed = sum(1 for r in results if r.status == "Pass")
    failed = sum(1 for r in results if r.status == "Fail")
    blocked = sum(1 for r in results if r.status == "Blocked")

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(
            {
                "started_at": started.isoformat(timespec="seconds"),
                "finished_at": finished.isoformat(timespec="seconds"),
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "blocked": blocked,
                "results": [r.__dict__ for r in results],
            },
            jf,
            indent=2,
        )

    with open(txt_path, "w", encoding="utf-8") as tf:
        tf.write("LAB-9 ADDITIONAL MODULE TEST EXECUTION LOG\n")
        tf.write("=" * 58 + "\n")
        tf.write(f"Started : {started.isoformat(timespec='seconds')}\n")
        tf.write(f"Finished: {finished.isoformat(timespec='seconds')}\n")
        tf.write(f"Total   : {len(results)}\n")
        tf.write(f"Passed  : {passed}\n")
        tf.write(f"Failed  : {failed}\n")
        tf.write(f"Blocked : {blocked}\n\n")

        for r in results:
            tf.write(f"[{r.test_case_id}] ({r.module}) {r.description}\n")
            tf.write(f"Input    : {r.input_data}\n")
            tf.write(f"Expected : {r.expected_output}\n")
            tf.write(f"Actual   : {r.actual_output}\n")
            tf.write(f"Status   : {r.status}\n")
            tf.write("-" * 58 + "\n")

    print(f"Generated: {txt_path}")
    print(f"Generated: {json_path}")
    print(f"Summary: total={len(results)} passed={passed} failed={failed} blocked={blocked}")
    for r in results:
        print(f"{r.test_case_id}: {r.status} | {r.actual_output}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise

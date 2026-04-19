"""
LAB-9 automated execution for SmartSignalController test cases.
Generates machine-readable and text logs for assignment evidence.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CaseResult:
    test_case_id: str
    description: str
    input_data: str
    expected_output: str
    actual_output: str
    status: str


def _build_controller():
    # Add smart_traffic package root to import path.
    here = os.path.abspath(os.path.dirname(__file__))
    repo_root = os.path.abspath(os.path.join(here, "..", ".."))
    smart_traffic_root = os.path.join(repo_root, "smart_traffic")
    if smart_traffic_root not in sys.path:
        sys.path.insert(0, smart_traffic_root)

    from smart_traffic_system.smart_signal_controller import SmartSignalController  # type: ignore[import-not-found]
    from traffic_signal.signal_state import SignalState  # type: ignore[import-not-found]

    return SmartSignalController, SignalState


def run_cases() -> list[CaseResult]:
    SmartSignalController, SignalState = _build_controller()
    results: list[CaseResult] = []

    # TC-01: Initialization sanity
    c = SmartSignalController()
    try:
        cond = (
            c.current_side == "NORTH"
            and c.get_signal_state("NORTH") == SignalState.GREEN
            and c.get_signal_state("EAST") == SignalState.RED
            and c.get_signal_state("SOUTH") == SignalState.RED
            and c.get_signal_state("WEST") == SignalState.RED
        )
        results.append(
            CaseResult(
                "TC-SSC-01",
                "Controller initializes with NORTH green and others red",
                "Instantiate SmartSignalController()",
                "NORTH=GREEN, EAST/SOUTH/WEST=RED",
                f"N={c.get_signal_state('NORTH').name}, E={c.get_signal_state('EAST').name}, S={c.get_signal_state('SOUTH').name}, W={c.get_signal_state('WEST').name}",
                "Pass" if cond else "Fail",
            )
        )
    except Exception as exc:
        results.append(
            CaseResult(
                "TC-SSC-01",
                "Controller initializes with NORTH green and others red",
                "Instantiate SmartSignalController()",
                "NORTH=GREEN, EAST/SOUTH/WEST=RED",
                f"Exception: {type(exc).__name__}: {exc}",
                "Fail",
            )
        )

    # TC-02: Timed GREEN -> YELLOW transition
    c = SmartSignalController()
    c.last_change_time -= c.green_duration + 0.1
    c.update({"NORTH": 3, "EAST": 1, "SOUTH": 0, "WEST": 2})
    actual_2 = (
        f"NORTH={c.get_signal_state('NORTH').name}, "
        f"EAST={c.get_signal_state('EAST').name}, "
        f"yellow_pass_side={c.yellow_pass_side}"
    )
    results.append(
        CaseResult(
            "TC-SSC-02",
            "After green duration, current and next sides become YELLOW",
            "elapsed > green_duration, queued NORTH > 0",
            "NORTH=YELLOW, EAST=YELLOW, yellow_pass_side=NORTH",
            actual_2,
            "Pass"
            if c.get_signal_state("NORTH") == SignalState.YELLOW
            and c.get_signal_state("EAST") == SignalState.YELLOW
            and c.yellow_pass_side == "NORTH"
            else "Fail",
        )
    )

    # TC-03: Timed YELLOW -> next GREEN transition
    c.last_change_time -= c.yellow_duration + 0.1
    c.update({"NORTH": 0, "EAST": 3, "SOUTH": 2, "WEST": 1})
    actual_3 = (
        f"current_side={c.current_side}, "
        f"NORTH={c.get_signal_state('NORTH').name}, "
        f"EAST={c.get_signal_state('EAST').name}"
    )
    results.append(
        CaseResult(
            "TC-SSC-03",
            "After yellow duration, next side turns GREEN and pointer advances",
            "elapsed > yellow_duration in YELLOW phase",
            "current_side=EAST, NORTH=RED, EAST=GREEN",
            actual_3,
            "Pass"
            if c.current_side == "EAST"
            and c.get_signal_state("NORTH") == SignalState.RED
            and c.get_signal_state("EAST") == SignalState.GREEN
            else "Fail",
        )
    )

    # TC-04: Early switch when queue is empty
    c = SmartSignalController()
    c.last_change_time = c.last_change_time  # elapsed ~0, below green duration
    c.update({"NORTH": 0, "EAST": 2, "SOUTH": 1, "WEST": 1})
    actual_4 = (
        f"NORTH={c.get_signal_state('NORTH').name}, "
        f"EAST={c.get_signal_state('EAST').name}"
    )
    results.append(
        CaseResult(
            "TC-SSC-04",
            "Controller switches early when current queue is empty",
            "queued_counts[NORTH]=0 and elapsed < green_duration",
            "NORTH=YELLOW and EAST=YELLOW",
            actual_4,
            "Pass"
            if c.get_signal_state("NORTH") == SignalState.YELLOW
            and c.get_signal_state("EAST") == SignalState.YELLOW
            else "Fail",
        )
    )

    # TC-05: No early switch when queue present
    c = SmartSignalController()
    c.update({"NORTH": 2, "EAST": 0, "SOUTH": 0, "WEST": 0})
    actual_5 = (
        f"NORTH={c.get_signal_state('NORTH').name}, "
        f"EAST={c.get_signal_state('EAST').name}"
    )
    results.append(
        CaseResult(
            "TC-SSC-05",
            "Controller stays GREEN if queue exists and duration not exceeded",
            "queued_counts[NORTH]=2 and elapsed < green_duration",
            "NORTH=GREEN and EAST=RED",
            actual_5,
            "Pass"
            if c.get_signal_state("NORTH") == SignalState.GREEN
            and c.get_signal_state("EAST") == SignalState.RED
            else "Fail",
        )
    )

    # TC-06: Missing queued_counts should keep normal timing (expected), but code early-switches
    c = SmartSignalController()
    c.update(None)
    actual_6 = (
        f"NORTH={c.get_signal_state('NORTH').name}, "
        f"EAST={c.get_signal_state('EAST').name}"
    )
    results.append(
        CaseResult(
            "TC-SSC-06",
            "Calling update(None) should preserve GREEN until timer (robust default)",
            "queued_counts=None on first frame",
            "NORTH remains GREEN and EAST remains RED",
            actual_6,
            "Pass"
            if c.get_signal_state("NORTH") == SignalState.GREEN
            and c.get_signal_state("EAST") == SignalState.RED
            else "Fail",
        )
    )

    # TC-07: Case-insensitive emergency side handling
    c = SmartSignalController()
    try:
        c.start_emergency("north")
        c.last_change_time -= c.yellow_duration + 0.1
        c.update({"NORTH": 1, "EAST": 1, "SOUTH": 1, "WEST": 1})
        actual_7 = f"current_side={c.current_side}, emergency_phase_active={c.emergency_mode}"
        status_7 = "Pass" if c.current_side == "NORTH" and c.emergency_mode else "Fail"
    except Exception as exc:
        actual_7 = f"Exception: {type(exc).__name__}: {exc}"
        status_7 = "Fail"

    results.append(
        CaseResult(
            "TC-SSC-07",
            "Emergency side should be accepted in lowercase input",
            'start_emergency("north")',
            "Emergency starts for NORTH without exception",
            actual_7,
            status_7,
        )
    )

    # TC-08: Invalid emergency side should throw clear ValueError
    c = SmartSignalController()
    try:
        c.start_emergency("UPWARD")
        actual_8 = "No exception raised"
        status_8 = "Fail"
    except ValueError as exc:
        actual_8 = f"ValueError: {exc}"
        status_8 = "Pass"
    except Exception as exc:
        actual_8 = f"Unexpected exception: {type(exc).__name__}: {exc}"
        status_8 = "Fail"

    results.append(
        CaseResult(
            "TC-SSC-08",
            "Invalid emergency side should be rejected",
            'start_emergency("UPWARD")',
            "Raise ValueError('Invalid side')",
            actual_8,
            status_8,
        )
    )

    return results


def main() -> int:
    started = datetime.now()
    results = run_cases()
    finished = datetime.now()

    out_dir = os.path.abspath(os.path.dirname(__file__))
    txt_path = os.path.join(out_dir, "test_execution_log.txt")
    json_path = os.path.join(out_dir, "test_results.json")

    passed = sum(1 for r in results if r.status == "Pass")
    failed = len(results) - passed

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(
            {
                "started_at": started.isoformat(timespec="seconds"),
                "finished_at": finished.isoformat(timespec="seconds"),
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "results": [r.__dict__ for r in results],
            },
            jf,
            indent=2,
        )

    with open(txt_path, "w", encoding="utf-8") as tf:
        tf.write("SMART SIGNAL CONTROLLER TEST EXECUTION LOG\n")
        tf.write("=" * 52 + "\n")
        tf.write(f"Started : {started.isoformat(timespec='seconds')}\n")
        tf.write(f"Finished: {finished.isoformat(timespec='seconds')}\n")
        tf.write(f"Total   : {len(results)}\n")
        tf.write(f"Passed  : {passed}\n")
        tf.write(f"Failed  : {failed}\n")
        tf.write("\n")

        for r in results:
            tf.write(f"[{r.test_case_id}] {r.description}\n")
            tf.write(f"Input    : {r.input_data}\n")
            tf.write(f"Expected : {r.expected_output}\n")
            tf.write(f"Actual   : {r.actual_output}\n")
            tf.write(f"Status   : {r.status}\n")
            tf.write("-" * 52 + "\n")

    # Console output for terminal capture
    print(f"Generated: {txt_path}")
    print(f"Generated: {json_path}")
    print(f"Summary: total={len(results)} passed={passed} failed={failed}")
    for r in results:
        print(f"{r.test_case_id}: {r.status} | {r.actual_output}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:  # pragma: no cover
        traceback.print_exc()
        raise

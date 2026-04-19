# CS331 Software Engineering Lab 9

## Project: Smart Traffic Signal Automation System

## Q1(a) Test Plan

### 1. Objective of Testing
- Validate correctness, reliability, and robustness of the Smart Traffic Signal Automation System.
- Verify signal sequencing, emergency preemption behavior, adaptive timing, and API-facing control expectations.
- Identify defects that can cause wrong traffic behavior or runtime exceptions.

### 2. Scope (Modules/Features to be Tested)
- In scope modules:
  - Smart signal control logic in SmartSignalController.
  - Emergency handling path in start_emergency and transition phases.
  - Timing behavior: GREEN to YELLOW to next GREEN.
  - Adaptive early switch behavior based on queue counts.
- Broader project modules reviewed for plan scope:
  - smart_traffic: simulation core, emergency, violations, visualization, API server.
  - smart_traffic_signal_ui: React role-based dashboard for controls and monitoring.
- Out of scope for this execution run:
  - Full GUI rendering validation (pygame visual checks).
  - MySQL integration tests requiring live DB setup.

### 3. Types of Testing Performed
- Unit testing:
  - Functional and state-transition tests for SmartSignalController.
- Boundary and negative testing:
  - Missing input (None queue map), invalid side names, case-sensitivity checks.
- Static review-assisted testing:
  - Cross-check behavior against expected API/controller robustness requirements.

### 4. Tools Used
- Python 3.13.2 runtime.
- Custom Python test execution script:
  - assignment/LAB-9/execute_smart_signal_tests.py
- Evidence logs generated automatically:
  - assignment/LAB-9/test_execution_log.txt
  - assignment/LAB-9/test_results.json
- VS Code terminal for execution.

### 5. Entry Criteria
- Source code available and readable.
- Smart traffic module importable in Python environment.
- Test script prepared with 8 deterministic test cases.

### 6. Exit Criteria
- All 8 planned test cases executed.
- Actual outputs recorded for each case.
- Pass/Fail status assigned for each case.
- Defect list prepared for all failing tests with severity and fix suggestions.

---

## Q1(b) Test Cases (Major Module: SmartSignalController)

| Test Case ID | Test Scenario / Description | Input Data | Expected Output | Actual Output | Status |
|---|---|---|---|---|---|
| TC-SSC-01 | Controller initializes with NORTH green and others red | Instantiate SmartSignalController() | NORTH=GREEN, EAST/SOUTH/WEST=RED | N=GREEN, E=RED, S=RED, W=RED | Pass |
| TC-SSC-02 | GREEN to YELLOW transition after configured green duration | elapsed > green_duration, queued NORTH > 0 | NORTH=YELLOW, EAST=YELLOW, yellow_pass_side=NORTH | NORTH=YELLOW, EAST=YELLOW, yellow_pass_side=NORTH | Pass |
| TC-SSC-03 | YELLOW to next GREEN transition after yellow duration | elapsed > yellow_duration in YELLOW phase | current_side=EAST, NORTH=RED, EAST=GREEN | current_side=EAST, NORTH=RED, EAST=GREEN | Pass |
| TC-SSC-04 | Early switch when current side queue becomes empty | queued_counts[NORTH]=0 and elapsed < green_duration | NORTH=YELLOW and EAST=YELLOW | NORTH=YELLOW, EAST=YELLOW | Pass |
| TC-SSC-05 | No early switch when queue exists and duration not exceeded | queued_counts[NORTH]=2 and elapsed < green_duration | NORTH=GREEN and EAST=RED | NORTH=GREEN, EAST=RED | Pass |
| TC-SSC-06 | Robust default behavior for missing queue map | queued_counts=None on first frame | NORTH remains GREEN and EAST remains RED | NORTH=YELLOW, EAST=YELLOW | Fail |
| TC-SSC-07 | Emergency side handling should accept lowercase input | start_emergency("north") | Emergency starts for NORTH without exception | Exception: ValueError: 'north' is not in list | Fail |
| TC-SSC-08 | Invalid emergency side should be rejected clearly | start_emergency("UPWARD") | Raise ValueError("Invalid side") | No exception raised | Fail |

---

## Q2(a) Test Case Execution and Evidence

### Execution Summary
- Total test cases executed: 8
- Passed: 5
- Failed: 3
- Execution timestamp:
  - Started: 2026-04-19T22:36:41
  - Finished: 2026-04-19T22:36:41

### Execution Command Used
- c:/Users/gauta/sem6/softwareProject-CS331/CS331-software-project/CS331-software-project/.venv-1/Scripts/python.exe assignment/LAB-9/execute_smart_signal_tests.py

### Evidence (Logs)
- Detailed execution log:
  - assignment/LAB-9/test_execution_log.txt
- Structured machine-readable results:
  - assignment/LAB-9/test_results.json
- Test runner script used:
  - assignment/LAB-9/execute_smart_signal_tests.py

### Post-Pull Revalidation Note
- Re-verified after pulling latest code on branch main.
- Result remained unchanged: 8 executed, 5 passed, 3 failed.
- Therefore, no mandatory correction is required in existing Q1/Q2 findings.

### Optional Additions After Pull
- Add a small appendix titled "Integration Test Opportunities" for newly emphasized backend/UI features:
  - Role-based API authorization checks (401/403 across admin/officer/viewer roles).
  - Violation workflow API chain: update action then conditional delete.
  - Socket state stream stability test (connect, disconnect, reconnect).

---

## Q2(b) Defects Identified and Analysis

### Bug ID: BUG-SSC-01
- Description:
  - SmartSignalController performs an immediate early switch when update(None) is called, because missing queue map defaults current queue to 0.
- Steps to Reproduce:
  1. Create SmartSignalController instance.
  2. Call update(None) on initial cycle.
  3. Observe signal states.
- Expected vs Actual:
  - Expected: Without queue input, controller should continue normal GREEN timing.
  - Actual: Controller instantly transitions NORTH and EAST to YELLOW.
- Severity:
  - Medium
- Suggested Fix:
  - In update(), when queued_counts is None, disable early-switch logic and only allow timing-based transition.
  - Example approach: pass a flag into _update_normal to treat missing input as unknown instead of zero.

### Bug ID: BUG-SSC-02
- Description:
  - start_emergency is case-sensitive and fails for lowercase side values used by callers.
- Steps to Reproduce:
  1. Create SmartSignalController instance.
  2. Call start_emergency("north").
  3. Run one update step after yellow duration.
- Expected vs Actual:
  - Expected: Input should be normalized (uppercased) and emergency should activate for NORTH.
  - Actual: ValueError occurs ('north' is not in list).
- Severity:
  - High
- Suggested Fix:
  - Normalize input side = side.upper().strip() and validate against allowed sides.

### Bug ID: BUG-SSC-03
- Description:
  - start_emergency does not validate invalid side names at call time.
- Steps to Reproduce:
  1. Create SmartSignalController instance.
  2. Call start_emergency("UPWARD").
- Expected vs Actual:
  - Expected: Immediate ValueError("Invalid side").
  - Actual: No exception raised at method call, causing hidden invalid internal state.
- Severity:
  - High
- Suggested Fix:
  - Add explicit guard in start_emergency:
    - if side not in self.sides: raise ValueError("Invalid side")
  - Keep validation consistent with API layer side checks.

---

## Conclusion
- The major module SmartSignalController is functionally correct for core cycle and adaptive switching scenarios (5/5 key functional checks passed).
- Three robustness defects were identified in input handling and default behavior paths.
- Fixing these defects will improve controller stability, prevent runtime exceptions, and make behavior safer for integration with UI/API callers.

---

## Additional Module Testing (Post-Pull)

### Modules Covered
- api_server (authorization/control endpoints)
- emergency_handler
- vehicle
- traffic_generator
- smart_intersection
- violation_logger

### Additional Execution Summary
- Total additional cases: 14
- Passed: 12
- Failed: 2
- Blocked: 0
- Timestamp:
  - Started: 2026-04-19T23:55:24
  - Finished: 2026-04-19T23:55:26

### Additional Test Results Snapshot
- Passed cases:
  - TC-API-01, TC-API-02, TC-API-03, TC-API-04
  - TC-EH-01, TC-EH-02
  - TC-VEH-01, TC-VEH-02
  - TC-TG-01, TC-TG-02
  - TC-SI-01
  - TC-VL-01
- Failed API cases:
  - TC-API-05 (boolean parsing issue for running flag)
  - TC-API-06 (invalid emergency duration returns 500 instead of 400)

### Additional Defects Found (API)

#### Bug ID: BUG-API-01
- Description:
  - Endpoint /api/control/running converts string values using bool(), so "false" becomes True.
- Steps to Reproduce:
  1. Send POST /api/control/running with JSON {"running": "false"}.
  2. Observe argument passed to set_running and resulting state.
- Expected vs Actual:
  - Expected: "false" should be parsed as False.
  - Actual: bool("false") evaluates to True, so simulation stays/runs as True.
- Severity:
  - Medium
- Suggested Fix:
  - Add explicit boolean normalization for string inputs (true/false/1/0/yes/no) before calling set_running.

#### Bug ID: BUG-API-02
- Description:
  - Endpoint /api/control/emergency does float() conversion outside error handling and returns HTTP 500 for invalid duration.
- Steps to Reproduce:
  1. Send POST /api/control/emergency with JSON {"side": "NORTH", "duration": "abc"}.
  2. Observe server response.
- Expected vs Actual:
  - Expected: HTTP 400 with clear validation message for invalid duration.
  - Actual: ValueError propagates and endpoint returns HTTP 500.
- Severity:
  - High
- Suggested Fix:
  - Wrap duration parsing in try/except and return 400 for non-numeric values.

### Additional Evidence Files
- assignment/LAB-9/execute_additional_tests.py
- assignment/LAB-9/additional_test_execution_log.txt
- assignment/LAB-9/additional_test_results.json

### Environment Setup Used for Additional API Execution
- Installed Python packages in active venv:
  - flask
  - flask-socketio
  - pygame

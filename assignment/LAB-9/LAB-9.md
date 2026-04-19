# CS331 Software Engineering Lab 9

## Project: Smart Traffic Signal Automation System

## Q1(a) Test Plan

### Objective of Testing
- Validate correctness, reliability, and robustness of the Smart Traffic Signal Automation System.
- Verify signal sequencing, emergency preemption behavior, adaptive timing, and API-facing control expectations.
- Identify defects that can cause wrong traffic behavior or runtime exceptions.

### Scope (Modules/Features to be Tested)
- Smart signal control logic in SmartSignalController.
- Emergency handling path in start_emergency and transition phases.
- Timing behavior: GREEN to YELLOW to next GREEN.
- Adaptive early switch behavior based on queue counts.

### Types of Testing Performed
- Unit testing
- Functional testing
- Boundary and negative testing

### Tools
- Python 3.13.2
- VS Code terminal
- Custom test scripts in assignment/LAB-9

### Entry Criteria
- Source code available and readable.
- Python environment configured.
- Test script prepared with deterministic test cases.

### Exit Criteria
- All planned test cases executed.
- Actual outputs recorded for each case.
- Pass/Fail status assigned.
- Defects documented with severity and suggested fixes.

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

### Evidence
- assignment/LAB-9/test_execution_log.txt
- assignment/LAB-9/test_results.json

---

## Q2(b) Defects Identified and Analysis

### Bug ID: BUG-SSC-01
- Description: update(None) causes immediate early switch due to default zero queue.
- Steps to reproduce:
  1. Create SmartSignalController.
  2. Call update(None).
  3. Observe signals.
- Expected vs Actual:
  - Expected: Continue normal GREEN timing.
  - Actual: NORTH and EAST switch to YELLOW immediately.
- Severity: Medium
- Suggested fix: Handle None queue input separately and disable early-switch logic for unknown queue state.

### Bug ID: BUG-SSC-02
- Description: start_emergency is case-sensitive and fails for lowercase side values.
- Steps to reproduce:
  1. Create SmartSignalController.
  2. Call start_emergency("north").
- Expected vs Actual:
  - Expected: Input normalized to NORTH and accepted.
  - Actual: ValueError ('north' is not in list).
- Severity: High
- Suggested fix: Normalize side input with upper().strip() and validate.

### Bug ID: BUG-SSC-03
- Description: start_emergency does not validate invalid side names at call time.
- Steps to reproduce:
  1. Create SmartSignalController.
  2. Call start_emergency("UPWARD").
- Expected vs Actual:
  - Expected: Immediate ValueError("Invalid side").
  - Actual: No exception raised at call time.
- Severity: High
- Suggested fix: Add explicit side validation and raise ValueError for invalid side.

---

## Conclusion
- Core cycle and adaptive switching scenarios passed.
- Three robustness defects were identified in SmartSignalController input handling paths.

# Q1(a) Test Plan

## Objective of Testing
- Verify correctness, reliability, and robustness of the Smart Traffic Signal System.
- Validate signal sequencing, adaptive switching, emergency handling, vehicle movement logic, traffic generation, queue counting, and violation logging resilience.
- Identify defects that can cause incorrect traffic control behavior or runtime failures.

## Scope (Modules/Features to be Tested)
- SmartSignalController: initialization, timed transitions, early switching, emergency input handling.
- EmergencyHandler: emergency detection and FCFS queue behavior.
- Vehicle: stop-line distance logic and license-plate uniqueness.
- TrafficGenerator: spawn cooldown behavior and max queue limit.
- SmartIntersection: queued vehicle counting behavior.
- TrafficViolationLogger: graceful degradation when DB connector is unavailable.

## Types of Testing Performed
- Unit Testing
- Functional Testing
- Negative Testing
- Boundary/Validation Testing

## Tools
- Python 3.13.2
- Custom test scripts
- VS Code terminal logs
- Text and JSON execution logs

## Entry Criteria
- Project source code available.
- Python environment configured.
- Test scripts prepared for selected modules.

## Exit Criteria
- All planned test cases executed.
- Actual outputs recorded with status.
- Defects documented with severity and suggested fixes.

---

# Q1(b) Test Cases

| Test Case ID | Test Scenario / Description | Input Data | Expected Output | Actual Output | Status |
|---|---|---|---|---|---|
| TC-01 | SmartSignalController initializes with correct default lights | Instantiate SmartSignalController() | NORTH=GREEN, EAST/SOUTH/WEST=RED | N=GREEN, E=RED, S=RED, W=RED | Pass |
| TC-02 | GREEN to YELLOW transition after green duration | elapsed > green_duration, queued NORTH > 0 | NORTH=YELLOW, EAST=YELLOW, yellow_pass_side=NORTH | NORTH=YELLOW, EAST=YELLOW, yellow_pass_side=NORTH | Pass |
| TC-03 | YELLOW to next GREEN transition after yellow duration | elapsed > yellow_duration in YELLOW phase | current_side=EAST, NORTH=RED, EAST=GREEN | current_side=EAST, NORTH=RED, EAST=GREEN | Pass |
| TC-04 | Early switch when current queue is empty | queued_counts[NORTH]=0 and elapsed < green_duration | NORTH=YELLOW and EAST=YELLOW | NORTH=YELLOW, EAST=YELLOW | Pass |
| TC-05 | No early switch while queue exists | queued_counts[NORTH]=2 and elapsed < green_duration | NORTH=GREEN and EAST=RED | NORTH=GREEN, EAST=RED | Pass |
| TC-06 | update(None) should keep normal timer behavior | queued_counts=None on first frame | NORTH remains GREEN and EAST remains RED | NORTH=YELLOW, EAST=YELLOW | Fail |
| TC-07 | Emergency input should accept lowercase side | start_emergency("north") | Emergency starts for NORTH without exception | Exception: ValueError: 'north' is not in list | Fail |
| TC-08 | Invalid emergency side should be rejected | start_emergency("UPWARD") | Raise ValueError('Invalid side') | No exception raised | Fail |
| TC-09 | Already-green emergency side should avoid preemption | NORTH already green; ambulance on NORTH | active=True, emergency_side=NORTH, needs_signal_change=False | active=True, side=NORTH, preemption=False | Pass |
| TC-10 | Emergency FCFS order | Queue=[A1(SOUTH), A2(EAST)] | First served ambulance is A1 on SOUTH | served_first=A1, side=SOUTH | Pass |
| TC-11 | Stop-line distance positive while approaching (all sides) | Positions 10px before each stop line | Distances > 0 for N/S/E/W | N=10, S=10, E=10, W=10 | Pass |
| TC-12 | License plates remain unique | Generate 250 plates | 250 unique values | unique_count=250 | Pass |
| TC-13 | Generator blocks spawn at max queue | current_count == MAX_VEHICLES_PER_SIDE | None returned | returned=None | Pass |
| TC-14 | Generator spawns after cooldown elapsed | Forced elapsed > interval for NORTH | Vehicle instance generated | generated=True, type=TRUCK | Pass |
| TC-15 | SmartIntersection queued count excludes crossed/passed | Mixed queued/passed/crossed vehicles | NORTH=1, EAST=1, SOUTH=0, WEST=0 | counts={'NORTH': 1, 'SOUTH': 0, 'EAST': 1, 'WEST': 0} | Pass |
| TC-16 | Violation logger handles missing DB connector safely | Force mysql module None; log twice | No crash; logger disables itself | disabled=True, warned=True | Pass |

---

# Q2(a) Test Case Execution and Results with Evidence

## Execution Summary
- Total test cases executed: 16
- Passed: 13
- Failed: 3

## Evidence
- Combined execution log: assignment/LAB-9/final_16_combined_execution_log.txt

---

# Q2(b) Defects (Bugs) Identified During Testing

## Bug ID: BUG-01
- Description of issue:
  - update(None) triggers immediate early switch because missing queue data is treated as zero vehicles.
- Steps to reproduce:
  1. Create SmartSignalController instance.
  2. Call update(None).
  3. Observe signal state change.
- Expected vs Actual Result:
  - Expected: Continue normal GREEN timing.
  - Actual: NORTH and EAST move to YELLOW immediately.
- Severity level:
  - Medium
- Suggested fix:
  - Handle None queue input separately and disable early-switch logic when queue data is unavailable.

## Bug ID: BUG-02
- Description of issue:
  - Lowercase side input in start_emergency causes exception.
- Steps to reproduce:
  1. Create SmartSignalController instance.
  2. Call start_emergency("north").
- Expected vs Actual Result:
  - Expected: Input normalized and emergency starts for NORTH.
  - Actual: ValueError raised ('north' is not in list).
- Severity level:
  - High
- Suggested fix:
  - Normalize and validate side input: side = side.upper().strip().

## Bug ID: BUG-03
- Description of issue:
  - Invalid side values in start_emergency are not validated at call time.
- Steps to reproduce:
  1. Create SmartSignalController instance.
  2. Call start_emergency("UPWARD").
- Expected vs Actual Result:
  - Expected: Immediate ValueError("Invalid side").
  - Actual: No validation error at call; invalid state continues.
- Severity level:
  - High
- Suggested fix:
  - Add explicit allowed-side validation and raise ValueError for invalid input.

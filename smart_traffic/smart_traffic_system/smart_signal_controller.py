"""
Smart Signal Controller Module

Adaptive version of the normal sequential controller:
- Maximum green per side is GREEN_LIGHT_DURATION
- If the current side has no queued vehicles, it may switch early
  (yellow transition happens immediately).

Emergency preemption behavior is identical to the normal system.
"""

import time
from traffic_signal.signal_state import SignalState
from config import GREEN_LIGHT_DURATION, YELLOW_LIGHT_DURATION


class SmartSignalController:
    """
    Adaptive controller with emergency preemption.

    Call update(queued_counts) each frame, where queued_counts is a dict:
      {"NORTH": int, "SOUTH": int, "EAST": int, "WEST": int}
    """

    def __init__(self):
        self.sides = ["NORTH", "EAST", "SOUTH", "WEST"]  # clockwise order
        self.current_side_index = 0
        self.current_side = self.sides[0]

        # All signals start as RED
        self.signals = {
            "NORTH": SignalState.RED,
            "SOUTH": SignalState.RED,
            "EAST": SignalState.RED,
            "WEST": SignalState.RED,
        }

        # Set first side to GREEN
        self.signals[self.current_side] = SignalState.GREEN

        # Timing
        self.last_change_time = time.time()
        self.green_duration = GREEN_LIGHT_DURATION
        self.yellow_duration = YELLOW_LIGHT_DURATION

        # ---- Emergency preemption state ---- #
        self.emergency_mode = False
        # Phases: "TRANSITION_TO"  → yellow before giving emergency green
        #         "ACTIVE"         → emergency side is green
        #         "TRANSITION_BACK"→ yellow before resuming normal cycle
        self._emergency_phase = None
        self._emergency_side = None
        self._resume_side_index = None
        self._resume_side = None
        self._resume_green_remaining = None

        # During any yellow phase (normal or emergency), this is the side
        # whose vehicles are allowed to keep passing.
        self.yellow_pass_side = None

    # ================================================================== #
    #  Update (called every frame)
    # ================================================================== #
    def update(self, queued_counts: dict | None = None):
        if self.emergency_mode:
            self._update_emergency()
        else:
            self._update_normal(queued_counts or {})

    # ------------------------------------------------------------------ #
    #  Normal cycling (adaptive)
    # ------------------------------------------------------------------ #
    def _update_normal(self, queued_counts: dict):
        """
        GREEN → YELLOW (current + next-side get-ready)
        YELLOW → current RED, next GREEN

        If the current side has no queued vehicles, it can transition
        to YELLOW early.
        """
        current_time = time.time()
        elapsed = current_time - self.last_change_time

        current_state = self.signals[self.current_side]
        next_index = (self.current_side_index + 1) % len(self.sides)
        next_side = self.sides[next_index]

        queued_now = queued_counts.get(self.current_side, 0)
        can_switch_early = (queued_now == 0)

        # GREEN → YELLOW  (both current *and* next side turn yellow)
        if (current_state == SignalState.GREEN and
                (elapsed >= self.green_duration or can_switch_early)):
            self.signals[self.current_side] = SignalState.YELLOW
            self.signals[next_side] = SignalState.YELLOW
            self.yellow_pass_side = self.current_side   # outgoing side passes
            self.last_change_time = current_time

        # YELLOW → current goes RED, next goes GREEN
        elif current_state == SignalState.YELLOW and elapsed >= self.yellow_duration:
            self.signals[self.current_side] = SignalState.RED
            self.signals[next_side] = SignalState.GREEN
            self.yellow_pass_side = None

            # Advance pointer
            self.current_side_index = next_index
            self.current_side = next_side
            self.last_change_time = current_time

    # ================================================================== #
    #  Emergency preemption (unchanged)
    # ================================================================== #
    def start_emergency(self, side: str):
        self.emergency_mode = True
        self._emergency_side = side

        # If the emergency side is already green, skip transition
        if self.current_side == side and self.signals[side] == SignalState.GREEN:
            self._emergency_phase = "ACTIVE"
            for s in self.sides:
                if s != side:
                    self.signals[s] = SignalState.RED
            return

        # Otherwise, transition:  current → YELLOW, emergency → YELLOW
        self._emergency_phase = "TRANSITION_TO"
        self.yellow_pass_side = self.current_side   # outgoing side passes
        for s in self.sides:
            if s == self.current_side or s == side:
                self.signals[s] = SignalState.YELLOW
            else:
                self.signals[s] = SignalState.RED
        self.last_change_time = time.time()

    def end_emergency(self, resume_side_index: int, resume_side: str, resume_green_remaining: float | None = None):
        self._resume_side_index = resume_side_index
        self._resume_side = resume_side
        self._resume_green_remaining = resume_green_remaining
        self._emergency_phase = "TRANSITION_BACK"

        # Emergency side → YELLOW, resume side → YELLOW (get-ready)
        self.yellow_pass_side = self._emergency_side
        for s in self.sides:
            if s == self._emergency_side or s == self._resume_side:
                self.signals[s] = SignalState.YELLOW
            else:
                self.signals[s] = SignalState.RED
        self.last_change_time = time.time()

    def _update_emergency(self):
        current_time = time.time()
        elapsed = current_time - self.last_change_time

        # Phase 1: waiting for yellow before giving emergency green
        if self._emergency_phase == "TRANSITION_TO":
            if elapsed >= self.yellow_duration:
                for s in self.sides:
                    self.signals[s] = SignalState.RED
                self.signals[self._emergency_side] = SignalState.GREEN
                self.current_side_index = self.sides.index(
                    self._emergency_side)
                self.current_side = self._emergency_side
                self.yellow_pass_side = None
                self._emergency_phase = "ACTIVE"
                self.last_change_time = current_time

        # Phase 2: emergency green — just hold, no time-out
        elif self._emergency_phase == "ACTIVE":
            pass

        # Phase 3: yellow transition back to normal cycle
        elif self._emergency_phase == "TRANSITION_BACK":
            if elapsed >= self.yellow_duration:
                for s in self.sides:
                    self.signals[s] = SignalState.RED

                self.current_side_index = self._resume_side_index
                self.current_side = self._resume_side
                self.signals[self.current_side] = SignalState.GREEN
                self.yellow_pass_side = None

                # Resume with remaining green time (min 5s)
                resume_remaining = self._resume_green_remaining
                if resume_remaining is None:
                    resume_remaining = self.green_duration
                resume_remaining = max(
                    5.0, min(self.green_duration, resume_remaining))
                self.last_change_time = current_time - \
                    (self.green_duration - resume_remaining)

                # Clear emergency state
                self.emergency_mode = False
                self._emergency_phase = None
                self._emergency_side = None
                self._resume_side_index = None
                self._resume_side = None
                self._resume_green_remaining = None

    # ================================================================== #
    #  Queries
    # ================================================================== #
    def get_signal_state(self, side):
        return self.signals.get(side, SignalState.RED)

    def is_green(self, side):
        return self.signals.get(side) == SignalState.GREEN

    def is_red(self, side):
        return self.signals.get(side) == SignalState.RED

    def get_green_elapsed(self, side):
        if self.signals.get(side) != SignalState.GREEN:
            return -1
        return time.time() - self.last_change_time

    def get_remaining_time(self):
        current_time = time.time()
        elapsed = current_time - self.last_change_time

        current_state = self.signals[self.current_side]
        if current_state == SignalState.GREEN:
            if self.emergency_mode and self._emergency_phase == "ACTIVE":
                return 0
            return max(0, self.green_duration - elapsed)
        elif current_state == SignalState.YELLOW:
            return max(0, self.yellow_duration - elapsed)
        return 0

    # ================================================================== #
    #  Manual controls (for API/UI)
    # ================================================================== #
    def set_manual_green(self, side: str):
        """Force one side to GREEN and all others to RED."""
        side = side.upper()
        if side not in self.sides:
            raise ValueError(f"Invalid side: {side}")

        self.emergency_mode = False
        self._emergency_phase = None
        self._emergency_side = None
        self._resume_side_index = None
        self._resume_side = None
        self._resume_green_remaining = None
        self.yellow_pass_side = None

        for s in self.sides:
            self.signals[s] = SignalState.RED
        self.signals[side] = SignalState.GREEN

        self.current_side_index = self.sides.index(side)
        self.current_side = side
        self.last_change_time = time.time()

    def set_durations(self, green_duration: float, yellow_duration: float):
        """Update cycle timing values with safe lower bounds."""
        self.green_duration = max(5.0, float(green_duration))
        self.yellow_duration = max(2.0, float(yellow_duration))

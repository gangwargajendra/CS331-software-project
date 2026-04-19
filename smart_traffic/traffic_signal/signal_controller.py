"""
Signal Controller Module
Controls traffic signal timing and state changes for all sides.

Supports two modes:
  • Normal cycling:  NORTH → EAST → SOUTH → WEST (clockwise)
  • Emergency preemption: smooth transition to give one side green,
    then smooth transition back to the interrupted cycle.
"""

import time
from .signal_state import SignalState
from config import GREEN_LIGHT_DURATION, YELLOW_LIGHT_DURATION


class SignalController:
    """
    Controls traffic signals for a 4-sided intersection.
    Cycles through sides sequentially with support for emergency preemption.
    """

    def __init__(self):
        """Initialize signal controller with all sides starting as RED"""
        self.sides = ["NORTH", "EAST", "SOUTH", "WEST"]  # clockwise order
        self.current_side_index = 0
        self.current_side = self.sides[0]

        # All signals start as RED
        self.signals = {
            "NORTH": SignalState.RED,
            "SOUTH": SignalState.RED,
            "EAST": SignalState.RED,
            "WEST": SignalState.RED
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
        # whose vehicles are allowed to keep passing.  The OTHER yellow
        # side is the "get-ready" side whose vehicles must wait.
        self.yellow_pass_side = None

    # ================================================================== #
    #  Normal update (called every frame)
    # ================================================================== #
    def update(self):
        if self.emergency_mode:
            self._update_emergency()
        else:
            self._update_normal()

    # ------------------------------------------------------------------ #
    #  Normal cycling
    # ------------------------------------------------------------------ #
    def _update_normal(self):
        """
        GREEN → YELLOW (current + next-side get-ready)
        YELLOW → current RED, next GREEN
        """
        current_time = time.time()
        elapsed = current_time - self.last_change_time

        current_state = self.signals[self.current_side]
        next_index = (self.current_side_index + 1) % len(self.sides)
        next_side = self.sides[next_index]

        # GREEN → YELLOW  (both current *and* next side turn yellow)
        if current_state == SignalState.GREEN and elapsed >= self.green_duration:
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
    #  Emergency preemption
    # ================================================================== #
    def start_emergency(self, side: str):
        """
        Begin the preemption sequence.
        Phase 1 ("TRANSITION_TO"): set current green side → YELLOW
        and emergency side → YELLOW (get-ready), wait yellow_duration.
        If the emergency side *is* already the green side, just stay green.
        """
        self.emergency_mode = True
        self._emergency_side = side

        # If the emergency side is already green, skip transition
        if self.current_side == side and self.signals[side] == SignalState.GREEN:
            self._emergency_phase = "ACTIVE"
            # ensure only this side is green
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
        """
        Begin winding down the emergency green.
        Phase 3 ("TRANSITION_BACK"): emergency side → YELLOW,
        resume side → YELLOW (get-ready), wait yellow_duration,
        then resume normal cycle.
        """
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
        """State machine for the three emergency phases."""
        current_time = time.time()
        elapsed = current_time - self.last_change_time

        # Phase 1: waiting for yellow before giving emergency green
        if self._emergency_phase == "TRANSITION_TO":
            if elapsed >= self.yellow_duration:
                # All RED, then emergency side GREEN
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
            pass   # EmergencyHandler calls end_emergency() when vehicle passes

        # Phase 3: yellow transition back to normal cycle
        elif self._emergency_phase == "TRANSITION_BACK":
            if elapsed >= self.yellow_duration:
                # Resume normal cycle
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
        """Return seconds since *side* turned green, or -1 if not green."""
        if self.signals.get(side) != SignalState.GREEN:
            return -1
        return time.time() - self.last_change_time

    def get_remaining_time(self):
        """Get remaining time for current state"""
        current_time = time.time()
        elapsed = current_time - self.last_change_time

        current_state = self.signals[self.current_side]
        if current_state == SignalState.GREEN:
            if self.emergency_mode and self._emergency_phase == "ACTIVE":
                return 0   # no countdown during emergency hold
            return max(0, self.green_duration - elapsed)
        elif current_state == SignalState.YELLOW:
            return max(0, self.yellow_duration - elapsed)
        return 0

"""
Vehicle Module — Waypoint-based path movement

Each vehicle follows a pre-computed list of (x, y) waypoints that
define its complete route from spawn → stop-line → intersection → exit.
Bézier curves are used for smooth turns into the correct exit lane.

Lane System (Left-Hand Traffic / India, top-down view):
  NORTH vehicles (heading south ↓): x = center + offset  (right half)
  SOUTH vehicles (heading north ↑): x = center − offset  (left half)
  EAST  vehicles (heading west  ←): y = center + offset  (bottom half)
  WEST  vehicles (heading east  →): y = center − offset  (top half)
"""

import math
import random
import config


class Vehicle:
    """Single vehicle with waypoint-based movement."""

    _used_plates: set = set()

    # ------------------------------------------------------------------ #
    #  License-plate generator (Indian format, eg UP27M1234)
    # ------------------------------------------------------------------ #
    @staticmethod
    def generate_license_plate() -> str:
        while True:
            state = random.choice(config.LICENSE_PLATE_STATES)
            district = random.randint(10, 99)
            letter = random.choice(config.LICENSE_PLATE_LETTERS)
            number = random.randint(1000, 9999)
            plate = f"{state}{district}{letter}{number}"
            if plate not in Vehicle._used_plates:
                Vehicle._used_plates.add(plate)
                return plate

    # ------------------------------------------------------------------ #
    #  Constructor
    # ------------------------------------------------------------------ #
    def __init__(self, original_side: str, vehicle_type: str, queue_position: int = 0):
        self.original_side = original_side
        self.vehicle_type = vehicle_type
        self.vehicle_id = Vehicle.generate_license_plate()

        self.speed = config.VEHICLE_SPEED
        self.crossed = False          # left the screen
        self.stopped = False          # temporarily halted (red / queue)

        # display dimensions
        self.width, self.length = config.VEHICLE_DISPLAY_SIZES.get(
            vehicle_type, (35, 55)
        )

        # turn: 0 = straight, 1 = left, 2 = right
        self.turn_direction = random.choices(
            [0, 1, 2], weights=[60, 20, 20]
        )[0]

        # float position & heading
        self.x = 0.0
        self.y = 0.0
        self.angle = 0.0             # degrees (from atan2)

        # waypoint path
        self.waypoints: list = []
        self.wp_index: int = 0
        self.queue_position = queue_position
        self._path_ready = False

        # side-lane violation behavior (cars/trucks only, very rare)
        self.in_offset_mag = config.LANE_OFFSET
        self.out_offset_mag = config.LANE_OFFSET
        self.in_middle = False
        self.out_middle = False
        self.violation_logged = False
        self._assign_lane_behavior()

    # ------------------------------------------------------------------ #
    #  Path setup  (call once when screen size is known)
    # ------------------------------------------------------------------ #
    def setup_path(self, cx: int, cy: int, screen_w: int, screen_h: int):
        if self._path_ready:
            return
        self._path_ready = True
        self._last_cx = cx
        self._last_cy = cy

        # Spawn just off-screen: use half the relevant screen dimension + buffer
        if self.original_side in ("NORTH", "SOUTH"):
            base_spawn = cy + 60          # off-screen vertically
        else:
            base_spawn = cx + 60          # off-screen horizontally
        spawn_d = base_spawn + self.queue_position * config.MIN_FOLLOWING_DISTANCE
        edge = max(screen_w, screen_h) + 300

        in_off = self._lane_offset(self.original_side, self.in_offset_mag)
        exit_side = self._exit_direction()
        out_off = self._lane_offset(exit_side, self.out_offset_mag)

        self.waypoints = self._build_path(
            cx, cy, in_off, out_off, spawn_d, edge)

        if self.waypoints:
            self.x, self.y = self.waypoints[0]
            self.wp_index = 1
            self._refresh_angle()

    def recompute_path(self, cx: int, cy: int, screen_w: int, screen_h: int):
        """Rebuild waypoints for a new window center, shifting the vehicle position."""
        old_cx = getattr(self, '_last_cx', cx)
        old_cy = getattr(self, '_last_cy', cy)
        if old_cx == cx and old_cy == cy:
            return

        dx_shift = cx - old_cx
        dy_shift = cy - old_cy
        self._last_cx = cx
        self._last_cy = cy

        # Shift current position by the same delta as the center moved
        self.x += dx_shift
        self.y += dy_shift

        # Rebuild waypoints from the new center
        if self.original_side in ("NORTH", "SOUTH"):
            base_spawn = cy + 60
        else:
            base_spawn = cx + 60
        spawn_d = base_spawn + self.queue_position * config.MIN_FOLLOWING_DISTANCE
        edge = max(screen_w, screen_h) + 300

        in_off = self._lane_offset(self.original_side, self.in_offset_mag)
        exit_side = self._exit_direction()
        out_off = self._lane_offset(exit_side, self.out_offset_mag)

        new_waypoints = self._build_path(
            cx, cy, in_off, out_off, spawn_d, edge)

        if new_waypoints and self.wp_index < len(new_waypoints):
            # Keep current progress, update remaining waypoints
            self.waypoints = new_waypoints
        elif new_waypoints:
            self.waypoints = new_waypoints
            self.wp_index = min(self.wp_index, len(new_waypoints) - 1)

        self._refresh_angle()

    # ------------------------------------------------------------------ #
    #  Turn direction helpers
    # ------------------------------------------------------------------ #
    def _exit_direction(self):
        """Return the side-label the vehicle will be 'from' after any turn."""
        if self.turn_direction == 0:
            return self.original_side

        right = {"NORTH": "EAST",  "SOUTH": "WEST",
                 "EAST": "SOUTH", "WEST": "NORTH"}
        left = {"NORTH": "WEST",  "SOUTH": "EAST",
                "EAST": "NORTH", "WEST": "SOUTH"}
        return right[self.original_side] if self.turn_direction == 2 else left[self.original_side]

    # -- quadratic Bézier ---------------------------------------------- #
    @staticmethod
    def _bezier(p0, p1, p2, n=6):
        """n points along a quadratic Bézier (excludes p0)."""
        pts = []
        for i in range(1, n + 1):
            t = i / n
            x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
            y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
            pts.append((x, y))
        return pts

    # ------------------------------------------------------------------ #
    #  Lane behavior helpers (side-line violation)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _lane_offset(side: str, mag: int) -> int:
        """Return signed offset for a side (+ for NORTH/EAST, - for SOUTH/WEST)."""
        return mag if side in ("NORTH", "EAST") else -mag

    def _assign_lane_behavior(self):
        """Assign rare middle-lane behavior for cars/trucks only."""
        if self.vehicle_type not in ("CAR", "TRUCK"):
            return

        if random.random() < config.SIDE_LANE_VIOLATION_RATE:
            pattern = random.choice(
                ("MID_TO_NORMAL", "NORMAL_TO_MID", "MID_TO_MID"))
            if pattern == "MID_TO_NORMAL":
                self.in_offset_mag = 0
                self.out_offset_mag = config.LANE_OFFSET
            elif pattern == "NORMAL_TO_MID":
                self.in_offset_mag = config.LANE_OFFSET
                self.out_offset_mag = 0
            else:  # MID_TO_MID
                self.in_offset_mag = 0
                self.out_offset_mag = 0

        self.in_middle = (self.in_offset_mag == 0)
        self.out_middle = (self.out_offset_mag == 0)

    # ------------------------------------------------------------------ #
    #  Path builder
    # ------------------------------------------------------------------ #
    def _build_path(self, cx, cy, in_off, out_off, spawn_d, edge):
        # spawn positions  (Left-Hand Traffic: keep LEFT from driver POV)
        spawns = {
            "NORTH": (cx + in_off, cy - spawn_d),
            "SOUTH": (cx + in_off, cy + spawn_d),
            "EAST":  (cx + spawn_d, cy + in_off),
            "WEST":  (cx - spawn_d, cy + in_off),
        }
        wp = [spawns[self.original_side]]

        # ---- straight ------------------------------------------------ #
        if self.turn_direction == 0:
            exits = {
                "NORTH": (cx + out_off, cy + edge),
                "SOUTH": (cx + out_off, cy - edge),
                "EAST":  (cx - edge,   cy + out_off),
                "WEST":  (cx + edge,   cy + out_off),
            }
            wp.append(exits[self.original_side])
            return wp

        # ---- right turn (wide turn in LHT) -------------------------- #
        if self.turn_direction == 2:
            curves = {
                "NORTH": ((cx + in_off,      cy + out_off - 15),
                          (cx + in_off,      cy + out_off),
                          (cx + in_off - 15, cy + out_off)),
                "SOUTH": ((cx + in_off,      cy + out_off + 15),
                          (cx + in_off,      cy + out_off),
                          (cx + in_off + 15, cy + out_off)),
                "EAST":  ((cx + out_off + 15, cy + in_off),
                          (cx + out_off,      cy + in_off),
                          (cx + out_off,      cy + in_off - 15)),
                "WEST":  ((cx + out_off - 15, cy + in_off),
                          (cx + out_off,      cy + in_off),
                          (cx + out_off,      cy + in_off + 15)),
            }
            exit_pts = {
                "NORTH": (cx - edge, cy + out_off),
                "SOUTH": (cx + edge, cy + out_off),
                "EAST":  (cx + out_off, cy - edge),
                "WEST":  (cx + out_off, cy + edge),
            }
            p0, p1, p2 = curves[self.original_side]
            wp.extend(self._bezier(p0, p1, p2))
            wp.append(exit_pts[self.original_side])
            return wp

        # ---- left turn (short turn in LHT) -------------------------- #
        curves = {
            "NORTH": ((cx + in_off,       cy + out_off + 15),
                      (cx + in_off,       cy + out_off),
                      (cx + in_off + 15,  cy + out_off)),
            "SOUTH": ((cx + in_off,       cy + out_off - 15),
                      (cx + in_off,       cy + out_off),
                      (cx + in_off - 15,  cy + out_off)),
            "EAST":  ((cx + out_off + 15,  cy + in_off),
                      (cx + out_off,       cy + in_off),
                      (cx + out_off,       cy + in_off + 15)),
            "WEST":  ((cx + out_off - 15,  cy + in_off),
                      (cx + out_off,       cy + in_off),
                      (cx + out_off,       cy + in_off - 15)),
        }
        exit_pts = {
            "NORTH": (cx + edge, cy + out_off),
            "SOUTH": (cx - edge, cy + out_off),
            "EAST":  (cx + out_off,   cy + edge),
            "WEST":  (cx + out_off,   cy - edge),
        }
        p0, p1, p2 = curves[self.original_side]
        wp.extend(self._bezier(p0, p1, p2))
        wp.append(exit_pts[self.original_side])
        return wp

    # ------------------------------------------------------------------ #
    #  Movement
    # ------------------------------------------------------------------ #
    def move(self):
        """Advance one step along the waypoint path."""
        if self.crossed or self.stopped:
            return
        if self.wp_index >= len(self.waypoints):
            self.crossed = True
            return

        tx, ty = self.waypoints[self.wp_index]
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)

        if dist < self.speed * 1.5:
            self.x, self.y = tx, ty
            self.wp_index += 1
            self._refresh_angle()
        else:
            self.x += self.speed * dx / dist
            self.y += self.speed * dy / dist
            self._refresh_angle()

    def _refresh_angle(self):
        if self.wp_index >= len(self.waypoints):
            return
        tx, ty = self.waypoints[self.wp_index]
        dx, dy = tx - self.x, ty - self.y
        if abs(dx) > 0.01 or abs(dy) > 0.01:
            # Keep heading changes continuous using the shortest angular delta.
            # This avoids visual 270-degree spins when crossing ±180 degrees.
            target = math.degrees(math.atan2(dy, dx))
            if not hasattr(self, "_angle_initialized"):
                self.angle = target
                self._angle_initialized = True
            else:
                delta = (target - self.angle + 180) % 360 - 180
                self.angle += delta

    def should_log_violation(self, cx, cy) -> bool:
        """Return True if this vehicle should log a side-lane violation."""
        if self.violation_logged:
            return False
        if self.vehicle_type not in ("CAR", "TRUCK"):
            return False
        if not (self.in_middle or self.out_middle):
            return False
        return self.has_passed_stop_line(cx, cy)

    # ------------------------------------------------------------------ #
    #  Queue / stop-line helpers
    # ------------------------------------------------------------------ #
    def get_distance_from_stop_line(self, cx, cy):
        """Positive → still approaching.  Negative → already past."""
        sl = config.STOP_LINE_OFFSET
        if self.original_side == "NORTH":
            return (cy - sl) - self.y
        elif self.original_side == "SOUTH":
            return self.y - (cy + sl)
        elif self.original_side == "EAST":
            return self.x - (cx + sl)
        elif self.original_side == "WEST":
            return (cx - sl) - self.x
        return 0

    def has_passed_stop_line(self, cx, cy):
        return self.get_distance_from_stop_line(cx, cy) < 0

    def distance_to_vehicle_ahead(self, other):
        """Signed gap to *other* on the same approach lane (positive = ahead)."""
        if self.original_side == "NORTH":
            return other.y - self.y
        elif self.original_side == "SOUTH":
            return self.y - other.y
        elif self.original_side == "EAST":
            return self.x - other.x
        elif self.original_side == "WEST":
            return other.x - self.x
        return 999

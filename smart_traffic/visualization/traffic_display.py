"""
Traffic Display Module
Pygame-based visualisation that renders the intersection, signals,
and vehicles using real photo images from the photo/ folder.
"""

import os
import math
import random
import pygame
import config
from traffic_signal import SignalState


class TrafficDisplay:
    """Fullscreen Pygame display for the traffic simulation."""

    def __init__(self):
        pygame.init()

        self.fullscreen = config.FULLSCREEN
        self._window_size = self._initial_window_size()
        self.screen = self._create_display(self._window_size)

        self.width = self.screen.get_width()
        self.height = self.screen.get_height()
        pygame.display.set_caption("Smart Traffic Signal Simulation")
        self.clock = pygame.time.Clock()

        # fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_vehicle_id = pygame.font.Font(None, 18)

        # ----- load vehicle images ----- #
        # { vehicle_type : [surface, surface, …] }
        self.vehicle_images: dict[str, list[pygame.Surface]] = {}
        # vid → chosen surface
        self._vehicle_image_map: dict[str, pygame.Surface] = {}
        self._load_vehicle_images()

    # ------------------------------------------------------------------ #
    #  Image loading
    # ------------------------------------------------------------------ #
    def _load_vehicle_images(self):
        """Load, scale, and pre-rotate every image so they all face UP."""
        photo_dir = config.PHOTO_DIR
        # Pre-rotation to normalise every sprite to face UP (north)
        dir_to_angle = {"UP": 0, "RIGHT": 90, "DOWN": 180, "LEFT": -90}

        for vtype, filenames in config.VEHICLE_IMAGES.items():
            w, h = config.VEHICLE_DISPLAY_SIZES.get(vtype, (35, 55))
            surfaces = []
            for fname in filenames:
                # Per-file rotation from IMAGE_DIRECTION (keyed by filename)
                pre_rot = dir_to_angle.get(
                    config.IMAGE_DIRECTION.get(fname, "UP"), 0
                )
                path = os.path.join(photo_dir, fname)
                try:
                    img = pygame.image.load(path).convert_alpha()
                    if pre_rot != 0:
                        img = pygame.transform.rotate(img, pre_rot)
                    img = pygame.transform.smoothscale(img, (w, h))
                    surfaces.append(img)
                except Exception:
                    fallback = pygame.Surface((w, h), pygame.SRCALPHA)
                    fallback.fill((120, 120, 120))
                    surfaces.append(fallback)
            self.vehicle_images[vtype] = surfaces if surfaces else [
                pygame.Surface((w, h), pygame.SRCALPHA)
            ]

    def _get_image_for(self, vehicle) -> pygame.Surface:
        """Return the (unrotated) image assigned to *vehicle*."""
        vid = vehicle.vehicle_id
        if vid not in self._vehicle_image_map:
            pool = self.vehicle_images.get(vehicle.vehicle_type, [])
            if pool:
                self._vehicle_image_map[vid] = random.choice(pool)
            else:
                s = pygame.Surface((30, 50), pygame.SRCALPHA)
                s.fill((120, 120, 120))
                self._vehicle_image_map[vid] = s
        return self._vehicle_image_map[vid]

    # ------------------------------------------------------------------ #
    #  Fullscreen toggle
    # ------------------------------------------------------------------ #
    def _initial_window_size(self):
        info = pygame.display.Info()
        default_w = getattr(config, "WINDOW_WIDTH", info.current_w - 100)
        default_h = getattr(config, "WINDOW_HEIGHT", info.current_h - 100)
        min_w = getattr(config, "MIN_WINDOW_WIDTH", 900)
        min_h = getattr(config, "MIN_WINDOW_HEIGHT", 650)

        width = max(min_w, min(int(default_w),
                    max(min_w, info.current_w - 40)))
        height = max(min_h, min(int(default_h),
                     max(min_h, info.current_h - 80)))
        return (width, height)

    def _create_display(self, size):
        if self.fullscreen:
            return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

        flags = pygame.RESIZABLE if getattr(
            config, "RESIZABLE_WINDOW", True) else 0
        return pygame.display.set_mode(size, flags)

    def _apply_window_resize(self, width, height):
        min_w = getattr(config, "MIN_WINDOW_WIDTH", 900)
        min_h = getattr(config, "MIN_WINDOW_HEIGHT", 650)
        safe_size = (max(min_w, int(width)), max(min_h, int(height)))
        self._window_size = safe_size
        self.screen = self._create_display(safe_size)
        self.width, self.height = self.screen.get_size()
        self._update_fonts()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.screen = self._create_display(self._window_size)
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()
        self._update_fonts()

    def _update_fonts(self):
        """Recalculate font sizes based on current window dimensions."""
        scale = min(self.width / 1400, self.height / 850)
        scale = max(0.6, min(scale, 1.5))
        self.font_large = pygame.font.Font(None, max(24, int(48 * scale)))
        self.font_medium = pygame.font.Font(None, max(18, int(32 * scale)))
        self.font_small = pygame.font.Font(None, max(14, int(24 * scale)))
        self.font_vehicle_id = pygame.font.Font(None, max(12, int(18 * scale)))

    # ------------------------------------------------------------------ #
    #  Main draw entry point
    # ------------------------------------------------------------------ #
    def draw(self, intersection):
        intersection.set_window_size(self.width, self.height)
        self.screen.fill(config.COLOR_BACKGROUND)

        self._draw_nature_decor()
        self._draw_roads()
        self._draw_lane_direction_labels()
        self._draw_signals(intersection.signal_controller)
        self._draw_vehicles(intersection.get_all_vehicles())
        self._draw_title()
        self._draw_statistics(intersection)
        self._draw_controls()
        self._draw_emergency_indicator(intersection)

        pygame.display.flip()
        self.clock.tick(config.FPS)

    # ------------------------------------------------------------------ #
    #  Title
    # ------------------------------------------------------------------ #
    def _draw_title(self):
        # Keep title in top-left corner to avoid road overlap.
        title = self.font_large.render(
            "Smart Traffic Signal Simulation", True, config.COLOR_TEXT
        )
        bg = pygame.Surface((title.get_width() + 24, title.get_height() + 14), pygame.SRCALPHA)
        bg.fill((10, 15, 25, 180))
        x, y = 18, 16
        self.screen.blit(bg, (x - 10, y - 6))
        self.screen.blit(title, (x, y))

    # ------------------------------------------------------------------ #
    #  Environment decor
    # ------------------------------------------------------------------ #
    def _draw_nature_decor(self):
        """Draw subtle natural elements (trees/grass) in safe corner zones."""
        cx, cy = self.width // 2, self.height // 2
        rw2 = config.ROAD_WIDTH // 2

        # Corner grass pads (stay outside road corridors)
        pads = [
            pygame.Rect(10, 10, max(120, cx - rw2 - 30), max(90, cy - rw2 - 30)),
            pygame.Rect(cx + rw2 + 20, 10, max(120, self.width - (cx + rw2 + 30)), max(90, cy - rw2 - 30)),
            pygame.Rect(10, cy + rw2 + 20, max(120, cx - rw2 - 30), max(90, self.height - (cy + rw2 + 30))),
            pygame.Rect(cx + rw2 + 20, cy + rw2 + 20, max(120, self.width - (cx + rw2 + 30)), max(90, self.height - (cy + rw2 + 30))),
        ]
        for r in pads:
            if r.width > 30 and r.height > 30:
                pygame.draw.rect(self.screen, (42, 68, 52), r, border_radius=18)

        # Simple tree icons in corners
        trees = [
            (40, 70), (120, 55),
            (self.width - 45, 70), (self.width - 120, 52),
            (48, self.height - 95), (130, self.height - 75),
            (self.width - 48, self.height - 95), (self.width - 130, self.height - 78),
        ]
        for tx, ty in trees:
            self._draw_tree(tx, ty)

    def _draw_tree(self, x, y):
        trunk = pygame.Rect(x - 4, y + 10, 8, 16)
        pygame.draw.rect(self.screen, (110, 78, 40), trunk, border_radius=2)
        pygame.draw.circle(self.screen, (55, 130, 70), (x, y), 14)
        pygame.draw.circle(self.screen, (70, 150, 85), (x - 8, y + 2), 10)
        pygame.draw.circle(self.screen, (70, 150, 85), (x + 8, y + 1), 9)

    # ------------------------------------------------------------------ #
    #  Roads & markings
    # ------------------------------------------------------------------ #
    def _draw_roads(self):
        cx = self.width // 2
        cy = self.height // 2
        # Keep road geometry fixed to simulation coordinates so vehicle
        # lanes, stop-lines, and signal logic stay perfectly aligned
        # across fullscreen and windowed modes.
        rw = config.ROAD_WIDTH

        # vertical road
        pygame.draw.rect(self.screen, config.COLOR_ROAD,
                         (cx - rw // 2, 0, rw, self.height))
        # horizontal road
        pygame.draw.rect(self.screen, config.COLOR_ROAD,
                         (0, cy - rw // 2, self.width, rw))

        self._draw_road_edge_highlights(cx, cy, rw)
        self._draw_road_markings(cx, cy, rw)
        self._draw_zebra_crossings(cx, cy, rw)
        self._draw_lane_arrows(cx, cy)

    def _draw_road_edge_highlights(self, cx, cy, rw):
        """Add subtle edge lines so roads look cleaner and more realistic."""
        edge = (110, 110, 110)
        shadow = (45, 45, 45)
        # vertical road edges
        pygame.draw.line(self.screen, edge, (cx - rw // 2, 0),
                         (cx - rw // 2, self.height), 2)
        pygame.draw.line(self.screen, edge, (cx + rw // 2, 0),
                         (cx + rw // 2, self.height), 2)
        pygame.draw.line(self.screen, shadow, (cx - rw // 2 + 3, 0),
                         (cx - rw // 2 + 3, self.height), 1)
        pygame.draw.line(self.screen, shadow, (cx + rw // 2 - 3, 0),
                         (cx + rw // 2 - 3, self.height), 1)

        # horizontal road edges
        pygame.draw.line(self.screen, edge, (0, cy - rw // 2),
                         (self.width, cy - rw // 2), 2)
        pygame.draw.line(self.screen, edge, (0, cy + rw // 2),
                         (self.width, cy + rw // 2), 2)
        pygame.draw.line(self.screen, shadow, (0, cy - rw // 2 + 3),
                         (self.width, cy - rw // 2 + 3), 1)
        pygame.draw.line(self.screen, shadow, (0, cy + rw // 2 - 3),
                         (self.width, cy + rw // 2 - 3), 1)

    def _draw_road_markings(self, cx, cy, rw):
        dash, gap, lw = 30, 20, 4

        # vertical centre dashes
        for y in range(0, self.height, dash + gap):
            if y < cy - rw // 2 or y > cy + rw // 2:
                pygame.draw.line(self.screen, config.COLOR_ROAD_LINE,
                                 (cx, y), (cx, min(y + dash, self.height)), lw)

        # horizontal centre dashes
        for x in range(0, self.width, dash + gap):
            if x < cx - rw // 2 or x > cx + rw // 2:
                pygame.draw.line(self.screen, config.COLOR_ROAD_LINE,
                                 (x, cy), (min(x + dash, self.width), cy), lw)

        # stop lines (yellow)
        sl = config.STOP_LINE_OFFSET
        slw = 8
        half = rw // 2 - 10

        # north stop line (right half of vertical road — LHT)
        pygame.draw.line(self.screen, config.COLOR_ROAD_MARKING,
                         (cx, cy - sl), (cx + half, cy - sl), slw)
        # south stop line (left half — LHT)
        pygame.draw.line(self.screen, config.COLOR_ROAD_MARKING,
                         (cx - half, cy + sl), (cx, cy + sl), slw)
        # east stop line (bottom half of horizontal road — LHT)
        pygame.draw.line(self.screen, config.COLOR_ROAD_MARKING,
                         (cx + sl, cy), (cx + sl, cy + half), slw)
        # west stop line (top half — LHT)
        pygame.draw.line(self.screen, config.COLOR_ROAD_MARKING,
                         (cx - sl, cy - half), (cx - sl, cy), slw)

    def _draw_zebra_crossings(self, cx, cy, rw):
        """Draw zebra crossings near stop-lines on all approaches."""
        sl = config.STOP_LINE_OFFSET
        stripe = (245, 245, 245)

        stripe_w = 9
        stripe_h = 24
        gap = 8
        count = 8

        # North and south crossings (horizontal stripes)
        start_x = cx - (count * (stripe_w + gap)) // 2
        y_north = cy - sl + 14
        y_south = cy + sl - 14 - stripe_h
        for i in range(count):
            x = start_x + i * (stripe_w + gap)
            pygame.draw.rect(self.screen, stripe,
                             (x, y_north, stripe_w, stripe_h), border_radius=2)
            pygame.draw.rect(self.screen, stripe,
                             (x, y_south, stripe_w, stripe_h), border_radius=2)

        # East and west crossings (vertical stripes)
        start_y = cy - (count * (stripe_w + gap)) // 2
        x_east = cx + sl - 14 - stripe_h
        x_west = cx - sl + 14
        for i in range(count):
            y = start_y + i * (stripe_w + gap)
            pygame.draw.rect(self.screen, stripe,
                             (x_east, y, stripe_h, stripe_w), border_radius=2)
            pygame.draw.rect(self.screen, stripe,
                             (x_west, y, stripe_h, stripe_w), border_radius=2)

    def _draw_lane_arrows(self, cx, cy):
        """Draw directional arrows on incoming lanes."""
        sl = config.STOP_LINE_OFFSET
        lo = config.LANE_OFFSET
        color = (230, 230, 230)

        # Incoming lane centers for LHT
        self._draw_arrow((cx + lo, cy - sl - 48), "DOWN", color)   # NORTH lane
        self._draw_arrow((cx - lo, cy + sl + 48), "UP", color)     # SOUTH lane
        self._draw_arrow((cx + sl + 48, cy + lo), "LEFT", color)   # EAST lane
        self._draw_arrow((cx - sl - 48, cy - lo), "RIGHT", color)  # WEST lane

    def _draw_arrow(self, center, direction, color):
        """Draw a simple filled lane arrow."""
        x, y = center
        shaft_w, shaft_h = 8, 24
        head = 10

        if direction == "UP":
            pygame.draw.rect(self.screen, color,
                             (x - shaft_w // 2, y - shaft_h // 2, shaft_w, shaft_h))
            pts = [(x, y - shaft_h // 2 - head),
                   (x - head, y - shaft_h // 2 + 2),
                   (x + head, y - shaft_h // 2 + 2)]
        elif direction == "DOWN":
            pygame.draw.rect(self.screen, color,
                             (x - shaft_w // 2, y - shaft_h // 2, shaft_w, shaft_h))
            pts = [(x, y + shaft_h // 2 + head),
                   (x - head, y + shaft_h // 2 - 2),
                   (x + head, y + shaft_h // 2 - 2)]
        elif direction == "LEFT":
            pygame.draw.rect(self.screen, color,
                             (x - shaft_h // 2, y - shaft_w // 2, shaft_h, shaft_w))
            pts = [(x - shaft_h // 2 - head, y),
                   (x - shaft_h // 2 + 2, y - head),
                   (x - shaft_h // 2 + 2, y + head)]
        else:  # RIGHT
            pygame.draw.rect(self.screen, color,
                             (x - shaft_h // 2, y - shaft_w // 2, shaft_h, shaft_w))
            pts = [(x + shaft_h // 2 + head, y),
                   (x + shaft_h // 2 - 2, y - head),
                   (x + shaft_h // 2 - 2, y + head)]

        pygame.draw.polygon(self.screen, color, pts)

    # ------------------------------------------------------------------ #
    #  Traffic signals
    # ------------------------------------------------------------------ #
    def _draw_signals(self, sc):
        cx = self.width // 2
        cy = self.height // 2
        off = 120

        # Signals near the stop lines (same side as the approaching lane)
        positions = {
            "NORTH": (cx + 50, cy - off),
            "SOUTH": (cx - 50, cy + off),
            "EAST":  (cx + off, cy + 50),
            "WEST":  (cx - off, cy - 50),
        }
        # Timer placed outside the road so it never overlaps vehicles
        rw2 = config.ROAD_WIDTH // 2
        timer_positions = {
            "NORTH": (cx + rw2 + 40, cy - off),
            "SOUTH": (cx - rw2 - 40, cy + off),
            "EAST":  (cx + off, cy + rw2 + 40),
            "WEST":  (cx - off, cy - rw2 - 40),
        }

        for side, pos in positions.items():
            state = sc.get_signal_state(side)
            if state == SignalState.RED:
                color = config.COLOR_SIGNAL_RED
            elif state == SignalState.YELLOW:
                color = config.COLOR_SIGNAL_YELLOW
            else:
                color = config.COLOR_SIGNAL_GREEN

            # background box
            bg = pygame.Rect(pos[0] - 25, pos[1] - 40, 50, 80)
            pygame.draw.rect(self.screen, (0, 0, 0), bg, border_radius=10)

            # light
            pygame.draw.circle(self.screen, color, pos, config.SIGNAL_SIZE)
            pygame.draw.circle(self.screen, (255, 255, 255), pos,
                               config.SIGNAL_SIZE, 3)

            # countdown timer (outside the road, never overlaps vehicles)
            remaining = sc.get_remaining_time()
            # Normal cycle: show timer for active side and next-side yellow.
            # Emergency transition: show timer for any side that is yellow.
            next_idx = (sc.current_side_index + 1) % len(sc.sides)
            next_side = sc.sides[next_idx]
            if sc.emergency_mode and state == SignalState.YELLOW:
                show_timer = True
            else:
                show_timer = (sc.current_side == side or
                              (next_side == side
                               and state == SignalState.YELLOW
                               and sc.get_signal_state(sc.current_side) == SignalState.YELLOW))
            if show_timer and remaining > 0:
                tp = timer_positions[side]
                txt = self.font_medium.render(f"{int(remaining)}s", True,
                                              config.COLOR_TEXT)
                self.screen.blit(txt, (tp[0] - txt.get_width() // 2,
                                       tp[1] - txt.get_height() // 2))

    def _draw_lane_direction_labels(self):
        """Draw NORTH/SOUTH/EAST/WEST around the center square (one per side)."""
        cx = self.width // 2
        cy = self.height // 2
        # Use a virtual square around the intersection center and place
        # one direction name on each side, well away from zebra crossings.
        pad = config.ROAD_WIDTH // 2 + 42

        text_color = (238, 242, 248)
        bg_color = (10, 15, 25, 170)

        labels = [
            ("NORTH", (cx, cy - pad), 0),
            ("SOUTH", (cx, cy + pad), 0),
            ("EAST",  (cx + pad, cy), 0),
            ("WEST",  (cx - pad, cy), 0),
        ]

        for text, (lx, ly), angle in labels:
            surf = self.font_small.render(text, True, text_color)
            if angle != 0:
                surf = pygame.transform.rotate(surf, angle)

            rect = surf.get_rect(center=(lx, ly))
            bg = pygame.Surface((rect.width + 10, rect.height + 6), pygame.SRCALPHA)
            bg.fill(bg_color)
            self.screen.blit(bg, (rect.x - 5, rect.y - 3))
            self.screen.blit(surf, rect)

    # ------------------------------------------------------------------ #
    #  Vehicles (photo images + license plates)
    # ------------------------------------------------------------------ #
    def _draw_vehicles(self, vehicles):
        for v in vehicles:
            self._draw_single_vehicle(v)

    def _draw_single_vehicle(self, v):
        base_img = self._get_image_for(v)

        # --- rotation ---
        # vehicle.angle is atan2 (0°=east, 90°=south, -90°=north, 180°=west)
        # If image faces UP (north), rotation formula:
        if config.IMAGE_FACES == "UP":
            rot_deg = -v.angle - 90
        else:  # image faces RIGHT (east)
            rot_deg = -v.angle

        rotated = pygame.transform.rotate(base_img, rot_deg)
        rect = rotated.get_rect(center=(int(v.x), int(v.y)))
        self.screen.blit(rotated, rect)

        # --- tiny license plate label --- #
        plate = self.font_vehicle_id.render(v.vehicle_id, True, (0, 0, 0))
        pw, ph = plate.get_size()
        bg = pygame.Surface((pw + 4, ph + 2), pygame.SRCALPHA)
        bg.fill((255, 255, 200, 210))
        # position the plate just below the vehicle image
        px = int(v.x) - (pw + 4) // 2
        py = rect.bottom + 1
        self.screen.blit(bg, (px, py))
        self.screen.blit(plate, (px + 2, py + 1))

    # ------------------------------------------------------------------ #
    #  Statistics panel
    # ------------------------------------------------------------------ #
    def _draw_statistics(self, intersection):
        # Compact card in top-left corner to avoid center-road overlap.
        px, py = 18, 76
        pw, ph = 350, 210
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((20, 20, 20, 185))
        self.screen.blit(panel, (px, py))

        y = py + 12
        t = self.font_medium.render("Statistics", True, config.COLOR_TEXT)
        self.screen.blit(t, (px + 15, y))
        y += 34

        self.screen.blit(
            self.font_small.render("Vehicles Waiting:",
                                   True, config.COLOR_TEXT),
            (px + 15, y)
        )
        y += 24

        for side in ("NORTH", "SOUTH", "EAST", "WEST"):
            cnt = intersection.get_vehicle_count(side)
            state = intersection.signal_controller.get_signal_state(side)
            if state == SignalState.GREEN:
                c = config.COLOR_SIGNAL_GREEN
            elif state == SignalState.YELLOW:
                c = config.COLOR_SIGNAL_YELLOW
            else:
                c = config.COLOR_SIGNAL_RED
            lbl = self.font_small.render(f"  {side}: {cnt}", True, c)
            self.screen.blit(lbl, (px + 20, y))
            y += 21

        y += 8
        total = intersection.get_total_vehicle_count()
        self.screen.blit(
            self.font_small.render(
                f"Total Active: {total}", True, config.COLOR_TEXT),
            (px + 15, y)
        )
        y += 24

        crossed = intersection.total_vehicles_crossed
        self.screen.blit(
            self.font_small.render(f"Vehicles Crossed: {crossed}", True,
                                   config.COLOR_TEXT),
            (px + 15, y)
        )
        y += 22

        c = intersection.vehicles_crossed_by_type.get("CAR", 0)
        tcnt = intersection.vehicles_crossed_by_type.get("TRUCK", 0)
        a = intersection.vehicles_crossed_by_type.get("AMBULANCE", 0)
        compact = self.font_small.render(
            f"C:{c}  T:{tcnt}  A:{a}", True, (180, 220, 255)
        )
        self.screen.blit(compact, (px + 15, y))

    # ------------------------------------------------------------------ #
    #  Controls footer
    # ------------------------------------------------------------------ #
    def _draw_controls(self):
        txt = "ESC/Q: Exit  |  F: Fullscreen  |  Drag edges to resize"
        lbl = self.font_small.render(txt, True, config.COLOR_TEXT)
        # Bottom-right corner placement to keep roads clear.
        x = self.width - lbl.get_width() - 18
        y = self.height - lbl.get_height() - 14
        bg = pygame.Surface((lbl.get_width() + 14, lbl.get_height() + 8), pygame.SRCALPHA)
        bg.fill((10, 15, 25, 160))
        self.screen.blit(bg, (x - 7, y - 4))
        self.screen.blit(lbl, (x, y))

    # ------------------------------------------------------------------ #
    #  Emergency indicator
    # ------------------------------------------------------------------ #
    def _draw_emergency_indicator(self, intersection):
        """Show a flashing EMERGENCY banner in the top-right corner."""
        eh = intersection.emergency_handler
        if not eh.active:
            return

        # Flashing effect (toggle every ~0.4 sec)
        import time
        show = int(time.time() * 2.5) % 2 == 0
        if not show:
            return

        banner_w, banner_h = 420, 45
        bx = self.width - banner_w - 20   # 20 px margin from right edge
        by = 20                            # top margin
        bg = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
        bg.fill((200, 0, 0, 220))
        self.screen.blit(bg, (bx, by))

        side = eh.emergency_side or "?"
        txt = self.font_medium.render(
            f"EMERGENCY  —  Ambulance on {side}", True, (255, 255, 255)
        )
        self.screen.blit(txt, (bx + banner_w // 2 - txt.get_width() // 2,
                               by + banner_h // 2 - txt.get_height() // 2))

        # Show queued count if more than one waiting
        qlen = len(eh._queue)
        if qlen > 0:
            q_txt = self.font_small.render(
                f"+{qlen} more in queue", True, (255, 200, 200)
            )
            self.screen.blit(q_txt, (bx + banner_w // 2 - q_txt.get_width() // 2,
                                     by + banner_h + 4))

    # ------------------------------------------------------------------ #
    #  Events
    # ------------------------------------------------------------------ #
    def check_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.VIDEORESIZE and not self.fullscreen:
                self._apply_window_resize(event.w, event.h)
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return True
                if event.key == pygame.K_f:
                    self.toggle_fullscreen()
        return False

    def cleanup(self):
        pygame.quit()

"""
Traffic Display Module
Uses Pygame to visualize the traffic simulation in fullscreen
"""

import pygame
import config
from traffic_signal import SignalState

class TrafficDisplay:
    """
    Displays the intersection, signals, and vehicles using Pygame
    """
    
    def __init__(self):
        """Initialize Pygame display"""
        pygame.init()
        
        # Get desktop resolution and create fullscreen window
        if config.FULLSCREEN:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            # Windowed mode
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w - 100, info.current_h - 100))
        
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()
        
        pygame.display.set_caption("Smart Traffic Signal Simulation")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_vehicle_id = pygame.font.Font(None, 20)
        
        self.fullscreen = config.FULLSCREEN
    
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w - 100, info.current_h - 100))
        
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()
    
    def draw(self, intersection):
        """
        Draw the entire scene
        
        Args:
            intersection (Intersection): The intersection to draw
        """
        # Update intersection window size
        intersection.set_window_size(self.width, self.height)
        
        # Clear screen
        self.screen.fill(config.COLOR_BACKGROUND)
        
        # Draw title
        self._draw_title()
        
        # Draw roads
        self._draw_roads()
        
        # Draw traffic signals
        self._draw_signals(intersection.signal_controller)
        
        # Draw vehicles with IDs
        self._draw_vehicles(intersection.get_all_vehicles())
        
        # Draw statistics
        self._draw_statistics(intersection)
        
        # Draw controls help
        self._draw_controls()
        
        # Update display
        pygame.display.flip()
        self.clock.tick(config.FPS)
    
    def _draw_title(self):
        """Draw title at top of screen"""
        title = self.font_large.render("Smart Traffic Signal Simulation", True, config.COLOR_TEXT)
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 20))
    
    def _draw_roads(self):
        """Draw the intersection roads"""
        center_x = self.width // 2
        center_y = self.height // 2
        road_width = config.ROAD_WIDTH
        
        # Vertical road
        pygame.draw.rect(
            self.screen, 
            config.COLOR_ROAD,
            (center_x - road_width//2, 0, road_width, self.height)
        )
        
        # Horizontal road
        pygame.draw.rect(
            self.screen,
            config.COLOR_ROAD,
            (0, center_y - road_width//2, self.width, road_width)
        )
        
        # Draw center lines and stop lines
        self._draw_road_markings(center_x, center_y, road_width)
    
    def _draw_road_markings(self, center_x, center_y, road_width):
        """Draw road markings, center lines, and stop lines"""
        line_width = 4
        dash_length = 30
        dash_gap = 20
        
        # Vertical center line (dashed)
        for y in range(0, self.height, dash_length + dash_gap):
            if y < center_y - road_width//2 or y > center_y + road_width//2:
                pygame.draw.line(
                    self.screen,
                    config.COLOR_ROAD_LINE,
                    (center_x, y),
                    (center_x, min(y + dash_length, self.height)),
                    line_width
                )
        
        # Horizontal center line (dashed)
        for x in range(0, self.width, dash_length + dash_gap):
            if x < center_x - road_width//2 or x > center_x + road_width//2:
                pygame.draw.line(
                    self.screen,
                    config.COLOR_ROAD_LINE,
                    (x, center_y),
                    (min(x + dash_length, self.width), center_y),
                    line_width
                )
        
        # Stop lines (yellow thick lines)
        stop_offset = 150
        stop_line_width = 8
        
        # North stop line
        pygame.draw.line(
            self.screen, config.COLOR_ROAD_MARKING,
            (center_x - road_width//2 + 10, center_y - stop_offset),
            (center_x, center_y - stop_offset),
            stop_line_width
        )
        
        # South stop line
        pygame.draw.line(
            self.screen, config.COLOR_ROAD_MARKING,
            (center_x, center_y + stop_offset),
            (center_x + road_width//2 - 10, center_y + stop_offset),
            stop_line_width
        )
        
        # East stop line
        pygame.draw.line(
            self.screen, config.COLOR_ROAD_MARKING,
            (center_x + stop_offset, center_y),
            (center_x + stop_offset, center_y + road_width//2 - 10),
            stop_line_width
        )
        
        # West stop line
        pygame.draw.line(
            self.screen, config.COLOR_ROAD_MARKING,
            (center_x - stop_offset, center_y - road_width//2 + 10),
            (center_x - stop_offset, center_y),
            stop_line_width
        )
    
    def _draw_signals(self, signal_controller):
        """Draw traffic signals for each side"""
        center_x = self.width // 2
        center_y = self.height // 2
        offset = 120
        
        signal_positions = {
            "NORTH": (center_x - 50, center_y - offset),
            "SOUTH": (center_x + 50, center_y + offset),
            "EAST": (center_x + offset, center_y + 50),
            "WEST": (center_x - offset, center_y - 50)
        }
        
        for side, pos in signal_positions.items():
            state = signal_controller.get_signal_state(side)
            
            # Choose color based on state
            if state == SignalState.RED:
                color = config.COLOR_SIGNAL_RED
            elif state == SignalState.YELLOW:
                color = config.COLOR_SIGNAL_YELLOW
            else:  # GREEN
                color = config.COLOR_SIGNAL_GREEN
            
            # Draw signal background (black box)
            signal_rect = pygame.Rect(pos[0] - 25, pos[1] - 40, 50, 80)
            pygame.draw.rect(self.screen, (0, 0, 0), signal_rect, border_radius=10)
            
            # Draw signal light
            pygame.draw.circle(self.screen, color, pos, config.SIGNAL_SIZE)
            pygame.draw.circle(self.screen, (255, 255, 255), pos, config.SIGNAL_SIZE, 3)
            
            # Draw side label
            label = self.font_small.render(side, True, config.COLOR_TEXT)
            label_pos = (pos[0] - label.get_width()//2, pos[1] - 65)
            self.screen.blit(label, label_pos)
            
            # Draw countdown timer
            remaining_time = signal_controller.get_remaining_time()
            if signal_controller.current_side == side and remaining_time > 0:
                timer_text = f"{int(remaining_time)}s"
                timer = self.font_small.render(timer_text, True, config.COLOR_TEXT)
                timer_pos = (pos[0] - timer.get_width()//2, pos[1] + 50)
                self.screen.blit(timer, timer_pos)
    
    def _draw_vehicles(self, vehicles):
        """Draw all vehicles with realistic appearance and license plates"""
        for vehicle in vehicles:
            self._draw_single_vehicle(vehicle)
    
    def _draw_single_vehicle(self, vehicle):
        """Draw a single vehicle with realistic details"""
        # Determine orientation
        is_vertical = vehicle.side in ["NORTH", "SOUTH"]
        
        if is_vertical:
            w, h = vehicle.width, vehicle.height
            x = vehicle.x - w//2
            y = vehicle.y - h//2
        else:
            # Swap dimensions for horizontal vehicles
            w, h = vehicle.height, vehicle.width
            x = vehicle.x - w//2
            y = vehicle.y - h//2
        
        # Draw based on vehicle type
        if vehicle.vehicle_type == "CAR":
            self._draw_car(x, y, w, h, vehicle.color, is_vertical)
        elif vehicle.vehicle_type == "TRUCK":
            self._draw_truck(x, y, w, h, vehicle.color, is_vertical)
        elif vehicle.vehicle_type == "BUS":
            self._draw_bus(x, y, w, h, vehicle.color, is_vertical)
        
        # Draw license plate
        self._draw_license_plate(vehicle, x, y, w, h, is_vertical)
    
    def _draw_car(self, x, y, w, h, color, is_vertical):
        """Draw a car with realistic details"""
        # Main body
        body_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, color, body_rect, border_radius=4)
        pygame.draw.rect(self.screen, (0, 0, 0), body_rect, 2, border_radius=4)
        
        # Windows (darker shade)
        window_color = tuple(max(0, c - 80) for c in color)
        if is_vertical:
            # Front and rear windows
            front_window = pygame.Rect(x + 3, y + 3, w - 6, h//3 - 3)
            rear_window = pygame.Rect(x + 3, y + 2*h//3, w - 6, h//3 - 3)
        else:
            # Side windows
            front_window = pygame.Rect(x + 3, y + 3, w//3 - 3, h - 6)
            rear_window = pygame.Rect(x + 2*w//3, y + 3, w//3 - 3, h - 6)
        
        pygame.draw.rect(self.screen, window_color, front_window, border_radius=2)
        pygame.draw.rect(self.screen, window_color, rear_window, border_radius=2)
        
        # Wheels (small black circles)
        wheel_radius = 3
        if is_vertical:
            wheel1 = (x + w//4, y + h - 5)
            wheel2 = (x + 3*w//4, y + h - 5)
            wheel3 = (x + w//4, y + 5)
            wheel4 = (x + 3*w//4, y + 5)
        else:
            wheel1 = (x + 5, y + h//4)
            wheel2 = (x + 5, y + 3*h//4)
            wheel3 = (x + w - 5, y + h//4)
            wheel4 = (x + w - 5, y + 3*h//4)
        
        for wheel_pos in [wheel1, wheel2, wheel3, wheel4]:
            pygame.draw.circle(self.screen, (30, 30, 30), wheel_pos, wheel_radius)
    
    def _draw_truck(self, x, y, w, h, color, is_vertical):
        """Draw a truck with cargo area"""
        # Cargo area (rear)
        cargo_color = tuple(max(0, c - 40) for c in color)
        if is_vertical:
            cargo_rect = pygame.Rect(x, y + h//2, w, h//2)
            cab_rect = pygame.Rect(x, y, w, h//2)
        else:
            cargo_rect = pygame.Rect(x + w//2, y, w//2, h)
            cab_rect = pygame.Rect(x, y, w//2, h)
        
        pygame.draw.rect(self.screen, cargo_color, cargo_rect, border_radius=3)
        pygame.draw.rect(self.screen, (0, 0, 0), cargo_rect, 2, border_radius=3)
        
        # Cab (front)
        pygame.draw.rect(self.screen, color, cab_rect, border_radius=3)
        pygame.draw.rect(self.screen, (0, 0, 0), cab_rect, 2, border_radius=3)
        
        # Windows
        window_color = tuple(max(0, c - 80) for c in color)
        if is_vertical:
            window = pygame.Rect(x + 4, y + 4, w - 8, h//4)
        else:
            window = pygame.Rect(x + 4, y + 4, w//4, h - 8)
        pygame.draw.rect(self.screen, window_color, window, border_radius=2)
        
        # Larger wheels
        wheel_radius = 4
        if is_vertical:
            wheels = [(x + w//4, y + h - 6), (x + 3*w//4, y + h - 6),
                     (x + w//4, y + h//2 - 6), (x + 3*w//4, y + h//2 - 6)]
        else:
            wheels = [(x + 6, y + h//4), (x + 6, y + 3*h//4),
                     (x + w//2 + 6, y + h//4), (x + w//2 + 6, y + 3*h//4)]
        
        for wheel_pos in wheels:
            pygame.draw.circle(self.screen, (30, 30, 30), wheel_pos, wheel_radius)
    
    def _draw_bus(self, x, y, w, h, color, is_vertical):
        """Draw a bus with multiple windows"""
        # Main body
        body_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, color, body_rect, border_radius=4)
        pygame.draw.rect(self.screen, (0, 0, 0), body_rect, 2, border_radius=4)
        
        # Multiple windows
        window_color = tuple(max(0, c - 80) for c in color)
        num_windows = 4
        
        if is_vertical:
            window_h = (h - 10) // num_windows
            for i in range(num_windows):
                window = pygame.Rect(x + 4, y + 5 + i * window_h, w - 8, window_h - 5)
                pygame.draw.rect(self.screen, window_color, window, border_radius=1)
        else:
            window_w = (w - 10) // num_windows
            for i in range(num_windows):
                window = pygame.Rect(x + 5 + i * window_w, y + 4, window_w - 5, h - 8)
                pygame.draw.rect(self.screen, window_color, window, border_radius=1)
        
        # Wheels
        wheel_radius = 4
        if is_vertical:
            wheels = [(x + w//4, y + h - 6), (x + 3*w//4, y + h - 6),
                     (x + w//4, y + 6), (x + 3*w//4, y + 6)]
        else:
            wheels = [(x + 6, y + h//4), (x + 6, y + 3*h//4),
                     (x + w - 6, y + h//4), (x + w - 6, y + 3*h//4)]
        
        for wheel_pos in wheels:
            pygame.draw.circle(self.screen, (30, 30, 30), wheel_pos, wheel_radius)
    
    def _draw_license_plate(self, vehicle, x, y, w, h, is_vertical):
        """Draw license plate on vehicle"""
        plate_text = vehicle.vehicle_id
        
        # Create license plate surface
        plate_font = pygame.font.Font(None, 14)
        text_surface = plate_font.render(plate_text, True, (0, 0, 0))
        
        # License plate background (white/yellow)
        plate_bg_color = (255, 255, 200)
        padding = 2
        plate_w = text_surface.get_width() + padding * 2
        plate_h = text_surface.get_height() + padding * 2
        
        # Position license plate
        if is_vertical:
            # Put at bottom of vehicle
            plate_x = x + w//2 - plate_w//2
            plate_y = y + h - plate_h - 2
        else:
            # Put at end of vehicle
            plate_x = x + w - plate_w - 2
            plate_y = y + h//2 - plate_h//2
        
        # Draw plate background
        plate_rect = pygame.Rect(plate_x, plate_y, plate_w, plate_h)
        pygame.draw.rect(self.screen, plate_bg_color, plate_rect, border_radius=2)
        pygame.draw.rect(self.screen, (0, 0, 0), plate_rect, 1, border_radius=2)
        
        # Draw text
        self.screen.blit(text_surface, (plate_x + padding, plate_y + padding))
    
    def _draw_statistics(self, intersection):
        """Draw comprehensive statistics panel"""
        panel_x = 20
        panel_y = 100
        
        # Semi-transparent background panel
        panel_width = 350
        panel_height = 400
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.set_alpha(200)
        panel_surface.fill((20, 20, 20))
        self.screen.blit(panel_surface, (panel_x, panel_y))
        
        y_offset = panel_y + 15
        
        # Title
        title = self.font_medium.render("Statistics", True, config.COLOR_TEXT)
        self.screen.blit(title, (panel_x + 15, y_offset))
        y_offset += 45
        
        # Current vehicles by side
        side_title = self.font_small.render("Vehicles Waiting:", True, config.COLOR_TEXT)
        self.screen.blit(side_title, (panel_x + 15, y_offset))
        y_offset += 30
        
        for side in ["NORTH", "SOUTH", "EAST", "WEST"]:
            count = intersection.get_vehicle_count(side)
            signal_state = intersection.signal_controller.get_signal_state(side)
            
            # Color code by signal state
            if signal_state == SignalState.GREEN:
                color = config.COLOR_SIGNAL_GREEN
            elif signal_state == SignalState.YELLOW:
                color = config.COLOR_SIGNAL_YELLOW
            else:
                color = config.COLOR_SIGNAL_RED
            
            text = f"  {side}: {count}"
            label = self.font_small.render(text, True, color)
            self.screen.blit(label, (panel_x + 20, y_offset))
            y_offset += 28
        
        y_offset += 15
        
        # Total vehicles
        total = intersection.get_total_vehicle_count()
        total_text = self.font_small.render(f"Total Waiting: {total}", True, config.COLOR_TEXT)
        self.screen.blit(total_text, (panel_x + 15, y_offset))
        y_offset += 35
        
        # Vehicles crossed
        crossed = intersection.total_vehicles_crossed
        crossed_text = self.font_small.render(f"Vehicles Crossed: {crossed}", True, config.COLOR_TEXT)
        self.screen.blit(crossed_text, (panel_x + 15, y_offset))
        y_offset += 30
        
        # By type
        type_title = self.font_small.render("Crossed by Type:", True, config.COLOR_TEXT)
        self.screen.blit(type_title, (panel_x + 15, y_offset))
        y_offset += 28
        
        for vtype, color in config.VEHICLE_COLORS.items():
            count = intersection.vehicles_crossed_by_type[vtype]
            text = f"  {vtype}: {count}"
            label = self.font_small.render(text, True, color)
            self.screen.blit(label, (panel_x + 20, y_offset))
            y_offset += 28
    
    def _draw_controls(self):
        """Draw control instructions"""
        controls = [
            "Controls: ESC or Q - Exit  |  F - Toggle Fullscreen"
        ]
        
        y_offset = self.height - 40
        for control_text in controls:
            control = self.font_small.render(control_text, True, config.COLOR_TEXT)
            self.screen.blit(control, (self.width // 2 - control.get_width() // 2, y_offset))
            y_offset += 30
    
    def check_events(self):
        """
        Check for user input events
        
        Returns:
            bool: True if user wants to quit
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    return True
                elif event.key == pygame.K_f:
                    self.toggle_fullscreen()
        return False
    
    def cleanup(self):
        """Clean up Pygame"""
        pygame.quit()

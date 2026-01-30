"""
GUI Module - Traffic Signal Visualization
Displays 4 video feeds, vehicle counts, signal states, and countdown timers
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
from typing import Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    GUI_WIDTH, GUI_HEIGHT, VIDEO_DISPLAY_WIDTH, VIDEO_DISPLAY_HEIGHT,
    SIGNAL_COLORS, SIGNAL_SEQUENCE
)
from controllers.traffic_controller import SignalState


class TrafficGUI:
    """
    Graphical User Interface for Traffic Signal System
    Shows live video feeds and signal status
    """
    
    def __init__(self, root: tk.Tk):
        """
        Initialize GUI
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("🚦 Smart Traffic Signal Automation System - CS331 Project")
        self.root.geometry(f"{GUI_WIDTH}x{GUI_HEIGHT}")
        self.root.configure(bg='#1a1a1a')
        
        # Video display labels
        self.video_labels = {}
        
        # Signal indicator canvases
        self.signal_canvases = {}
        self.signal_circles = {}
        
        # Info labels
        self.info_labels = {}
        self.timer_labels = {}
        
        # System status label
        self.status_label = None
        
        # Statistics labels
        self.stats_labels = {}
        
        # Create GUI layout
        self._create_gui()
        
        print("✓ GUI initialized")
    
    def _create_gui(self):
        """Create GUI layout"""
        # Title header
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        
        title_label = tk.Label(
            header_frame,
            text="SMART TRAFFIC SIGNAL AUTOMATION SYSTEM",
            font=('Arial', 20, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=15)
        
        # Main content area
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top row (North and South)
        top_frame = tk.Frame(main_frame, bg='#1a1a1a')
        top_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self._create_side_panel(top_frame, "NORTH", 0, 0)
        self._create_side_panel(top_frame, "SOUTH", 0, 1)
        
        # Bottom row (East and West)
        bottom_frame = tk.Frame(main_frame, bg='#1a1a1a')
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self._create_side_panel(bottom_frame, "EAST", 0, 0)
        self._create_side_panel(bottom_frame, "WEST", 0, 1)
        
        # Status bar at bottom
        self._create_status_bar()
    
    def _create_side_panel(self, parent, side: str, row: int, col: int):
        """
        Create panel for one traffic side
        
        Args:
            parent: Parent frame
            side: Side name (NORTH, SOUTH, EAST, WEST)
            row: Grid row
            col: Grid column
        """
        # Main panel frame
        panel = tk.Frame(parent, bg='#2c3e50', relief=tk.RAISED, borderwidth=2)
        panel.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
        parent.grid_columnconfigure(col, weight=1)
        parent.grid_rowconfigure(row, weight=1)
        
        # Side label
        side_label = tk.Label(
            panel,
            text=f"{side} SIDE",
            font=('Arial', 14, 'bold'),
            bg='#34495e',
            fg='white',
            pady=5
        )
        side_label.pack(fill=tk.X)
        
        # Video display
        video_label = tk.Label(panel, bg='black')
        video_label.pack(pady=5)
        self.video_labels[side] = video_label
        
        # Info frame (signal + statistics)
        info_frame = tk.Frame(panel, bg='#2c3e50')
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Traffic signal indicators (left side)
        signal_frame = tk.Frame(info_frame, bg='#2c3e50')
        signal_frame.pack(side=tk.LEFT, padx=10)
        
        signal_label = tk.Label(
            signal_frame,
            text="Signal:",
            font=('Arial', 10, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        signal_label.pack()
        
        signal_canvas = tk.Canvas(
            signal_frame,
            width=30,
            height=90,
            bg='#1a1a1a',
            highlightthickness=0
        )
        signal_canvas.pack()
        
        # Create three circles (RED, YELLOW, GREEN)
        circles = {
            'RED': signal_canvas.create_oval(5, 5, 25, 25, 
                                            fill=SIGNAL_COLORS['OFF']),
            'YELLOW': signal_canvas.create_oval(5, 35, 25, 55, 
                                               fill=SIGNAL_COLORS['OFF']),
            'GREEN': signal_canvas.create_oval(5, 65, 25, 85, 
                                              fill=SIGNAL_COLORS['OFF'])
        }
        
        self.signal_canvases[side] = signal_canvas
        self.signal_circles[side] = circles
        
        # Vehicle statistics (right side)
        stats_frame = tk.Frame(info_frame, bg='#2c3e50')
        stats_frame.pack(side=tk.LEFT, padx=20, fill=tk.BOTH, expand=True)
        
        info_text = tk.Label(
            stats_frame,
            text=f"Vehicles: 0\nCars: 0\nTrucks: 0\nBikes: 0",
            font=('Courier', 10),
            bg='#2c3e50',
            fg='#ecf0f1',
            justify=tk.LEFT
        )
        info_text.pack(anchor='w')
        self.info_labels[side] = info_text
        
        # Timer label
        timer_label = tk.Label(
            stats_frame,
            text="Time: --s",
            font=('Arial', 12, 'bold'),
            bg='#2c3e50',
            fg='#3498db'
        )
        timer_label.pack(anchor='w', pady=(5, 0))
        self.timer_labels[side] = timer_label
    
    def _create_status_bar(self):
        """Create bottom status bar"""
        status_frame = tk.Frame(self.root, bg='#34495e', height=50)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(
            status_frame,
            text="System Status: Initializing...",
            font=('Arial', 11),
            bg='#34495e',
            fg='white',
            anchor='w',
            padx=20
        )
        self.status_label.pack(fill=tk.BOTH, expand=True)
    
    def update_video(self, side: str, frame: np.ndarray):
        """
        Update video display for a specific side
        
        Args:
            side: Side name
            frame: Video frame (BGR format)
        """
        if frame is None or side not in self.video_labels:
            return
        
        try:
            # Resize frame to display size
            frame_resized = cv2.resize(frame, 
                                      (VIDEO_DISPLAY_WIDTH, VIDEO_DISPLAY_HEIGHT))
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Update label
            self.video_labels[side].imgtk = imgtk
            self.video_labels[side].configure(image=imgtk)
            
        except Exception as e:
            print(f"Error updating video for {side}: {e}")
    
    def update_signal_state(self, side: str, state: SignalState):
        """
        Update signal light indicators
        
        Args:
            side: Side name
            state: Signal state (RED, YELLOW, GREEN)
        """
        if side not in self.signal_circles:
            return
        
        canvas = self.signal_canvases[side]
        circles = self.signal_circles[side]
        
        # Turn off all lights first
        for light in ['RED', 'YELLOW', 'GREEN']:
            canvas.itemconfig(circles[light], fill=SIGNAL_COLORS['OFF'])
        
        # Turn on active light
        if state == SignalState.RED:
            canvas.itemconfig(circles['RED'], fill=SIGNAL_COLORS['RED'])
        elif state == SignalState.YELLOW:
            canvas.itemconfig(circles['YELLOW'], fill=SIGNAL_COLORS['YELLOW'])
        elif state == SignalState.GREEN:
            canvas.itemconfig(circles['GREEN'], fill=SIGNAL_COLORS['GREEN'])
    
    def update_vehicle_info(self, side: str, vehicle_data: Dict):
        """
        Update vehicle count information
        
        Args:
            side: Side name
            vehicle_data: Dictionary with vehicle counts
        """
        if side not in self.info_labels:
            return
        
        total = vehicle_data.get('total_vehicles', 0)
        cars = vehicle_data.get('cars', 0)
        trucks = vehicle_data.get('trucks', 0)
        bikes = vehicle_data.get('motorcycles', 0)
        emergency = vehicle_data.get('emergency', False)
        
        info_text = f"Vehicles: {total}\nCars: {cars}\nTrucks: {trucks}\nBikes: {bikes}"
        
        if emergency:
            info_text += "\n! EMERGENCY!"
            self.info_labels[side].configure(fg='#e74c3c')
        else:
            self.info_labels[side].configure(fg='#ecf0f1')
        
        self.info_labels[side].configure(text=info_text)
    
    def update_timer(self, side: str, time_remaining: float, is_active: bool):
        """
        Update countdown timer
        
        Args:
            side: Side name
            time_remaining: Seconds remaining
            is_active: Whether this side is currently active
        """
        if side not in self.timer_labels:
            return
        
        if is_active:
            timer_text = f"Time: {int(time_remaining)}s"
            color = '#2ecc71' if time_remaining > 10 else '#e74c3c'
        else:
            timer_text = "Time: --s"
            color = '#7f8c8d'
        
        self.timer_labels[side].configure(text=timer_text, fg=color)
    
    def update_status(self, message: str, is_emergency: bool = False):
        """
        Update system status message
        
        Args:
            message: Status message
            is_emergency: Whether this is an emergency status
        """
        if self.status_label:
            self.status_label.configure(
                text=f"Status: {message}",
                fg='#e74c3c' if is_emergency else 'white'
            )
    
    def get_root(self) -> tk.Tk:
        """Get root window"""
        return self.root


# Test function
if __name__ == "__main__":
    print("Testing Traffic GUI...\n")
    
    root = tk.Tk()
    gui = TrafficGUI(root)
    
    # Test updates
    def test_update():
        # Create test frame
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(test_frame, "TEST NORTH", (200, 240),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        gui.update_video("NORTH", test_frame)
        gui.update_signal_state("NORTH", SignalState.GREEN)
        gui.update_vehicle_info("NORTH", {
            'total_vehicles': 15,
            'cars': 10,
            'trucks': 3,
            'motorcycles': 2
        })
        gui.update_timer("NORTH", 35, True)
        gui.update_status("System Running - Test Mode")
    
    root.after(100, test_update)
    
    print("✓ GUI window created")
    print("  Close window to end test\n")
    
    root.mainloop()

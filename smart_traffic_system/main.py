"""
Main Application - Smart Traffic Signal Automation System
CS331 Software Engineering Lab Project

This is the main entry point that integrates all system components:
- Video Manager: Handles 4 video feeds
- Vehicle Detector: YOLO-based vehicle counting  
- Traffic Controller: Sequential signal logic with adaptive timing
- GUI: Visual interface showing all 4 sides
- Logger: Event and data logging

Author: CS331 Project Team
"""

import tkinter as tk
import threading
import time
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.video_manager import VideoManager
from models.vehicle_detector import VehicleDetector
from controllers.traffic_controller import TrafficSignalController
from views.traffic_gui import TrafficGUI
from utils.logger import TrafficLogger
from config import SIGNAL_SEQUENCE


class SmartTrafficSystem:
    """
    Main application class that coordinates all system components
    """
    
    def __init__(self):
        """Initialize the traffic signal system"""
        print("\n" + "="*70)
        print("  SMART TRAFFIC SIGNAL AUTOMATION SYSTEM")
        print("  CS331 - Software Engineering Lab Project")
        print("="*70 + "\n")
        
        # Initialize components
        print("Initializing system components...\n")
        
        try:
            # 1. Video Manager
            print("[1/5] Initializing Video Manager...")
            self.video_manager = VideoManager()
            
            # 2. Vehicle Detector
            print("\n[2/5] Loading Vehicle Detection Model...")
            self.vehicle_detector = VehicleDetector()
            
            # 3. Traffic Controller
            print("\n[3/5] Initializing Traffic Signal Controller...")
            self.traffic_controller = TrafficSignalController()
            
            # 4. Logger
            print("\n[4/5] Setting up Logger...")
            self.logger = TrafficLogger()
            
            # 5. GUI
            print("\n[5/5] Creating GUI Interface...")
            self.root = tk.Tk()
            self.gui = TrafficGUI(self.root)
            
            print("\n" + "="*70)
            print("✓ ALL COMPONENTS INITIALIZED SUCCESSFULLY")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n✗ INITIALIZATION FAILED: {e}")
            raise
        
        # System state
        self.running = False
        self.processing_thread = None
        
        # Vehicle count cache
        self.vehicle_counts = {side: {} for side in SIGNAL_SEQUENCE}
        
        # Performance tracking
        self.frame_count = 0
        self.start_time = None
    
    def start(self):
        """Start the traffic system"""
        print("Starting Smart Traffic System...\n")
        
        self.running = True
        self.start_time = time.time()
        
        # Log system start
        self.logger.log_system_start()
        
        # Start video capture
        self.video_manager.start()
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self.processing_thread.start()
        
        # Start GUI update loop
        self._gui_update_loop()
        
        # Update status
        self.gui.update_status("System Running - Monitoring Traffic")
        
        print("✓ System started successfully")
        print("\nMonitoring traffic... (Close window to stop)\n")
    
    def _processing_loop(self):
        """
        Main processing loop - runs in separate thread
        Handles vehicle detection and traffic control logic
        """
        last_log_time = time.time()
        log_interval = 5  # Log every 5 seconds
        
        while self.running:
            try:
                # Get frames from all sides
                frames = self.video_manager.get_all_frames()
                
                if not frames:
                    time.sleep(0.1)
                    continue
                
                # Detect vehicles on all sides
                for side, frame in frames.items():
                    if frame is not None:
                        # Run vehicle detection
                        detection_results = self.vehicle_detector.detect_vehicles(frame)
                        
                        # Store results
                        self.vehicle_counts[side] = detection_results
                        
                        # Log vehicle counts periodically
                        current_time = time.time()
                        if current_time - last_log_time >= log_interval:
                            self.logger.log_vehicle_count(side, detection_results)
                        
                        # Check for emergency vehicles
                        if detection_results.get('emergency', False):
                            self.logger.log_emergency(side)
                
                # Update log timer
                if time.time() - last_log_time >= log_interval:
                    last_log_time = time.time()
                
                # Update traffic controller
                vehicle_count_dict = {
                    side: data for side, data in self.vehicle_counts.items()
                }
                
                control_result = self.traffic_controller.update(vehicle_count_dict)
                
                # Log signal changes
                if control_result.get('switched', False):
                    self.logger.log_signal_change(control_result)
                    
                    # Update GUI status
                    from_side = control_result.get('from_side', '')
                    to_side = control_result.get('to_side', '')
                    reason = control_result.get('reason', '')
                    
                    status_msg = f"Signal: {from_side} → {to_side} | {reason}"
                    is_emergency = control_result.get('emergency', False)
                    
                    self.gui.update_status(status_msg, is_emergency)
                
                # Small delay to prevent CPU overload
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"Error in processing loop: {e}")
                time.sleep(0.1)
    
    def _gui_update_loop(self):
        """
        GUI update loop - updates visual display
        Runs on main thread (Tkinter requirement)
        """
        try:
            if not self.running:
                return
            
            # Get current signal states
            signal_states = self.traffic_controller.get_signal_states()
            current_side = self.traffic_controller.get_current_side()
            time_remaining = self.traffic_controller.get_time_remaining()
            
            # Update each side
            for side in SIGNAL_SEQUENCE:
                # Get frame
                frame = self.video_manager.get_frame(side)
                
                if frame is not None:
                    # Get vehicle data
                    vehicle_data = self.vehicle_counts.get(side, {})
                    
                    # Draw detections on frame
                    if vehicle_data.get('detections'):
                        frame = self.vehicle_detector.draw_detections(
                            frame, vehicle_data['detections']
                        )
                    
                    # Add stats overlay
                    frame = self.vehicle_detector.add_stats_overlay(
                        frame, vehicle_data, side
                    )
                    
                    # Update GUI video
                    self.gui.update_video(side, frame)
                
                # Update signal indicator
                signal_state = signal_states.get(side)
                if signal_state:
                    self.gui.update_signal_state(side, signal_state)
                
                # Update vehicle info
                if side in self.vehicle_counts:
                    self.gui.update_vehicle_info(side, self.vehicle_counts[side])
                
                # Update timer
                is_active = (side == current_side)
                self.gui.update_timer(side, time_remaining, is_active)
            
            # Schedule next update
            self.root.after(50, self._gui_update_loop)  # ~20 FPS
            
        except Exception as e:
            print(f"Error in GUI update: {e}")
            if self.running:
                self.root.after(100, self._gui_update_loop)
    
    def stop(self):
        """Stop the traffic system"""
        print("\nStopping system...")
        
        self.running = False
        
        # Stop video manager
        self.video_manager.stop()
        
        # Log system stop
        self.logger.log_system_stop()
        
        # Show statistics
        self._print_statistics()
        
        print("\n✓ System stopped successfully")
    
    def _print_statistics(self):
        """Print system statistics"""
        runtime = time.time() - self.start_time if self.start_time else 0
        stats = self.traffic_controller.get_statistics()
        
        print("\n" + "="*70)
        print("SESSION STATISTICS")
        print("="*70)
        print(f"Runtime: {runtime/60:.1f} minutes")
        print(f"Total Signal Cycles: {stats['total_cycles']}")
        print(f"Signal Changes: {stats['signal_changes']}")
        print(f"Final Active Side: {stats['current_side']}")
        print(f"\nLog files saved:")
        print(f"  • {self.logger.get_log_path()}")
        print(f"  • {self.logger.get_csv_path()}")
        print("="*70)
    
    def run(self):
        """Run the application"""
        try:
            # Start system
            self.start()
            
            # Handle window close event
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # Run GUI main loop
            self.root.mainloop()
            
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received")
        except Exception as e:
            print(f"\nError in main loop: {e}")
        finally:
            self.stop()
    
    def _on_closing(self):
        """Handle window close event"""
        self.stop()
        self.root.destroy()


def main():
    """Main entry point"""
    try:
        # Create and run the system
        system = SmartTrafficSystem()
        system.run()
        
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()

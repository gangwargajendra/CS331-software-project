"""
Logger Module
Tracks all system events, vehicle counts, and signal changes
"""

import csv
import os
from datetime import datetime
from typing import Dict, Any
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ENABLE_LOGGING, LOG_FILE, CSV_LOG_FILE


class TrafficLogger:
    """
    Logs traffic system events and data for analysis
    """
    
    def __init__(self, log_file: str = LOG_FILE, csv_file: str = CSV_LOG_FILE):
        """
        Initialize logger
        
        Args:
            log_file: Path to text log file
            csv_file: Path to CSV data file
        """
        self.log_file = log_file
        self.csv_file = csv_file
        self.enabled = ENABLE_LOGGING
        
        if self.enabled:
            self._initialize_files()
    
    def _initialize_files(self):
        """Initialize log files with headers"""
        # Create log directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Initialize text log
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("\n" + "="*80 + "\n")
            f.write(f"Traffic System Log - Session Started: {self._get_timestamp()}\n")
            f.write("="*80 + "\n\n")
        
        # Initialize CSV log if it doesn't exist
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp',
                    'Event_Type',
                    'Side',
                    'Signal_State',
                    'Total_Vehicles',
                    'Cars',
                    'Trucks',
                    'Motorcycles',
                    'Emergency',
                    'Duration',
                    'Reason'
                ])
        
        print(f"✓ Logger initialized: {os.path.basename(self.log_file)}")
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def log_event(self, event_type: str, message: str):
        """
        Log a general event
        
        Args:
            event_type: Type of event (INFO, WARNING, ERROR, etc.)
            message: Event message
        """
        if not self.enabled:
            return
        
        timestamp = self._get_timestamp()
        log_entry = f"[{timestamp}] [{event_type}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def log_signal_change(self, change_info: Dict[str, Any]):
        """
        Log traffic signal change
        
        Args:
            change_info: Dictionary with signal change information
        """
        if not self.enabled:
            return
        
        timestamp = self._get_timestamp()
        
        # Text log
        message = (f"Signal Changed: {change_info.get('from_side', 'N/A')} → "
                  f"{change_info['to_side']} | "
                  f"Duration: {change_info.get('duration', 0):.1f}s | "
                  f"Reason: {change_info.get('reason', 'N/A')}")
        
        if change_info.get('emergency', False):
            message = "[!EMERGENCY!] " + message
        
        self.log_event("SIGNAL", message)
        
        # CSV log
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                'SIGNAL_CHANGE',
                change_info['to_side'],
                'GREEN',
                '',
                '',
                '',
                '',
                change_info.get('emergency', False),
                f"{change_info.get('duration', 0):.1f}",
                change_info.get('reason', '')
            ])
    
    def log_vehicle_count(self, side: str, vehicle_data: Dict[str, Any]):
        """
        Log vehicle count data
        
        Args:
            side: Side name
            vehicle_data: Dictionary with vehicle counts
        """
        if not self.enabled:
            return
        
        timestamp = self._get_timestamp()
        
        # CSV log
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                'VEHICLE_COUNT',
                side,
                '',
                vehicle_data.get('total_vehicles', 0),
                vehicle_data.get('cars', 0),
                vehicle_data.get('trucks', 0),
                vehicle_data.get('motorcycles', 0),
                vehicle_data.get('emergency', False),
                '',
                ''
            ])
    
    def log_emergency(self, side: str):
        """
        Log emergency vehicle detection
        
        Args:
            side: Side where emergency vehicle detected
        """
        if not self.enabled:
            return
        
        message = f"[!EMERGENCY!] EMERGENCY VEHICLE DETECTED on {side} side!"
        self.log_event("EMERGENCY", message)
    
    def log_system_start(self):
        """Log system startup"""
        self.log_event("SYSTEM", "Traffic system started")
    
    def log_system_stop(self):
        """Log system shutdown"""
        self.log_event("SYSTEM", "Traffic system stopped")
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("\n" + "="*80 + "\n")
            f.write(f"Session Ended: {self._get_timestamp()}\n")
            f.write("="*80 + "\n\n")
    
    def get_log_path(self) -> str:
        """Get path to log file"""
        return self.log_file
    
    def get_csv_path(self) -> str:
        """Get path to CSV file"""
        return self.csv_file


# Test function
if __name__ == "__main__":
    print("Testing Traffic Logger...\n")
    
    logger = TrafficLogger()
    
    # Test logging
    logger.log_system_start()
    
    logger.log_signal_change({
        'from_side': 'NORTH',
        'to_side': 'EAST',
        'duration': 35.5,
        'reason': 'Early clearance'
    })
    
    logger.log_vehicle_count('NORTH', {
        'total_vehicles': 15,
        'cars': 10,
        'trucks': 3,
        'motorcycles': 2,
        'emergency': False
    })
    
    logger.log_emergency('SOUTH')
    
    logger.log_system_stop()
    
    print(f"✓ Logger test passed")
    print(f"  Log file: {logger.get_log_path()}")
    print(f"  CSV file: {logger.get_csv_path()}")

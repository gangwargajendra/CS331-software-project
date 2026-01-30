"""
Video Manager Module
Handles multiple video feeds from all four traffic sides
"""

import cv2
import threading
import queue
from typing import Dict, Optional
import time
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import VIDEO_SOURCES, FRAME_SKIP


class VideoManager:
    """
    Manages video capture from multiple sources (4 sides)
    Provides thread-safe frame access
    """
    
    def __init__(self, video_sources: Dict[str, str] = VIDEO_SOURCES):
        """
        Initialize video manager with sources
        
        Args:
            video_sources: Dictionary mapping side names to video paths
        """
        self.video_sources = video_sources
        self.captures = {}
        self.current_frames = {}
        self.frame_queues = {}
        self.running = False
        self.threads = {}
        self.frame_skip = FRAME_SKIP
        self.frame_counts = {side: 0 for side in video_sources.keys()}
        
        # Initialize video captures
        self._initialize_captures()
    
    def _initialize_captures(self):
        """Initialize video capture objects for all sides"""
        print("\n" + "="*60)
        print("INITIALIZING VIDEO SOURCES")
        print("="*60)
        
        for side, video_path in self.video_sources.items():
            if not os.path.exists(video_path):
                print(f"✗ {side}: Video not found at {video_path}")
                continue
            
            cap = cv2.VideoCapture(video_path)
            
            if cap.isOpened():
                self.captures[side] = cap
                self.frame_queues[side] = queue.Queue(maxsize=10)
                
                # Get video properties
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else 0
                
                print(f"✓ {side}: Loaded successfully")
                print(f"  Path: {os.path.basename(video_path)}")
                print(f"  FPS: {fps:.2f} | Frames: {frame_count} | Duration: {duration/60:.1f} min")
            else:
                print(f"✗ {side}: Failed to open video")
        
        print("="*60)
        
        if not self.captures:
            raise Exception("No video sources could be loaded!")
        
        print(f"\n✓ Successfully loaded {len(self.captures)}/4 video sources\n")
    
    def start(self):
        """Start video capture threads for all sides"""
        self.running = True
        
        for side in self.captures.keys():
            thread = threading.Thread(target=self._capture_loop, 
                                     args=(side,),
                                     daemon=True)
            thread.start()
            self.threads[side] = thread
            
        print("✓ Video capture threads started\n")
    
    def _capture_loop(self, side: str):
        """
        Continuous capture loop for a specific side
        
        Args:
            side: Side name (NORTH, SOUTH, EAST, WEST)
        """
        cap = self.captures[side]
        frame_counter = 0
        
        while self.running:
            ret, frame = cap.read()
            
            # Loop video when it ends
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            # Frame skipping for performance
            frame_counter += 1
            if frame_counter % self.frame_skip != 0:
                continue
            
            # Store frame
            self.current_frames[side] = frame
            self.frame_counts[side] += 1
            
            # Put frame in queue (non-blocking)
            try:
                if not self.frame_queues[side].full():
                    self.frame_queues[side].put(frame, block=False)
            except queue.Full:
                pass
            
            # Small delay to control frame rate
            time.sleep(0.001)
    
    def get_frame(self, side: str) -> Optional[cv2.Mat]:
        """
        Get the latest frame from a specific side
        
        Args:
            side: Side name
            
        Returns:
            Latest frame or None if not available
        """
        return self.current_frames.get(side, None)
    
    def get_all_frames(self) -> Dict[str, cv2.Mat]:
        """
        Get latest frames from all sides
        
        Returns:
            Dictionary mapping side names to frames
        """
        return self.current_frames.copy()
    
    def stop(self):
        """Stop all video capture threads"""
        print("\nStopping video captures...")
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads.values():
            thread.join(timeout=2.0)
        
        # Release all captures
        for cap in self.captures.values():
            cap.release()
        
        print("✓ All video captures stopped\n")
    
    def get_video_info(self, side: str) -> Dict:
        """
        Get video information for a specific side
        
        Args:
            side: Side name
            
        Returns:
            Dictionary with video properties
        """
        if side not in self.captures:
            return {}
        
        cap = self.captures[side]
        
        return {
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "current_frame": int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        }
    
    def is_running(self) -> bool:
        """Check if video manager is running"""
        return self.running
    
    def restart_video(self, side: str):
        """
        Restart video from beginning for a specific side
        
        Args:
            side: Side name
        """
        if side in self.captures:
            self.captures[side].set(cv2.CAP_PROP_POS_FRAMES, 0)
            print(f"✓ Restarted video for {side} side")


# Test function
if __name__ == "__main__":
    print("Testing Video Manager...")
    
    try:
        vm = VideoManager()
        vm.start()
        
        print("Capturing frames for 5 seconds...")
        time.sleep(5)
        
        frames = vm.get_all_frames()
        print(f"\n✓ Captured frames from {len(frames)} sides")
        
        for side, frame in frames.items():
            if frame is not None:
                print(f"  {side}: {frame.shape}")
        
        vm.stop()
        print("\n✓ Video Manager test passed")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")

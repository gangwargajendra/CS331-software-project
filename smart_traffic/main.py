"""
Main Entry Point
Run this file to start the traffic simulation
"""

from traffic_signal import SignalController
from traffic_simulation import Intersection
from visualization import TrafficDisplay

def main():
    """
    Main function to run the traffic simulation
    """
    print("=" * 70)
    print("Smart Traffic Signal Simulation")
    print("=" * 70)
    print("\nInitializing simulation...")
    print("Features:")
    print("  ✓ Fullscreen display")
    print("  ✓ Different vehicle types (Car, Truck, Bus)")
    print("  ✓ Unique vehicle ID numbers")
    print("  ✓ Sequential traffic signals")
    print("  ✓ Real-time statistics")
    print("\nControls:")
    print("  - ESC or Q: Exit simulation")
    print("  - F: Toggle fullscreen/windowed mode")
    print("\nStarting...\n")
    
    # Initialize components
    signal_controller = SignalController()
    intersection = Intersection(signal_controller)
    display = TrafficDisplay()
    
    # Main simulation loop
    running = True
    frame_count = 0
    
    try:
        while running:
            # Check for quit event
            if display.check_events():
                running = False
            
            # Update intersection (signals + vehicles)
            intersection.update()
            
            # Draw everything
            display.draw(intersection)
            
            frame_count += 1
            
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
    except Exception as e:
        print(f"\n\nError occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        display.cleanup()
        print("\nSimulation ended.")
        print(f"Total frames rendered: {frame_count}")
        print(f"Total vehicles crossed: {intersection.total_vehicles_crossed}")
        print("=" * 70)

if __name__ == "__main__":
    main()

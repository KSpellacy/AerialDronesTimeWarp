# recorder/generic_recorder.py
"""
Generic waypoint recorder for VEX Aerial Drones competitions.
Records course parameters in a year-agnostic format.
"""
import json
import time
from datetime import datetime
from pathlib import Path
from codrone_edu.drone import Drone

# Sampling parameters for height averaging
SAMPLES = 7
DELAY = 0.02

# Data directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def average_height(drone, samples=SAMPLES, delay=DELAY):
    """
    Take multiple height readings and return their average.
    
    Args:
        drone: CoDrone EDU instance
        samples: Number of samples to average
        delay: Delay between samples in seconds
    
    Returns:
        Average height in cm, or None if no valid readings
    """
    values = []
    for _ in range(samples):
        h = drone.get_height()
        if isinstance(h, (int, float)) and h >= 0:
            values.append(h)
        time.sleep(delay)
    
    if not values:
        return None
    
    avg = sum(values) / len(values)
    return round(avg, 1)


def record_waypoint(drone, waypoint_name, waypoint_type="unknown"):
    """
    Record height for a specific waypoint interactively.
    
    Args:
        drone: CoDrone EDU instance
        waypoint_name: Name/ID of the waypoint
        waypoint_type: Type of waypoint (gate, target, etc.)
    
    Returns:
        Height in cm
    """
    print(f"\n📍 Recording: {waypoint_name} ({waypoint_type})")
    print(f"   Hold the drone at the '{waypoint_name}' height and press Enter.")
    input("   Ready? > ")
    
    print("   Measuring", end="", flush=True)
    for _ in range(SAMPLES):
        print(".", end="", flush=True)
        time.sleep(DELAY)
    
    height = average_height(drone, samples=SAMPLES, delay=0)
    
    if height is not None:
        print(f" ✓")
        print(f"   Recorded {waypoint_name} height: {height} cm")
    else:
        print(f" ✗")
        print(f"   Warning: Could not read height for {waypoint_name}")
        height = 0.0
    
    return height


def get_float_input(prompt, default=None):
    """Get validated float input from user."""
    while True:
        try:
            user_input = input(prompt).strip()
            if not user_input and default is not None:
                return default
            return float(user_input)
        except ValueError:
            print("   ⚠ Please enter a valid number.")


def get_int_input(prompt, minimum=1, maximum=None):
    """Get validated integer input from user."""
    while True:
        try:
            value = int(input(prompt).strip())
            if value < minimum:
                print(f"   ⚠ Must be at least {minimum}.")
                continue
            if maximum and value > maximum:
                print(f"   ⚠ Must be at most {maximum}.")
                continue
            return value
        except ValueError:
            print("   ⚠ Please enter a valid integer.")


def create_default_config():
    """Create default configuration template."""
    return {
        "metadata": {
            "competition": "VEX Aerial Drones Time Warp",
            "year": datetime.now().year,
            "date_recorded": datetime.now().isoformat(),
            "recorded_by": "",
            "notes": ""
        },
        "waypoints": [
            {
                "id": "start",
                "type": "takeoff",
                "height_cm": 0,
                "action": "takeoff"
            }
        ],
        "tuning": {
            "height_tolerance_cm": 6,
            "height_timeout_sec": 6,
            "forward_chunk_cm": 30,
            "forward_stop_epsilon_cm": 5.0,
            "flow_scale": 1.0
        }
    }


def run_interactive():
    """
    Interactive recorder with flexible waypoint system.
    Guides user through recording process step-by-step.
    """
    print("\n" + "="*60)
    print("VEX Aerial Drones - Generic Course Recorder")
    print("="*60)
    
    drone = Drone()
    
    try:
        print("\n📡 Connecting to drone...")
        drone.pair()
        print("✓ Drone connected!")
        
        # Initialize configuration
        config = create_default_config()
        
        # Get metadata
        print("\n--- Course Information ---")
        config["metadata"]["recorded_by"] = input("Your name: ").strip()
        
        year_input = input(f"Competition year [{datetime.now().year}]: ").strip()
        if year_input:
            config["metadata"]["year"] = int(year_input)
        
        config["metadata"]["notes"] = input("Notes (optional): ").strip()
        
        # Get tuning parameters
        print("\n--- Tuning Parameters ---")
        print("Press Enter to use default values.")
        
        flow_scale = get_float_input(
            f"Flow scale [{config['tuning']['flow_scale']}]: ",
            default=config['tuning']['flow_scale']
        )
        config['tuning']['flow_scale'] = flow_scale
        
        height_tol = get_float_input(
            f"Height tolerance (cm) [{config['tuning']['height_tolerance_cm']}]: ",
            default=config['tuning']['height_tolerance_cm']
        )
        config['tuning']['height_tolerance_cm'] = height_tol
        
        # Record waypoints
        print("\n--- Waypoint Recording ---")
        num_waypoints = get_int_input(
            "How many waypoints (gates/targets) to record? ",
            minimum=1,
            maximum=10
        )
        
        for i in range(num_waypoints):
            print(f"\n--- Waypoint {i+1}/{num_waypoints} ---")
            
            # Get waypoint details
            wp_id = input("  Waypoint ID (e.g., 'arch', 'cube'): ").strip()
            if not wp_id:
                wp_id = f"waypoint_{i+1}"
            
            wp_type = input("  Type (gate/target): ").strip().lower()
            if wp_type not in ["gate", "target"]:
                print(f"  Unknown type '{wp_type}', using 'gate'")
                wp_type = "gate"
            
            wp_action = input("  Action (pass_through/land): ").strip().lower()
            if wp_action not in ["pass_through", "land"]:
                print(f"  Unknown action '{wp_action}', using 'pass_through'")
                wp_action = "pass_through"
            
            # Record height
            height = record_waypoint(drone, wp_id, wp_type)
            
            # Get distance
            print(f"  Distance from previous waypoint (cm): ", end="")
            distance = get_float_input("", default=0.0)
            
            # Add waypoint to configuration
            config["waypoints"].append({
                "id": wp_id,
                "type": wp_type,
                "height_cm": height,
                "distance_from_previous_cm": distance,
                "action": wp_action
            })
        
        # Save configuration
        print("\n--- Saving Configuration ---")
        year = config["metadata"]["year"]
        default_name = f"course_{year}.json"
        
        filename = input(f"Filename [{default_name}]: ").strip()
        if not filename:
            filename = default_name
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        output_file = DATA_DIR / filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n✓ Configuration saved to: {output_file.resolve()}")
        
        # Summary
        print("\n--- Summary ---")
        print(f"Competition: {config['metadata']['competition']}")
        print(f"Year: {config['metadata']['year']}")
        print(f"Recorded by: {config['metadata']['recorded_by']}")
        print(f"\nWaypoints:")
        for i, wp in enumerate(config["waypoints"]):
            if wp["id"] == "start":
                continue
            print(f"  {i}. {wp['id']}")
            print(f"     Height: {wp['height_cm']} cm")
            print(f"     Distance: {wp['distance_from_previous_cm']} cm")
            print(f"     Action: {wp['action']}")
        
        print("\n✓ Recording complete!")
        print(f"\nTo run autonomous flight:")
        print(f"  python main.py phase1")
        print(f"Or specify config:")
        print(f"  python main.py phase1 --config {filename}")
    
    except KeyboardInterrupt:
        print("\n\n⚠ Recording cancelled by user.")
    
    except Exception as e:
        print(f"\n✗ Error during recording: {e}")
        raise
    
    finally:
        drone.close()
        print("\n🔌 Drone disconnected")


def run_quick_phase1():
    """
    Quick recorder for standard Phase 1 course (backward compatible).
    Records arch and cube heights with distances.
    """
    print("\n" + "="*60)
    print("Phase 1 Quick Recorder (Backward Compatible)")
    print("="*60)
    
    drone = Drone()
    
    try:
        print("\n📡 Connecting to drone...")
        drone.pair()
        print("✓ Drone connected!")
        
        recorder_name = input("\nYour name: ").strip()
        
        # Create configuration
        config = create_default_config()
        config["metadata"]["recorded_by"] = recorder_name
        config["metadata"]["notes"] = "Phase 1 - Standard arch and cube course"
        
        # Record arch
        print("\n--- Arch Gate ---")
        arch_height = record_waypoint(drone, "arch", "gate")
        arch_distance = get_float_input("Distance to arch from start (cm): ")
        
        config["waypoints"].append({
            "id": "arch",
            "type": "gate",
            "height_cm": arch_height,
            "distance_from_previous_cm": arch_distance,
            "action": "pass_through"
        })
        
        # Record cube
        print("\n--- Cube Target ---")
        cube_height = record_waypoint(drone, "cube", "target")
        cube_distance = get_float_input("Distance from arch to cube (cm): ")
        
        config["waypoints"].append({
            "id": "cube",
            "type": "target",
            "height_cm": cube_height,
            "distance_from_previous_cm": cube_distance,
            "action": "land"
        })
        
        # Save with default name for compatibility
        output_file = DATA_DIR / "phase1_params.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n✓ Configuration saved to: {output_file.resolve()}")
        print("\nRecorded parameters:")
        print(f"  Arch height: {arch_height} cm at {arch_distance} cm")
        print(f"  Cube height: {cube_height} cm at {cube_distance} cm from arch")
        print("\nReady to fly! Run: python main.py phase1")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise
    
    finally:
        drone.close()
        print("\n🔌 Drone disconnected")


def run(quick_mode=False):
    """
    Main entry point for recorder.
    
    Args:
        quick_mode: If True, use quick Phase 1 recorder (backward compatible)
    """
    if quick_mode:
        run_quick_phase1()
    else:
        run_interactive()


if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        run(quick_mode=True)
    else:
        run(quick_mode=False)

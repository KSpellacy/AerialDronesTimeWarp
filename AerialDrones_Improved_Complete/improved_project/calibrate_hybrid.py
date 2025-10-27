#!/usr/bin/env python3
"""
Calibration script for time-based autonomous navigation.
Run this to determine the cm_per_second value for your drone.

** INTEGRATED WITH AUTONOMOUS MISSION **
Automatically updates mission_2026_autonomous_waypoints.json with calibration results

Usage:
    python calibrate_hybrid.py
"""
import sys
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import time
from codrone_edu.drone import Drone


def calibrate_time_based_navigation(drone, num_trials=3):
    """
    Calibrate time-based navigation by measuring actual distance traveled.

    This determines the cm_per_second value for your specific drone and environment.

    Args:
        drone: Connected CoDrone EDU instance
        num_trials: Number of calibration runs (default 3)

    Returns:
        dict: Calibrated parameters including cm_per_second
    """
    print(f"\n{'=' * 70}")
    print(f"       TIME-BASED NAVIGATION CALIBRATION")
    print(f"{'=' * 70}")
    print(f"Trials: {num_trials}")
    print(f"\n📋 SETUP INSTRUCTIONS:")
    print(f"  1. Use a measuring tape to mark 100cm on the floor")
    print(f"  2. Mark the start position clearly")
    print(f"  3. Clear the flight path (at least 150cm)")
    print(f"  4. Ensure good lighting")
    print(f"\n🔧 FOR EACH TRIAL:")
    print(f"  1. Place drone at START mark")
    print(f"  2. Drone will take off and fly forward for 3 seconds")
    print(f"  3. Measure ACTUAL distance from start to landing spot")
    print(f"  4. Enter the measured distance")
    print(f"{'=' * 70}\n")

    input("Press Enter when ready to start calibration...")

    # Power settings
    forward_power = 50
    test_duration = 3.0

    speeds = []

    for trial in range(num_trials):
        print(f"\n{'=' * 70}")
        print(f"TRIAL {trial + 1}/{num_trials}")
        print(f"{'=' * 70}")

        input("📍 Position drone at START mark, then press Enter...")

        # Take off
        print("\n✈️  Taking off...")
        drone.takeoff()
        time.sleep(2.5)

        print(f"▶️  Moving forward at power {forward_power} for {test_duration} seconds...")

        # TIME-BASED MOVEMENT (same as autonomous mission)
        print("test")
        drone.set_pitch(forward_power)
        drone.move(test_duration)
        print("test")# <-- CRITICAL: Move for specified time
        drone.set_pitch(0)

        # Hover briefly
        print("⏸️  Hovering...")
        drone.hover(1)

        # Land
        print("🛬 Landing...")
        drone.land()
        time.sleep(2)

        # Get user input for actual distance
        print(f"\n📏 MEASURE the distance from START mark to where drone landed.")
        while True:
            try:
                actual_distance = float(input(f"   Enter measured distance (cm): "))
                if actual_distance > 0:
                    break
                print("   ⚠️  Please enter a positive number.")
            except ValueError:
                print("   ⚠️  Please enter a valid number.")

        # Calculate speed
        speed = actual_distance / test_duration
        speeds.append(speed)

        print(f"   ✓ Calculated speed: {speed:.1f} cm/s")
        print(f"   (traveled {actual_distance:.0f} cm in {test_duration} seconds)")

    # Calculate statistics
    avg_speed = sum(speeds) / len(speeds)
    std_dev = (sum((s - avg_speed) ** 2 for s in speeds) / len(speeds)) ** 0.5

    print(f"\n{'=' * 70}")
    print(f"       CALIBRATION RESULTS")
    print(f"{'=' * 70}")
    print(f"Individual speeds: {', '.join([f'{s:.1f} cm/s' for s in speeds])}")
    print(f"Average speed:     {avg_speed:.1f} cm/s")
    print(f"Standard dev:      {std_dev:.1f} cm/s")

    if std_dev > 3.0:
        print(f"\n⚠️  Warning: High variation in measurements!")
        print(f"   Consider recalibrating for better consistency.")
    else:
        print(f"\n✓ Good consistency!")

    # Return calibration parameters
    return {
        'cm_per_second': round(avg_speed, 1),
        'forward_power': forward_power,
        'throttle_power': 25,  # Default for vertical movement
        'test_duration': test_duration,
        'std_dev': round(std_dev, 1),
        'num_trials': num_trials
    }


def update_json_with_calibration(json_file, tuning_params):
    """
    Update the mission JSON file with calibrated tuning parameters.

    Args:
        json_file: Path to mission_2026_autonomous_waypoints.json
        tuning_params: Dictionary with calibration results

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        json_path = Path(json_file)

        if not json_path.exists():
            print(f"\n⚠️  File not found: {json_file}")
            print(f"   Current directory: {Path.cwd()}")
            return False

        # Load existing JSON
        with open(json_path, 'r') as f:
            mission_data = json.load(f)

        # Update or add tuning section
        mission_data['tuning'] = {
            'cm_per_second': tuning_params['cm_per_second'],
            'forward_power': tuning_params['forward_power'],
            'throttle_power': tuning_params['throttle_power'],
            'calibration_info': {
                'test_duration': tuning_params['test_duration'],
                'std_dev': tuning_params['std_dev'],
                'num_trials': tuning_params['num_trials'],
                'calibration_date': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }

        # Save updated JSON
        with open(json_path, 'w') as f:
            json.dump(mission_data, f, indent=2)

        print(f"\n✓ Updated {json_file} with calibration data!")
        return True

    except json.JSONDecodeError as e:
        print(f"\n✗ Error: Invalid JSON file - {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error updating JSON: {e}")
        return False


def print_summary(tuning_params, json_file):
    """Print calibration summary and next steps."""
    print(f"\n{'=' * 70}")
    print(f"📝 CALIBRATION COMPLETE")
    print(f"{'=' * 70}")
    print(f"\nYour drone's calibrated values:")
    print(f"  • Speed:          {tuning_params['cm_per_second']:.1f} cm/s")
    print(f"  • Power:          {tuning_params['forward_power']}")
    print(f"  • Consistency:    {tuning_params['std_dev']:.1f} cm/s std dev")

    if Path(json_file).exists():
        print(f"\n✓ Values saved to: {json_file}")
    else:
        print(f"\n⚠️  Could not find: {json_file}")
        print(f"\nManually add these values to your JSON file:")
        print(f'\n  "tuning": {{')
        print(f'    "cm_per_second": {tuning_params["cm_per_second"]},')
        print(f'    "forward_power": {tuning_params["forward_power"]},')
        print(f'    "throttle_power": {tuning_params["throttle_power"]}')
        print(f'  }}')

    print(f"\n{'=' * 70}")
    print(f"🚀 NEXT STEPS")
    print(f"{'=' * 70}")
    print(f"1. Check that {json_file} has tuning section")
    print(f"2. Run: python autonomous_mission_time_based.py")
    print(f"3. Your drone will use these calibrated values!")
    print(f"{'=' * 70}\n")


def main():
    """Main calibration routine."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║          TIME-BASED NAVIGATION CALIBRATION                        ║")
    print("║          For Mission 2026 Autonomous Flight                       ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print("\nThis calibration determines how fast your drone flies forward.")
    print("Results will be saved to mission_2026_autonomous_waypoints.json\n")

    # JSON file to update
    json_file = 'mission_2026_autonomous_waypoints.json'

    # Connect to drone
    print("Connecting to drone...")
    drone = Drone()

    try:
        drone.pair()
        battery = drone.get_battery()
        print(f"✓ Connected! Battery: {battery}%\n")

        if battery < 40:
            print("⚠️  Warning: Battery below 40%")
            print("   Recommend charging before calibration for consistent results.\n")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                print("Calibration cancelled.")
                return

        # Run calibration
        tuning_params = calibrate_time_based_navigation(drone, num_trials=3)

        # Update JSON file with results
        update_json_with_calibration(json_file, tuning_params)

        # Print summary
        print_summary(tuning_params, json_file)

    except KeyboardInterrupt:
        print("\n\n⚠️  Calibration interrupted by user")
    except Exception as e:
        print(f"\n✗ Error during calibration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        drone.close()
        print("\nDrone disconnected.")


if __name__ == "__main__":
    main()
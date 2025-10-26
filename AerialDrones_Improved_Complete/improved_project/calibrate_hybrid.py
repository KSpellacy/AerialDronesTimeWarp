# calibrate_hybrid.py
"""
Calibration script for hybrid time-based navigation system.
Run this to determine the cm_per_second value for your drone.
"""
import sys
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
        float: Calibrated cm_per_second value
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
    forward_power = 30
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

        # Move forward for test duration
        drone.set_pitch(forward_power)
        time.sleep(test_duration)
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

    print(f"\n{'=' * 70}")
    print(f"📝 UPDATE YOUR CONFIG FILE")
    print(f"{'=' * 70}")
    print(f"\nAdd these values to data/phase1_params.json:")
    print(f'\n  "tuning": {{')
    print(f'    "cm_per_second": {avg_speed:.1f},')
    print(f'    "forward_power": {forward_power},')
    print(f'    "throttle_power": 25,')
    print(f'    "height_tolerance_cm": 5,')
    print(f'    "height_timeout_sec": 8')
    print(f'  }}')
    print(f"\n{'=' * 70}\n")

    return avg_speed


def main():
    """Main calibration routine."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║          HYBRID TIME-BASED NAVIGATION CALIBRATION                 ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print("\nThis calibration determines how fast your drone flies forward.")
    print("More accurate than optical flow, and works in any environment!\n")

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
        cm_per_second = calibrate_time_based_navigation(drone, num_trials=3)

        print(f"✓ Calibration complete!")
        print(f"  Your drone's forward speed: {cm_per_second:.1f} cm/s at power 30")

    except KeyboardInterrupt:
        print("\n\n⚠️  Calibration interrupted by user")
    except Exception as e:
        print(f"\n✗ Error during calibration: {e}")
    finally:
        drone.close()
        print("\nDrone disconnected.")


if __name__ == "__main__":
    main()
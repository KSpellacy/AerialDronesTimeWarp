#!/usr/bin/env python3
"""
VEX Aerial Drones Time Warp - Autonomous Controller
Main entry point with integrated hybrid time-based navigation support
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from codrone_edu.drone import Drone
import time


def print_header():
    """Print application header."""
    print("\n" + "=" * 70)
    print("VEX Aerial Drones Time Warp - Autonomous Controller")
    print("Version 2.0 - Hybrid Time-Based Navigation")
    print("Modes:")
    print("  'record'    - Record course waypoints and parameters")
    print("  'fly'       - Execute autonomous flight using saved configuration")
    print("  'calibrate' - Calibrate navigation system")
    print("=" * 70)


def print_menu():
    """Print main menu."""
    print("\nChoose a mode:")
    print("  1) record     - Record course waypoints and save to JSON")
    print("  2) fly        - Execute autonomous flight")
    print("  3) calibrate  - Calibrate navigation system")
    print("  4) exit       - Quit")


def get_mode_choice():
    """Get mode choice from user."""
    while True:
        choice = input("\nEnter 1-4: ").strip()
        if choice == '1':
            return 'record'
        elif choice == '2':
            return 'fly'
        elif choice == '3':
            return 'calibrate'
        elif choice == '4':
            return 'exit'
        else:
            print("Invalid choice. Please enter 1-4.")


def run_recorder(config_path):
    """Run the course recorder."""
    print("\n--- Recording Mode ---")
    print("Record waypoints for your autonomous flight")
    print("⚠ Not implemented in this version")
    print("Manually create/edit your configuration file instead.")


def run_autonomous_flight(config_path):
    """Run autonomous flight using saved configuration."""
    print("\n▶ Running mode: fly\n")
    print("\n--- Autonomous Flight Mode ---")
    print(f"Using configuration: {config_path}")

    from phases.autonomous_flight import run
    run(config_path=config_path)


def calibrate_time_based_navigation():
    """
    Calibrate time-based navigation by measuring actual distance traveled.

    Returns:
        float: Calibrated cm_per_second value
    """
    print(f"\n{'=' * 70}")
    print(f"       TIME-BASED NAVIGATION CALIBRATION")
    print(f"{'=' * 70}")

    num_trials = 3
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

    # Connect to drone
    drone = Drone()
    drone.pair()

    battery = drone.get_battery()
    print(f"✓ Connected! Battery: {battery}%\n")

    if battery < 40:
        print("⚠️  Warning: Battery below 40%")
        print("   Recommend charging before calibration for consistent results.\n")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Calibration cancelled.")
            drone.close()
            return None

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

    drone.close()

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


def calibrate_optical_flow():
    """Calibrate optical flow sensor (legacy method)."""
    from navigation.estimator import calibrate_flow_sensor

    distance = 100.0
    print(f"\n--- Optical Flow Calibration (Legacy) ---")
    print(f"Calibrating over {distance} cm")
    print("⚠ Ensure clear flight path and level surface!")

    drone = Drone()
    drone.pair()

    battery = drone.get_battery()
    print(f"Battery: {battery}%")
    print("✓ Drone paired!")

    input("\nPress Enter to start calibration...")

    flow_scale = calibrate_flow_sensor(drone, known_distance_cm=distance)

    print(f"\n✓ Calibration complete!")
    print(f"Add this line to your configuration file's 'tuning' section:")
    print(f'  "flow_scale": {flow_scale:.3f}')

    drone.close()

    return flow_scale


def run_calibration():
    """Run calibration with choice of method."""
    print("\n▶ Running mode: calibrate\n")
    print("\n--- Calibration Mode ---")
    print("Choose calibration type:")
    print("  1) Time-based navigation (RECOMMENDED - 90%+ accuracy)")
    print("  2) Optical flow sensor (Legacy - environmental issues)")

    while True:
        choice = input("\nEnter 1 or 2: ").strip()

        if choice == '1':
            # Time-based calibration
            try:
                cm_per_second = calibrate_time_based_navigation()
                if cm_per_second:
                    print(f"\n✓ Time-based calibration complete: {cm_per_second:.1f} cm/s")
            except KeyboardInterrupt:
                print("\n\n⚠ Calibration interrupted by user")
            except Exception as e:
                print(f"\n✗ Calibration error: {e}")
            break

        elif choice == '2':
            # Optical flow calibration
            try:
                flow_scale = calibrate_optical_flow()
                print(f"\n✓ Optical flow calibration complete: {flow_scale:.3f}")
            except KeyboardInterrupt:
                print("\n\n⚠ Calibration interrupted by user")
            except Exception as e:
                print(f"\n✗ Calibration error: {e}")
            break

        else:
            print("Invalid choice. Please enter 1 or 2.")


def run_mode(mode, args):
    """Execute the selected mode."""
    config_path = Path(args.get('config', 'data/phase1_params.json'))

    if mode == 'record':
        run_recorder(config_path)

    elif mode == 'fly':
        print("\n▶ Running mode: fly\n")
        run_autonomous_flight(config_path)

    elif mode == 'calibrate':
        run_calibration()

    elif mode == 'exit':
        print("\nExiting...")
        return False

    return True


def main():
    """Main application loop."""
    print_header()

    try:
        while True:
            print_menu()
            mode = get_mode_choice()

            if mode == 'exit':
                break

            args = {}
            should_continue = run_mode(mode, args)

            if not should_continue:
                break

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user. Exiting cleanly...")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTip: If this happened during flight, wait for the drone to")
        print("complete its land/cleanup sequence, then power cycle if needed.")
        raise

    finally:
        print("\n" + "=" * 70)
        print("Done. Thanks for flying with Etowah Eagles!")
        print("=" * 70)
        print("\n")


if __name__ == "__main__":
    main()
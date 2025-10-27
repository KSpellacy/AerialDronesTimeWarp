#!/usr/bin/env python3
"""
VEX Aerial Drones Time Warp - Autonomous Controller
Main entry point with integrated hybrid time-based navigation support

** UPDATED WITH PROPER drone.move() IMPLEMENTATION **
Uses set_pitch() + move(duration) like calibrate_hybrid.py
"""
import sys
from pathlib import Path
from recorder import generic_recorder
from phases import autonomous_flight
from recorder import generic_recorder
import calibrate_hybrid


# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from codrone_edu.drone import Drone
import time


def print_header():
    """Print application header."""
    print("\n" + "=" * 70)
    print("VEX Aerial Drones Time Warp - Autonomous Controller")
    print("Version 2.1 - Hybrid Time-Based Navigation (FIXED)")
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
    generic_recorder.run()


def run_autonomous_flight(config_path):
    """Run autonomous flight using saved configuration."""
    print("\n▶ Running mode: fly\n")
    print("\n--- Autonomous Flight Mode ---")
    print(f"Using configuration: {config_path}")
    autonomous_flight.main()


def calibrate_time_based_navigation():
    """
    Calibrate time-based navigation by measuring actual distance traveled.

    ** FIXED: Now uses drone.move(duration) properly **

    Returns:
        float: Calibrated cm_per_second value
    """
    calibrate_hybrid.main()


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
                print("\n\n⚠️ Calibration interrupted by user")
            except Exception as e:
                print(f"\n✗ Calibration error: {e}")
            break

        elif choice == '2':
            # Optical flow calibration
            try:
                flow_scale = calibrate_optical_flow()
                print(f"\n✓ Optical flow calibration complete: {flow_scale:.3f}")
            except KeyboardInterrupt:
                print("\n\n⚠️ Calibration interrupted by user")
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
        print("\n\n⚠️ Interrupted by user. Exiting cleanly...")

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
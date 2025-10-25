# main.py
"""
Main entry point for VEX Aerial Drones Time Warp autonomous flight system.
Supports both quick recording and flexible waypoint-based navigation.
"""
import argparse
import sys
from pathlib import Path

# Import modes
from recorder.generic_recorder import run as run_recorder
from phases.autonomous_flight import run as run_autonomous_flight

APP_NAME = "VEX Aerial Drones Time Warp - Autonomous Controller"
VERSION = "2.0"


def print_banner():
    """Print application banner."""
    line = "=" * 70
    print(line)
    print(f"{APP_NAME}")
    print(f"Version {VERSION}")
    print("Modes:")
    print("  'record'  - Record course waypoints and parameters")
    print("  'fly'     - Execute autonomous flight using saved configuration")
    print("  'calibrate' - Calibrate optical flow sensor")
    print(line)


def parse_args():
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="VEX Aerial Drones autonomous flight controller"
    )
    
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["record", "fly", "calibrate"],
        help="Operating mode: record waypoints, fly course, or calibrate sensors"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="data/phase1_params.json",
        help="Path to configuration file (default: data/phase1_params.json)"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Use quick Phase 1 recorder (arch + cube only)"
    )
    
    parser.add_argument(
        "--calibrate-distance",
        type=float,
        default=100.0,
        help="Known distance for calibration in cm (default: 100)"
    )
    
    return parser.parse_args()


def interactive_menu():
    """
    Interactive menu when no command-line arguments provided.
    
    Returns:
        Selected mode as string
    """
    print("\nChoose a mode:")
    print("  1) record     - Record course waypoints and save to JSON")
    print("  2) fly        - Execute autonomous flight")
    print("  3) calibrate  - Calibrate optical flow sensor")
    print("  4) exit       - Quit\n")
    
    while True:
        choice = input("Enter 1-4: ").strip()
        
        if choice == "1":
            return "record"
        elif choice == "2":
            return "fly"
        elif choice == "3":
            return "calibrate"
        elif choice == "4":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter 1-4.\n")


def run_mode(mode, args):
    """
    Execute the selected operating mode.
    
    Args:
        mode: Operating mode string
        args: Parsed command-line arguments
    """
    try:
        if mode == "record":
            print("\n--- Recording Mode ---")
            if args.quick:
                print("Using quick Phase 1 recorder\n")
                run_recorder(quick_mode=True)
            else:
                print("Using interactive generic recorder\n")
                run_recorder(quick_mode=False)
        
        elif mode == "fly":
            print("\n--- Autonomous Flight Mode ---")
            config_path = Path(args.config)
            
            if not config_path.exists():
                print(f"✗ Configuration file not found: {config_path}")
                print("\nAvailable configurations:")
                data_dir = Path("data")
                if data_dir.exists():
                    json_files = list(data_dir.glob("*.json"))
                    if json_files:
                        for f in json_files:
                            print(f"  - {f}")
                        print(f"\nRun with: python main.py fly --config data/FILENAME.json")
                    else:
                        print("  (none found)")
                else:
                    print("  (data directory not found)")
                
                print("\nRun recorder first: python main.py record")
                return
            
            print(f"Using configuration: {config_path}\n")
            run_autonomous_flight(config_path)
        
        elif mode == "calibrate":
            print("\n--- Calibration Mode ---")
            from codrone_edu.drone import Drone
            from nav.estimator import calibrate_flow_sensor
            
            distance = args.calibrate_distance
            print(f"Calibrating over {distance} cm")
            print("⚠ Ensure clear flight path and level surface!\n")
            
            drone = Drone()
            try:
                print("Pairing drone...")
                drone.pair()
                print("✓ Drone paired!\n")
                
                input("Press Enter to start calibration...")
                
                flow_scale = calibrate_flow_sensor(drone, known_distance_cm=distance)
                
                print(f"\n✓ Calibration complete!")
                print(f"Add this line to your configuration file's 'tuning' section:")
                print(f'  "flow_scale": {flow_scale:.3f}')
            
            finally:
                drone.close()
                print("\n🔌 Drone disconnected")
        
        else:
            print(f"Unknown mode: {mode}")
    
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user. Exiting cleanly...")
    
    except Exception as exc:
        print(f"\n✗ Error: {exc}")
        print("\nTip: If this happened during flight, wait for the drone to")
        print("complete its land/cleanup sequence, then power cycle if needed.")
        raise


def main():
    """Main application entry point."""
    print_banner()
    
    # Parse command-line arguments
    args = parse_args()
    
    # Determine mode
    if args.mode:
        mode = args.mode
    else:
        mode = interactive_menu()
    
    # Execute mode
    print(f"\n▶ Running mode: {mode}\n")
    run_mode(mode, args)
    
    print("\n" + "="*70)
    print("Done. Thanks for flying with Etowah Eagles!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

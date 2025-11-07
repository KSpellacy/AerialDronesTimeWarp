# main.py
import argparse

# Phase entry points
from recorder.position_recorder import run as record_phase1
from phases.phase1 import run as run_phase1

APP_NAME = "Aerial Drone Time Warp"


def print_banner():
    line = "=" * 56
    print(line)
    print(APP_NAME + " — Controller")
    print("Modes: 'record' to capture data, 'phase1' to fly Phase 1")
    print("Created by Keaton Spellacy... the most obviously coolest coder on the team :P")
    print(line)
    #  line "=" * 56 prints "=" 56 times


def parse_args():
    """
    Let argparse read command-line arguments.
    If  user runs no arguments, returns None for mode
    and falls back to interactive menu.
    """
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Run the recorder or Phase 1 for the Aerial Drone Time Warp project."
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["record", "phase1"],
        help="Choose 'record' to save parameters or 'phase1' to run the flight."
    )
    return parser.parse_args()


def interactive_menu():
    print("\nChoose a mode:")
    print("  1) record  — capture heights/distances and save to JSON")
    print("  2) phase1  — run Phase 1 flight using saved JSON\n")
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            return "record"
        if choice == "2":
            return "phase1"
        print("Invalid choice. Please enter 1 or 2.\n")


def run_mode(mode):
    try:
        if mode == "record":
            record_phase1()
        elif mode == "phase1":
            run_phase1()
        else:
            # Should not happen because argparse/menu restricts choices
            print("Unknown mode. Use 'record' or 'phase1'.")
    except KeyboardInterrupt:
        print("\n[Interrupted] Exiting cleanly...")
    except Exception as exc:
        # Keep this message generic for compatibility across versions
        print("\n[Error] " + str(exc))
        print("Tip: If this happened during flight, wait for the drone to complete "
              "its land/cleanup, power cycle if needed, then try again.")


def main():
    print_banner()
    ns = parse_args()
    mode = ns.mode if ns.mode else interactive_menu()
    print("\n Running mode:", mode, "\n")
    run_mode(mode)
    print("\nDone. Thanks for flying with Etowah! ")


if __name__ == "__main__":
    main()

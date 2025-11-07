import sys

try:
    import createJSONfile
except ModuleNotFoundError:
    createJSONfile = None


try:
    import autonCode
except ModuleNotFoundError:
    autonCode = None

BANNER = (
    "This is the code — developed by Keaton Spellacy — for the 2025–2026 Aerial Drone Competition\n"
    "This code reads data from a JSON file to set the pitch and fly for a certain amount of time.\n"
    "After the code flies for a certain amount of time, it will make an odometry check and then go\n"
    "to the correct height.\n"
)


def run_json_flow():
    if createJSONfile is None:
        print("createJSONfile.py not found. Place it next to this script.")
        return
    if not hasattr(createJSONfile, "run"):
        print("createJSONfile.run() not defined. Add a run() function.")
        return
    try:
        createJSONfile.run()
        print("JSON flow completed.")
    except KeyboardInterrupt:
        print("\n Canceled by user.")
    except Exception as e:
        print(f" Error while running JSON flow: {e}")


def run_current_code():
    if autonCode is None:
        print("autonCode.py not found. Place it next to this script.")
        return
    if not hasattr(autonCode, "run"):
        print("autonCode.run() not defined. Add a run() function.")
        return
    try:
        autonCode.run()
        print("current code completed.")
    except KeyboardInterrupt:
        print("\n Canceled by user.")
    except Exception as e:
        print(f" Error while running current code: {e}")


def main():
    print(BANNER)
    try:
        while True:
            choice = input(
                "Do you want to create a JSON file or run the current code?\n"
                "Type: runjson / runcurrentcode / quit > ").strip().lower()

            if choice in ("q", "quit", "exit"):
                print("Bye!")
                break
            elif choice in ("runjson", "run_json"):
                run_json_flow()
            elif choice in ("runcurrentcode", "run_current_code"):
                run_current_code()
            else:
                print("Please enter a proper response: runjson, runcurrentcode, or quit.")
    except KeyboardInterrupt:
        print("\n Stopped. Peace!")
        sys.exit(0)
    except Exception as e:
        # last-resort catcher; keep it broad at top-level only
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

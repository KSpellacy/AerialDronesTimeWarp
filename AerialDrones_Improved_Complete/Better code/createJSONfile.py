import json
import keyboard
import time

# Default pitch setting for all waypoints
pitch = 50


def getTime():
    """Ask for duration between waypoints."""
    while True:
        try:
            time_input = input("Enter time in seconds to next waypoint: ")
            time_value = float(time_input)
            if time_value < 0:
                print("Time cannot be negative. Please try again.")
                continue
            return time_value
        except ValueError:
            print("Invalid input. Please enter a valid number.")
        except Exception as e:
            print(f"Error: {e}. Please try again.")


def getHeight():
    """Ask for target altitude in centimeters."""
    while True:
        try:
            height_input = input("Enter target height (in cm) for this waypoint: ")
            height_value = float(height_input)
            if height_value < 0:
                print("Height cannot be negative. Please try again.")
                continue
            return height_value
        except ValueError:
            print("Invalid input. Please enter a valid number.")
        except Exception as e:
            print(f"Error: {e}. Please try again.")


def getData():
    """Create and save mission JSON file with pitch, time, and height."""
    version = input("Input version: ")
    running = True
    waypoints = []  # List to hold each waypoint

    trial = 0
    while running:
        print(f"\n--- Waypoint {trial + 1} ---")

        try:
            waypoint = {
                "waypoint_number": trial + 1,
                "pitch": pitch,
                "time_to_next_waypoint": getTime(),
                "height_cm": getHeight()
            }
            waypoints.append(waypoint)
            trial += 1
        except KeyboardInterrupt:
            print("\n\nWaypoint entry interrupted. Creating JSON with current waypoints...")
            running = False
            break
        except Exception as e:
            print(f"\nError creating waypoint: {e}")
            retry = input("Try again for this waypoint? (y/n): ").lower()
            if retry != 'y':
                continue
            else:
                trial += 1
                continue

        print("Hit q to create JSON, hit space to continue")
        innerLoop = True
        while innerLoop:
            try:
                if keyboard.is_pressed("q"):
                    print("You pressed 'q', creating JSON")
                    running = False
                    break
                elif keyboard.is_pressed("space"):
                    print("You pressed 'space', adding another waypoint")
                    innerLoop = False
                else:
                    time.sleep(0.01)  # Small delay to prevent CPU overuse
            except Exception as e:
                print(f"Keyboard error: {e}. Press Enter to continue or type 'q' and Enter to quit.")
                user_input = input().strip().lower()
                if user_input == 'q':
                    running = False
                    break
                else:
                    innerLoop = False

    # Filter out any invalid waypoints
    valid_waypoints = []
    for wp in waypoints:
        try:
            if all(key in wp for key in ["waypoint_number", "pitch", "time_to_next_waypoint", "height_cm"]):
                valid_waypoints.append(wp)
        except Exception:
            continue

    if not valid_waypoints:
        print("\nNo valid waypoints created. JSON file not saved.")
        return

    data = {
        "name": "Current Drone Mission",
        "version": version,
        "waypoints": valid_waypoints
    }

    # Save to JSON file
    try:
        with open("mission_data_Current.json", "w") as f:
            json.dump(data, f, indent=4)

        print(f"\nmission_data_Current.json created successfully with {len(valid_waypoints)} waypoints!")
        print(json.dumps(data, indent=4))  # print preview
    except Exception as e:
        print(f"\nError saving JSON file: {e}")


def run():
    """Entry point for the launcher script."""
    try:
        getData()
    except Exception as e:
        print(f"\nFatal error: {e}")


if __name__ == "__main__":
    run()
import json

# Default pitch setting for all waypoints
pitch = 50


def getTime():
    """Ask for duration between waypoints."""
    return input("Enter time in seconds to next waypoint: ")


def getHeight():
    """Ask for target altitude in centimeters."""
    return input("Enter target height (in cm) for this waypoint: ")


def getData():
    """Create and save mission JSON file with pitch, time, and height."""
    version = input("Input version: ")
    numWaypoints = int(input("How many waypoints will this code have? "))

    waypoints = []  # List to hold each waypoint

    for i in range(numWaypoints):
        print(f"\n--- Waypoint {i+1} ---")
        waypoint = {
            "waypoint_number": i + 1,
            "pitch": pitch,
            "time_to_next_waypoint": float(getTime()),
            "height_cm": float(getHeight())
        }
        waypoints.append(waypoint)

    data = {
        "name": "Current Drone Mission",
        "version": version,
        "waypoints": waypoints
    }

    # Save to JSON file
    with open("mission_data_Current.json", "w") as f:
        json.dump(data, f, indent=4)

    print("\nmission_data_Current.json created successfully!")
    print(json.dumps(data, indent=4))  # print preview


def run():
    """Entry point for the launcher script."""
    getData()

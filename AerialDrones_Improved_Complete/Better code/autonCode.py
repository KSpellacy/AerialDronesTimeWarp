from codrone_edu.drone import Drone

drone = Drone()
drone.pair()
import json
import time
import sys
import os

print("1")


def load_mission(path="mission_data_Current.json"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Mission file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "waypoints" not in data or not isinstance(data["waypoints"], list):
        raise ValueError("Mission JSON must contain a 'waypoints' list.")
    return data


def move_to_waypoints(drone, data):
    """
    Execute waypoints using simple time-based movement like the old code.
    Each waypoint moves to a height, then forward with pitch for duration.
    """
    for i, wp in enumerate(data["waypoints"]):
        pitch = int(wp.get("pitch", 0))
        duration = float(wp.get("time_to_next_waypoint", 0))
        target_alt_cm = float(wp.get("height_cm", 80))

        # Sanitize inputs
        pitch = max(-100, min(100, pitch))
        duration = max(0.0, duration)

        print(f" WP {i + 1} | target_height={target_alt_cm:.0f}cm, pitch={pitch}, time={duration:.2f}s")

        # 1) Move to target altitude using vertical movement
        # Assume we start at ~80cm after takeoff, calculate needed vertical movement
        if i == 0:
            # First waypoint: calculate from takeoff height (~80cm)
            current_height = 80.0
        else:
            # Subsequent waypoints: use previous waypoint height
            current_height = float(data["waypoints"][i - 1].get("height_cm", 80))

        height_diff_cm = target_alt_cm - current_height

        if abs(height_diff_cm) > 5:  # Only adjust if difference is significant
            # Calculate duration based on height change (rough estimate: ~50cm per second at throttle 50)
            throttle_power = 50
            duration = abs(height_diff_cm) / 50.0  # Adjust this ratio based on testing

            if height_diff_cm > 0:
                # Need to go UP
                print(f"   Moving UP {height_diff_cm:.0f}cm (throttle={throttle_power}, time={duration:.2f}s)")
                drone.set_throttle(throttle_power)
                drone.move(duration)
            else:
                # Need to go DOWN
                print(f"   Moving DOWN {abs(height_diff_cm):.0f}cm (throttle={-throttle_power}, time={duration:.2f}s)")
                drone.set_throttle(-throttle_power)
                drone.move(duration)

            # Stop vertical movement
            drone.set_throttle(0)
            drone.move()

            # Brief hover to stabilize
            drone.hover(0.5)

        # 2) Move forward with pitch for the specified duration
        if duration > 0 and pitch != 0:
            print(f"   Moving forward with pitch={pitch} for {duration:.2f}s")
            drone.set_pitch(pitch)
            drone.move(duration)

            # Stop forward motion
            drone.set_pitch(0)
            drone.move()

            # Brief hover to stabilize
            drone.hover(0.3)


def run():
    print("2")
    try:
        data = load_mission()
        print("Mission JSON:\n" + json.dumps(data, indent=2))

        print("3")

        # Optional calibration (if available)
        calib = getattr(drone, "calibrate", None)
        if callable(calib):
            print("Calibrating drone...")
            calib()
            time.sleep(0.5)

        print("4 - Taking off")
        drone.takeoff()
        drone.hover(1.0)  # Hover for 1 second to stabilize after takeoff

        print("5 - Starting mission waypoints")
        # Run the mission waypoints
        move_to_waypoints(drone, data)

        print("6 - Mission complete, landing")
        # Land
        drone.land()
        drone.close()

        print("Mission complete!")

    except KeyboardInterrupt:
        print("\nAborted by user. Landing…")
        try:
            drone.land()
            drone.close()
        except Exception:
            pass
        sys.exit(1)
    except Exception as e:
        print(f"\n!!! Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            drone.land()
            drone.close()
        except Exception:
            pass
        sys.exit(1)


# Don't forget to call run() to start the mission!
if __name__ == "__main__":
    run()
# phases/phase1.py
import json
import time
from pathlib import Path
from codrone_edu.drone import Drone, Direction

DATA_PATH = Path("data/phase1_params.json")


def rise_to_height(drone, target_cm, tolerance=6, timeout=6):
    """Move the drone up or down until it’s close to the target height."""
    start = time.time()
    while time.time() - start < timeout:
        current = drone.get_height()
        diff = target_cm - current
        if abs(diff) <= tolerance:
            return
        step = min(20, abs(diff))
        if diff > 0:
            drone.go(Direction.UP, step)
        else:
            drone.go(Direction.DOWN, step)
        time.sleep(0.1)


def go_forward(drone, distance_cm):
    """Move forward in small segments to improve accuracy."""
    remaining = distance_cm
    step = 50  # cm per move
    while remaining > 0:
        move = min(step, remaining)
        drone.go(Direction.FORWARD, move)
        remaining -= move
        time.sleep(0.1)

def run(config_path=DATA_PATH):
    """Run the full Phase 1 flight using saved JSON data."""
    if not config_path.exists():
        raise FileNotFoundError("Missing phase1_params.json. Run the recorder first!")

    with open(config_path, "r", encoding="utf-8") as f:
        params = json.load(f)

    # Pull data from dictionary
    arch_h = params["arch_height"]["height_cm"]
    cube_h = params["cube_height"]["height_cm"]
    forward_arch = params["forward_to_arch_cm"]
    forward_cube = params["forward_arch_to_cube_cm"]

    drone = Drone()
    try:
        print("Pairing...")
        drone.pair()

        print("Takeoff")
        drone.takeoff()
        time.sleep(1)

        print(f"Rising to arch height ({arch_h} cm)")
        rise_to_height(drone, arch_h)
        drone.hover(1)

        print(f"Moving forward {forward_arch} cm to reach the arch")
        go_forward(drone, forward_arch)

        print("Passing through arch gate...")
        drone.go(Direction.FORWARD, 20)
        time.sleep(0.2)

        print(f"Moving toward cube ({forward_cube} cm)")
        go_forward(drone, forward_cube)

        print(f"Descending to cube height ({cube_h} cm)")
        rise_to_height(drone, cube_h)

        print("Landing...")
        drone.land()
        time.sleep(0.5)

        print("Phase 1 complete!")

    finally:
        drone.close()
        print("Drone disconnected.")


if __name__ == "__main__":
    run()

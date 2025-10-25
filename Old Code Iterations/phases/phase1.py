# phases/phase1.py
import json
import time
from pathlib import Path
from codrone_edu.drone import Drone, Direction
from nav.estimator import Odometry  # <-- new: on-board odometry helper

DATA_PATH = Path("data/phase1_params.json")

# Height-control tuning
TOLERANCE = 6   # acceptable cm error to target height
TIMEOUT = 6     # seconds to try reaching a target height

# Forward-control tuning
STOP_EPS = 5.0  # stop within 5 cm of the forward target
FWD_CHUNK = 30  # cm per forward move (small chunks = straighter + safer)


def rise_to_height(drone, target_cm, tolerance=TOLERANCE, timeout=TIMEOUT):
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


def go_forward_until(drone, odo: Odometry, target_forward_cm):
    """
    Move forward while checking odometry.y in real time.
    Stops when estimated forward distance y reaches the target.
    """
    while True:
        odo.step()  # read latest flow/yaw/height
        _, y, _, _ = odo.pose()
        if y >= (target_forward_cm - STOP_EPS):
            break

        drone.go(Direction.FORWARD, FWD_CHUNK)
        time.sleep(0.05)

        # take a few estimator steps while the drone settles
        for _ in range(3):
            time.sleep(0.03)
            odo.step()


def run(config_path=DATA_PATH):
    """Run the full Phase 1 flight using saved JSON data (on-board sensors only)."""
    if not config_path.exists():
        raise FileNotFoundError("Missing phase1_params.json. Run the recorder first!")

    with open(config_path, "r", encoding="utf-8") as f:
        params = json.load(f)

    # Pull data from dictionary (as saved by your recorder)
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
        time.sleep(0.8)

        # Initialize odometry (all on-board). If you calibrate later, set flow_scale!=1.0.
        odo = Odometry(drone, flow_scale=1.0)
        odo.zero()
        odo.step()

        print(f"Rising to arch height ({arch_h} cm)")
        rise_to_height(drone, arch_h)
        drone.hover(0.5)
        odo.step()

        print(f"Moving forward {forward_arch} cm to reach the arch (odometry-controlled)")
        go_forward_until(drone, odo, forward_arch)

        # Snap odometry to the nominal leg length to bound drift (legal: uses your own preset)
        odo.y = float(forward_arch)

        print("Passing through arch gate...")
        drone.go(Direction.FORWARD, 20)  # small push to clear the gate
        time.sleep(0.2)
        odo.step()

        print(f"Moving toward cube ({forward_cube} cm) (odometry-controlled)")
        # Treat the second leg as additional forward distance from the arch
        target_total_forward = forward_arch + forward_cube
        go_forward_until(drone, odo, target_total_forward)
        odo.y = float(target_total_forward)  # optional snap again

        print(f"Descending to cube height ({cube_h} cm)")
        rise_to_height(drone, cube_h)
        time.sleep(0.2)
        odo.step()

        print("Landing...")
        drone.land()
        time.sleep(0.5)
        print("Phase 1 complete!")

    finally:
        drone.close()
        print("Drone disconnected.")


if __name__ == "__main__":
    run()

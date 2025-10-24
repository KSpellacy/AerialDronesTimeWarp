import json
import time
from datetime import datetime
from pathlib import Path
from codrone_edu.drone import Drone

# Number of samples for averaging get_height()
SAMPLES = 7
# Delay between samples (seconds)
DELAY = 0.02

# Save data to JSON file to use later
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = DATA_DIR / "phase1_params.json"


def average_height(drone, samples=SAMPLES, delay=DELAY):
    """Take multiple height readings and return their average (cm)."""
    values = []
    for _ in range(samples):
        values.append(drone.get_height())
        time.sleep(delay)

    nums = [v for v in values if isinstance(v, (int, float))]
    return round(sum(nums) / len(nums), 1) if nums else None


def run():
    """
    Records heights (arch, cube) via averaged samples and saves them with distances
    to a JSON file for later use.
    """
    drone = Drone()
    try:
        drone.pair()
        recorder = input("Input your name for records: ")

        data = {
            "_meta": {
                "phase": "Phase1",
                "date": datetime.now().isoformat(),
                "name": recorder
            }
        }

        print("Hold the drone at the arch gate height and press Enter.")
        input()
        data["arch_height"] = {"height_cm": average_height(drone)}
        print(f"Recorded arch height: {data['arch_height']['height_cm']} cm\n")

        print("Now hold the drone above the cube and press Enter.")
        input()
        data["cube_height"] = {"height_cm": average_height(drone)}
        print(f"Recorded cube height: {data['cube_height']['height_cm']} cm\n")

        # Ask user for distances
        data["forward_to_arch_cm"] = float(input("Distance to arch (cm): "))
        data["forward_arch_to_cube_cm"] = float(input("Distance from arch to cube (cm): "))

        # Save to JSON file
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f" Data saved to {OUT_PATH.resolve()}")

    finally:
        drone.close()
        print("🔌 drone disconnected")


if __name__ == "__main__":
    run()

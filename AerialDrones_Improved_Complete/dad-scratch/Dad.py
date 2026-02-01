import time

from codrone_edu.drone import Drone

json_script = [
    {"cmd":"takeoff"},
    {"cmd":"forward", "cm":60},
    {"cmd":"hover",    "s": 2.0},
    {"cmd":"up",      "power":40, "s":0.75},
    {"cmd":"hover",    "s":1.0},
    {"cmd":"down",    "power":30, "s":0.5},
    {"cmd":"hover",    "s":1.0},
    {"cmd":"backward","cm":60},
    {"cmd":"land"}
]

def get_settle_duration(cmd) -> float:
    return {
        "takeoff": 0.3,
        "forward": 0.15,
        "backward": 0.15,
        "up": 0.7,
        "down": 0.7,
        "hover": 0.1,
        "land": 0.7,
    }.get(cmd, 0.2)

def settle(cmd):
    time.sleep(get_settle_duration(cmd))

def run_step(drone, step):
    cmd = step["cmd"]

    match cmd:
        case "takeoff":
            drone.takeoff()
            #  settle(cmd)
        case "land":
            settle(cmd)
            drone.land()
            time.sleep(1.5)
        case "forward":
            drone.move_forward(int(step["cm"]))
            settle(cmd)  # settle time helps repeatability
        case "backward":
            drone.move_backward(int(step["cm"]))
            settle(cmd)  # settle time helps repeatability
        case "up":
            drone.go("up", float(step["power"]), float(step["s"]))
            settle(cmd)  # settle time helps repeatability
        case "down":
            drone.go("down", float(step["power"]), float(step["s"]))
            settle(cmd)  # settle time helps repeatability
        case "hover":
            time.sleep(float(step["s"]))
            settle(cmd)
        case _:
            raise ValueError("Unknown command: " + cmd)


def main():
    drone = Drone()
    drone.pair()

    try:
        for step in json_script:
            run_step(drone, step)
    finally:
        # safety: if anything goes wrong, try to land
        try:
            drone.land()
        except Exception:
            pass
        drone.close()


if __name__ == "__main__":
    main()


chatters_optimized_json = [
  {"cmd":"takeoff"},

  {"cmd":"TASK_panel_smallhole", "attempt": 1},
  {"cmd":"TASK_tunnel",          "attempt": 1},
  {"cmd":"TASK_green_keyhole",   "attempt": 1},
  {"cmd":"TASK_yellow_keyhole",  "attempt": 1},

  {"cmd":"TASK_panel_smallhole", "attempt": 2},
  {"cmd":"TASK_tunnel",          "attempt": 2},
  {"cmd":"TASK_green_keyhole",   "attempt": 2},
  {"cmd":"TASK_yellow_keyhole",  "attempt": 2},

  {"cmd":"TASK_identify_mat",    "mat": 1},
  {"cmd":"TASK_identify_mat",    "mat": 2},

  {"cmd":"TASK_blue_arch",       "attempt": 1},
  {"cmd":"TASK_blue_arch",       "attempt": 2},
  {"cmd":"TASK_red_arch",        "attempt": 1},
  {"cmd":"TASK_red_arch",        "attempt": 2},

  {"cmd":"TASK_land_bullseye"},
  {"cmd":"land"}
]
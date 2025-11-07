from codrone_edu.drone import Drone
import json
import time
import sys
import os


def _resolve(drone, names):
    for n in names:
        fn = getattr(drone, n, None)
        if callable(fn):
            return fn
    return None

def _read_hybrid_height(drone, thresh=150.0, blend_width=50.0):
    read_rng = _resolve(drone, ["get_range","get_bottom_range","get_height_range","get_optical_flow_range"])
    read_alt = _resolve(drone, ["get_height","get_altitude","get_barometer_height"])

    rng_cm = None
    baro_cm = None
    if read_rng:
        v = read_rng()
        rng_cm = v*100 if abs(v) < 10 else float(v)
    if read_alt:
        v = read_alt()
        baro_cm = v*100 if abs(v) < 10 else float(v)

    if rng_cm is not None and baro_cm is None:
        return rng_cm, 1.0, "range"
    if baro_cm is not None and rng_cm is None:
        return baro_cm, 0.0, "baro"
    if rng_cm is None and baro_cm is None:
        return 0.0, 0.5, "none"

    if rng_cm <= thresh:
        return rng_cm, 1.0, "range"
    if rng_cm >= thresh + blend_width:
        return baro_cm, 0.0, "baro"

    t = (rng_cm - thresh) / blend_width
    w = max(0.0, min(1.0, 1.0 - t))
    h = w * rng_cm + (1.0 - w) * baro_cm
    return h, w, "blend"

def move_to_altitude(drone,
                     target_cm,
                     settle_tolerance_cm=6.0,
                     settle_time_s=0.6,
                     timeout_s=6.0,
                     loop_hz=30.0,
                     kp_range=0.10,
                     kp_baro=0.06,
                     kd=0.10,
                     throttle_limits=(-18, 18)):
    set_throttle = _resolve(drone, ["set_throttle","setThrottle"])
    if not set_throttle:
        raise RuntimeError("No set_throttle() available in SDK")

    dt = 1.0 / loop_hz
    prev_err = 0.0
    settle_start = None
    t0 = time.perf_counter()

    while True:
        h, w_range, _ = _read_hybrid_height(drone)
        err = float(target_cm - h)

        kp = w_range * kp_range + (1.0 - w_range) * kp_baro
        derr = (err - prev_err) / dt
        prev_err = err

        u = kp * err + kd * derr
        u = max(throttle_limits[0], min(throttle_limits[1], u))
        if abs(err) < 2.0:
            u = 0.0

        set_throttle(int(u))

        if abs(err) <= settle_tolerance_cm:
            if settle_start is None:
                settle_start = time.perf_counter()
            elif time.perf_counter() - settle_start >= settle_time_s:
                set_throttle(0)
                return True
        else:
            settle_start = None

        if time.perf_counter() - t0 > timeout_s:
            set_throttle(0)
            return False

        time.sleep(dt)

def hold_altitude(drone,
                  target_cm,
                  duration_s,
                  loop_hz=30.0,
                  kp_range=0.08,
                  kp_baro=0.05,
                  kd=0.06,
                  throttle_limits=(-12, 12)):
    set_throttle = _resolve(drone, ["set_throttle","setThrottle"])
    if not set_throttle:
        raise RuntimeError("No set_throttle() available in SDK")

    dt = 1.0 / loop_hz
    prev_err = 0.0
    t_end = time.perf_counter() + duration_s

    while time.perf_counter() < t_end:
        h, w_range, _ = _read_hybrid_height(drone)
        err = float(target_cm - h)
        kp = w_range * kp_range + (1.0 - w_range) * kp_baro
        derr = (err - prev_err) / dt
        prev_err = err

        u = kp * err + kd * derr
        u = max(throttle_limits[0], min(throttle_limits[1], u))
        if abs(err) < 2.0:
            u = 0.0

        set_throttle(int(u))
        time.sleep(dt)

    set_throttle(0)
# ---------- end helpers ----------

def load_mission(path="mission_data_Current.json"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Mission file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "waypoints" not in data or not isinstance(data["waypoints"], list):
        raise ValueError("Mission JSON must contain a 'waypoints' list.")
    return data

def move_to_waypoints(drone, data):
    for i, wp in enumerate(data["waypoints"]):
        pitch = int(wp.get("pitch", 0))
        duration = float(wp.get("time_to_next_waypoint", 0))
        target_alt = float(wp.get("height_cm", 80))  # default 80cm if missing

        # sanitize
        pitch = max(-100, min(100, pitch))
        duration = max(0.0, duration)

        print(f"\n➡️ WP {i+1} | height={target_alt:.0f}cm, pitch={pitch}, time={duration:.2f}s")

        # 1) Go to altitude first (hybrid controller)
        ok = move_to_altitude(drone, target_cm=target_alt, timeout_s=8.0)
        print(f"   altitude -> {'OK' if ok else 'TIMEOUT'}")

        # 2) Time-based forward motion
        if duration > 0 and pitch != 0:
            drone.set_pitch(pitch)
            time.sleep(duration)
            drone.set_pitch(0)

        # 3) Brief hold to stabilize at target height
        hold_altitude(drone, target_cm=target_alt, duration_s=0.6)


def run():
    try:
        data = load_mission()
        print("Mission JSON:\n" + json.dumps(data, indent=2))

        drone = Drone()
        drone.pair()

        calib = getattr(drone, "calibrate", None)
        if callable(calib):
            calib()
            time.sleep(0.5)

        get_h = getattr(drone, "get_height", None)
        if callable(get_h):
            baro_base = get_h()
            if abs(baro_base) < 10:
                baro_base *= 100
            print(f"Barometer baseline: {baro_base:.1f} cm")

        drone.takeoff()
        time.sleep(0.8)

        # Optional initial stage height (e.g., 80 cm)
        move_to_altitude(drone, target_cm=80, timeout_s=8.0)
        hold_altitude(drone, target_cm=80, duration_s=1.0)

        # Run the mission waypoints
        move_to_waypoints(drone, data)

        # Land
        drone.land()
        drone.close()

    except KeyboardInterrupt:
        print("\n⏹️ Aborted by user. Landing…")
        try:
            drone.land()
            drone.close()
        except Exception:
            pass
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        try:
            drone.land()
            drone.close()
        except Exception:
            pass
        sys.exit(1)



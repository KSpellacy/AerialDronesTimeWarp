# nav/estimator.py
import math
import time


class Odometry:
    """
    Simple on-board odometry using optical flow (x_body, y_body in cm),
    yaw (deg), and height (cm). Tracks (x, y, z, theta) in a field/world frame.
    """
    def __init__(self, drone, flow_scale=1.0):
        self.drone = drone
        self.flow_scale = flow_scale  # cm per reported flow unit (tune via calibration)
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.theta_deg = 0.0
        self._last_update = None

    def zero(self):
        """Zero the pose at current location."""
        self.x = self.y = 0.0
        self.z = float(self.drone.get_height())
        self.theta_deg = float(self._get_yaw_deg_safe())
        self._last_update = time.time()

        # If your SDK has explicit flow reset/zero, call it here.
        # e.g., self.drone.reset_flow()  (placeholder)

    def _get_yaw_deg_safe(self):
        # Replace with your SDK call; common names: get_yaw(), get_gyro_angles()[2], etc.
        try:
            return float(self.drone.get_yaw())
        except AttributeError:
            gx, gy, gz = self.drone.get_gyro_angles()  # if available
            return float(gz)

    def step(self):
        """
        Read sensors once and update pose. Call at ~10–30 Hz.
        Assumes drone.get_flow_x/y() return displacement since last read (common behavior).
        If they return totals, compute diffs yourself.
        """
        # Read raw sensor data
        try:
            dx_body = float(self.drone.get_flow_x()) * self.flow_scale  # cm
            dy_body = float(self.drone.get_flow_y()) * self.flow_scale  # cm
        except Exception:
            dx_body = dy_body = 0.0

        self.z = float(self.drone.get_height())
        self.theta_deg = float(self._get_yaw_deg_safe())

        # Rotate body deltas into world frame using yaw
        theta_rad = math.radians(self.theta_deg)
        cos_t, sin_t = math.cos(theta_rad), math.sin(theta_rad)

        # Body frame convention (assumed): +Y forward, +X right (adjust as needed).
        # World frame: +Y forward from start line, +X to the right.
        dx_world =  dx_body * cos_t + dy_body * sin_t
        dy_world = -dx_body * sin_t + dy_body * cos_t

        # Accumulate
        self.x += dx_world
        self.y += dy_world

        self._last_update = time.time()

    def pose(self):
        """Return (x_cm, y_cm, z_cm, theta_deg)."""
        return self.x, self.y, self.z, self.theta_deg

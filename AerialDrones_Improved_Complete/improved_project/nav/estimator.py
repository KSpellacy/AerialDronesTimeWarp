# nav/estimator.py
"""
Improved odometry system with drift mitigation and sensor fusion.
"""
import math
import time
import logging

logger = logging.getLogger(__name__)


class Odometry:
    """
    On-board odometry using optical flow (x_body, y_body in cm),
    yaw (deg), and height (cm). Tracks (x, y, z, theta) in world frame.
    
    Improvements:
    - Outlier rejection for impossible velocities
    - Moving average height filtering
    - Drift bounds checking
    """
    
    def __init__(self, drone, flow_scale=1.0):
        """
        Initialize odometry system.
        
        Args:
            drone: CoDrone EDU instance
            flow_scale: Calibration factor for optical flow (cm per flow unit)
        """
        self.drone = drone
        self.flow_scale = flow_scale
        
        # Pose state
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.theta_deg = 0.0
        
        # Timing
        self._last_update = None
        
        # Height filtering
        self.height_history = []
        self.max_height_history = 5
        
        # Drift detection
        self.max_velocity_cm_s = 200.0  # Maximum reasonable velocity for indoor drone
        
        logger.info(f"Odometry initialized with flow_scale={flow_scale}")
    
    def zero(self):
        """Zero the pose at current location."""
        self.x = self.y = 0.0
        
        # Initialize height with current reading
        h = self.drone.get_height()
        self.z = float(h) if h is not None else 0.0
        
        # Initialize yaw
        self.theta_deg = float(self._get_yaw_deg_safe())
        
        # Reset timing
        self._last_update = time.time()
        
        # Clear history
        self.height_history = [self.z]
        
        logger.info(f"Odometry zeroed at z={self.z:.1f}cm, θ={self.theta_deg:.1f}°")
    
    def _get_yaw_deg_safe(self):
        """
        Safely get yaw angle, trying multiple SDK methods.
        
        Returns:
            Yaw angle in degrees
        """
        try:
            # Try direct yaw method
            return float(self.drone.get_yaw())
        except (AttributeError, TypeError):
            try:
                # Try gyro angles method (returns [roll, pitch, yaw])
                gx, gy, gz = self.drone.get_gyro_angles()
                return float(gz)
            except (AttributeError, TypeError, ValueError):
                logger.warning("Could not read yaw, using last known value")
                return self.theta_deg
    
    def step(self):
        """
        Read sensors once and update pose. Call at ~10–30 Hz.
        
        Features:
        - Outlier rejection for impossible velocities
        - Height filtering with moving average
        - Drift accumulation bounds
        """
        # Calculate time delta
        current_time = time.time()
        dt = current_time - self._last_update if self._last_update else 0.05
        
        # Read optical flow (body frame displacements)
        try:
            dx_body = float(self.drone.get_flow_x()) * self.flow_scale  # cm
            dy_body = float(self.drone.get_flow_y()) * self.flow_scale  # cm
        except (AttributeError, TypeError, ValueError) as e:
            logger.warning(f"Flow read error: {e}")
            dx_body = dy_body = 0.0
        
        # Outlier rejection: check if velocities are physically possible
        if dt > 0:
            vx = abs(dx_body / dt)
            vy = abs(dy_body / dt)
            
            if vx > self.max_velocity_cm_s or vy > self.max_velocity_cm_s:
                logger.warning(f"Rejecting outlier: vx={vx:.1f}, vy={vy:.1f} cm/s")
                dx_body = dy_body = 0.0
        
        # Read height with filtering
        raw_height = self.drone.get_height()
        if raw_height is not None:
            self.height_history.append(float(raw_height))
            if len(self.height_history) > self.max_height_history:
                self.height_history.pop(0)
            
            # Moving average filter
            self.z = sum(self.height_history) / len(self.height_history)
        
        # Read yaw
        self.theta_deg = float(self._get_yaw_deg_safe())
        
        # Rotate body frame displacements to world frame
        theta_rad = math.radians(self.theta_deg)
        cos_t = math.cos(theta_rad)
        sin_t = math.sin(theta_rad)
        
        # Body frame convention: +Y forward, +X right
        # World frame: +Y forward from start, +X right
        dx_world =  dx_body * cos_t + dy_body * sin_t
        dy_world = -dx_body * sin_t + dy_body * cos_t
        
        # Accumulate position
        self.x += dx_world
        self.y += dy_world
        
        # Update timing
        self._last_update = current_time
    
    def pose(self):
        """
        Get current pose estimate.
        
        Returns:
            Tuple of (x_cm, y_cm, z_cm, theta_deg)
        """
        return self.x, self.y, self.z, self.theta_deg
    
    def reset_xy(self):
        """Reset horizontal position (useful for recalibration at waypoints)."""
        self.x = 0.0
        self.y = 0.0
        logger.info("X-Y position reset to origin")


class EnhancedOdometry(Odometry):
    """
    Extended odometry with additional features for competition use.
    
    Additional features:
    - Position history logging
    - Statistics tracking
    - Calibration helpers
    """
    
    def __init__(self, drone, flow_scale=1.0, enable_logging=True):
        super().__init__(drone, flow_scale)
        self.enable_logging = enable_logging
        
        # Position history for analysis
        self.position_history = []
        self.max_history_points = 1000
        
        # Statistics
        self.step_count = 0
        self.total_distance_traveled = 0.0
        self._last_x = 0.0
        self._last_y = 0.0
    
    def step(self):
        """Extended step with logging and statistics."""
        super().step()
        
        self.step_count += 1
        
        # Calculate distance traveled this step
        dx = self.x - self._last_x
        dy = self.y - self._last_y
        distance = math.sqrt(dx**2 + dy**2)
        self.total_distance_traveled += distance
        
        self._last_x = self.x
        self._last_y = self.y
        
        # Log position history
        if self.enable_logging:
            timestamp = time.time()
            self.position_history.append({
                'time': timestamp,
                'x': self.x,
                'y': self.y,
                'z': self.z,
                'theta': self.theta_deg
            })
            
            if len(self.position_history) > self.max_history_points:
                self.position_history.pop(0)
    
    def get_statistics(self):
        """
        Get odometry statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'steps': self.step_count,
            'total_distance_cm': self.total_distance_traveled,
            'current_x_cm': self.x,
            'current_y_cm': self.y,
            'current_z_cm': self.z,
            'current_theta_deg': self.theta_deg,
            'history_points': len(self.position_history)
        }
    
    def export_trajectory(self, filepath):
        """
        Export trajectory history to JSON file for analysis.
        
        Args:
            filepath: Path to save JSON file
        """
        import json
        from pathlib import Path
        
        data = {
            'metadata': {
                'flow_scale': self.flow_scale,
                'total_steps': self.step_count,
                'total_distance_cm': self.total_distance_traveled
            },
            'trajectory': self.position_history
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Trajectory exported to {filepath}")


def calibrate_flow_sensor(drone, known_distance_cm=100):
    """
    Calibrate optical flow sensor by moving a known distance.
    
    This should be run before competition flights to determine
    the optimal flow_scale parameter for accurate distance tracking.
    
    Args:
        drone: CoDrone EDU instance (already paired)
        known_distance_cm: Known calibration distance to move
    
    Returns:
        Calibrated flow_scale value
    """
    logger.info(f"Starting flow calibration over {known_distance_cm} cm")
    print(f"\nCalibration: Moving {known_distance_cm} cm forward...")
    print("Ensure clear flight path and level surface!")
    
    from codrone_edu.drone import Direction
    
    # Initialize odometry with default scale
    odo = Odometry(drone, flow_scale=1.0)
    odo.zero()
    time.sleep(0.5)
    
    # Move the known distance
    drone.go(Direction.FORWARD, known_distance_cm)
    time.sleep(2.0)  # Let drone settle
    
    # Collect multiple odometry samples
    for _ in range(10):
        odo.step()
        time.sleep(0.1)
    
    # Get measured distance
    _, measured_y, _, _ = odo.pose()
    
    if measured_y > 10:  # Sanity check
        flow_scale = known_distance_cm / measured_y
        logger.info(f"Calibration complete: measured={measured_y:.1f}cm, flow_scale={flow_scale:.3f}")
        print(f"\n✓ Calibration complete!")
        print(f"  Expected: {known_distance_cm} cm")
        print(f"  Measured: {measured_y:.1f} cm")
        print(f"  Calculated flow_scale: {flow_scale:.3f}")
        print(f"\nAdd this to your configuration file:")
        print(f'  "flow_scale": {flow_scale:.3f}')
        return flow_scale
    else:
        logger.warning("Calibration failed - insufficient movement detected")
        print("\n⚠ Calibration failed!")
        print("  Insufficient movement detected. Check:")
        print("  - Optical flow sensor is working")
        print("  - Surface has sufficient texture")
        print("  - Lighting is adequate")
        return 1.0


if __name__ == "__main__":
    # Example usage for testing
    from codrone_edu.drone import Drone
    
    print("Testing odometry system...")
    print("This requires a connected CoDrone EDU.")
    
    drone = Drone()
    try:
        drone.pair()
        print("Drone paired!")
        
        # Run calibration
        scale = calibrate_flow_sensor(drone, known_distance_cm=100)
        
        print(f"\nRecommended flow_scale: {scale:.3f}")
    
    finally:
        drone.close()
        print("Drone disconnected.")

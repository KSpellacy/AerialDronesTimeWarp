# navigation/estimator.py
"""
Odometry estimator using optical flow sensor.
Tracks drone position in 2D space using flow velocity integration.
"""
import time
import logging

logger = logging.getLogger(__name__)


class Odometry:
    """
    Dead-reckoning position estimator using optical flow sensor.
    
    Maintains (x, y, z, theta) pose estimate by integrating flow velocities.
    Includes outlier rejection and configurable scaling.
    """
    
    def __init__(self, drone, flow_scale=1.0):
        """
        Initialize odometry estimator.
        
        Args:
            drone: Connected CoDrone EDU instance
            flow_scale: Calibration factor for flow velocities (default 1.0)
        """
        self.drone = drone
        self.flow_scale = flow_scale
        
        # Position state
        self.x = 0.0  # cm, left/right
        self.y = 0.0  # cm, forward/backward
        self.z = 0.0  # cm, altitude
        self.theta_deg = 0.0  # degrees, yaw angle
        
        # Last update time
        self.last_time = time.time()
        
        # Outlier rejection threshold (cm/s)
        self.max_velocity = 200.0
        
        logger.info(f"Odometry initialized with flow_scale={flow_scale}")
    
    def zero(self):
        """Reset position to origin, keeping current altitude and yaw."""
        self.x = 0.0
        self.y = 0.0
        self.z = self._get_altitude()
        self.theta_deg = self._get_yaw()
        self.last_time = time.time()
        logger.info(f"Odometry zeroed at z={self.z:.1f}cm, θ={self.theta_deg:.1f}°")
    
    def step(self):
        """Update position estimate using current sensor readings."""
        now = time.time()
        dt = now - self.last_time
        
        if dt < 0.001:  # Avoid division by zero
            return
        
        # Get flow velocities (using non-deprecated functions)
        try:
            vx_raw = self.drone.get_flow_velocity_x()  # cm/s, left(+)/right(-)
            vy_raw = self.drone.get_flow_velocity_y()  # cm/s, forward(+)/backward(-)
        except AttributeError:
            # Fallback to deprecated functions if new ones don't exist
            vx_raw = self.drone.get_flow_x()
            vy_raw = self.drone.get_flow_y()
        
        # Apply scaling
        vx = vx_raw * self.flow_scale if vx_raw is not None else 0.0
        vy = vy_raw * self.flow_scale if vy_raw is not None else 0.0
        
        # Outlier rejection
        if abs(vx) > self.max_velocity or abs(vy) > self.max_velocity:
            logger.warning(f"Rejecting outlier: vx={vx:.1f}, vy={vy:.1f} cm/s")
            vx = 0.0
            vy = 0.0
        
        # Update position (simple Euler integration)
        self.x += vx * dt
        self.y += vy * dt
        
        # Update altitude and yaw
        self.z = self._get_altitude()
        self.theta_deg = self._get_yaw()
        
        self.last_time = now
    
    def pose(self):
        """
        Get current pose estimate.
        
        Returns:
            tuple: (x, y, z, theta) in cm and degrees
        """
        return (self.x, self.y, self.z, self.theta_deg)
    
    def _get_altitude(self):
        """Get current altitude from height sensor."""
        h = self.drone.get_height()
        return h if h is not None else self.z
    
    def _get_yaw(self):
        """Get current yaw angle from IMU."""
        try:
            yaw = self.drone.get_pos_yaw()
            if yaw is not None:
                return float(yaw)
        except:
            pass
        
        logger.warning("Could not read yaw, using last known value")
        return self.theta_deg


def calibrate_flow_sensor(drone, known_distance_cm=100.0, num_trials=3):
    """
    Calibrate optical flow sensor by comparing measured vs actual distance.
    
    The drone will:
    1. Take off
    2. Move forward a known distance multiple times
    3. Calculate the scaling factor needed to match reality
    
    Args:
        drone: Connected CoDrone EDU instance
        known_distance_cm: Actual distance to move (default 100cm)
        num_trials: Number of calibration trials (default 3)
    
    Returns:
        float: Recommended flow_scale value
    """
    print(f"\n{'='*60}")
    print(f"OPTICAL FLOW CALIBRATION")
    print(f"{'='*60}")
    print(f"Known distance: {known_distance_cm} cm")
    print(f"Trials: {num_trials}")
    print(f"\nEnsure:")
    print("  • Clear flight path")
    print("  • Level surface below drone")
    print("  • Good lighting")
    print("  • Textured surface (not plain white/black)")
    print(f"{'='*60}\n")
    
    input("Press Enter when ready to begin calibration...")
    
    # Take off
    print("\n✈ Taking off...")
    drone.takeoff()
    time.sleep(2)
    
    scale_factors = []
    
    for trial in range(num_trials):
        print(f"\n--- Trial {trial + 1}/{num_trials} ---")
        
        # Create odometry estimator with default scale
        odo = Odometry(drone, flow_scale=1.0)
        odo.zero()
        time.sleep(0.5)
        
        # Move forward the known distance
        print(f"Moving forward {known_distance_cm} cm...")
        
        # Use set_pitch for forward movement
        move_start = time.time()
        target_time = known_distance_cm / 30.0  # Rough estimate: 30 cm/sec
        
        drone.set_pitch(30)  # Move forward at power 30
        
        # Move for estimated time while updating odometry
        while time.time() - move_start < target_time:
            odo.step()
            time.sleep(0.05)
        
        drone.set_pitch(0)  # Stop
        time.sleep(0.5)
        
        # Take final readings
        for _ in range(10):
            odo.step()
            time.sleep(0.05)
        
        # Get measured distance
        x, y, z, theta = odo.pose()
        measured_distance = y
        
        print(f"  Measured: {measured_distance:.1f} cm")
        print(f"  Actual:   {known_distance_cm:.1f} cm")
        
        if abs(measured_distance) > 1.0:  # Avoid division by zero
            scale = known_distance_cm / measured_distance
            scale_factors.append(scale)
            print(f"  Scale factor: {scale:.3f}")
        else:
            print(f"  ⚠ Invalid measurement (too small), skipping trial")
        
        # Move back to start (approximate)
        if trial < num_trials - 1:  # Don't move back on last trial
            print("  Moving back to start...")
            drone.set_pitch(-30)  # Move backward
            time.sleep(target_time)
            drone.set_pitch(0)
            time.sleep(1)
    
    # Land
    print("\n🛬 Landing...")
    drone.land()
    time.sleep(2)
    
    # Calculate final scale
    if scale_factors:
        avg_scale = sum(scale_factors) / len(scale_factors)
        std_dev = (sum((s - avg_scale)**2 for s in scale_factors) / len(scale_factors))**0.5
        
        print(f"\n{'='*60}")
        print(f"CALIBRATION RESULTS")
        print(f"{'='*60}")
        print(f"Scale factors from trials: {[f'{s:.3f}' for s in scale_factors]}")
        print(f"Average: {avg_scale:.3f}")
        print(f"Std Dev: {std_dev:.3f}")
        print(f"\n✓ Recommended flow_scale value: {avg_scale:.3f}")
        print(f"\nUpdate your config file:")
        print(f'  "tuning": {{')
        print(f'    "flow_scale": {avg_scale:.3f},')
        print(f'    ...')
        print(f'  }}')
        print(f"{'='*60}\n")
        
        logger.info(f"Calibration complete: flow_scale={avg_scale:.3f}")
        return avg_scale
    else:
        print("\n⚠ Calibration failed - no valid measurements")
        print("Try again with better lighting and textured surface")
        return 1.0


# Example usage
if __name__ == "__main__":
    from codrone_edu.drone import Drone
    
    print("Odometry Estimator - Test Mode")
    print("="*60)
    
    drone = Drone()
    drone.pair()
    
    # Run calibration
    flow_scale = calibrate_flow_sensor(drone, known_distance_cm=100.0, num_trials=3)
    
    print(f"\nCalibration complete!")
    print(f"Use flow_scale={flow_scale:.3f} in your configuration")
    
    drone.close()
# phases/autonomous_flight.py
"""
Generic waypoint-based autonomous flight controller.
Supports any course layout through JSON configuration files.
"""
import json
import time
import logging
from pathlib import Path
from codrone_edu.drone import Drone, Direction
from nav.estimator import Odometry

logger = logging.getLogger(__name__)


class WaypointNavigator:
    """Generic waypoint-based navigation for any course layout."""
    
    def __init__(self, config_path: Path):
        """Initialize navigator with course configuration."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.waypoints = self.config['waypoints']
        self.tuning = self.config.get('tuning', {})
        self.metadata = self.config.get('metadata', {})
        self.drone = None
        self.odo = None
        
        logger.info(f"Loaded config: {self.metadata.get('competition', 'Unknown')}")
        logger.info(f"Waypoints: {len(self.waypoints)}")
    
    def execute_flight(self):
        """Execute full autonomous flight based on waypoints."""
        self.drone = Drone()
        
        try:
            logger.info("Pairing drone...")
            print("Pairing drone...")
            self.drone.pair()
            
            # Initialize odometry with config parameters
            flow_scale = self.tuning.get('flow_scale', 1.0)
            self.odo = Odometry(self.drone, flow_scale=flow_scale)
            
            # Process each waypoint sequentially
            cumulative_distance = 0.0
            
            for i, waypoint in enumerate(self.waypoints):
                wp_id = waypoint.get('id', f'waypoint_{i}')
                logger.info(f"Processing waypoint {i}: {wp_id}")
                print(f"\n--- Waypoint {i}: {wp_id} ---")
                
                action = waypoint.get('action', '')
                
                if action == 'takeoff':
                    self._execute_takeoff()
                
                elif action == 'pass_through':
                    self._execute_pass_through(waypoint, cumulative_distance)
                    cumulative_distance += waypoint.get('distance_from_previous_cm', 0)
                
                elif action == 'land':
                    cumulative_distance += waypoint.get('distance_from_previous_cm', 0)
                    self._execute_landing(waypoint, cumulative_distance)
                
                else:
                    logger.warning(f"Unknown action: {action}")
            
            logger.info("Flight sequence complete!")
            print("\n✓ Flight complete!")
        
        except Exception as e:
            logger.error(f"Flight error: {e}", exc_info=True)
            raise
        
        finally:
            if self.drone:
                self.drone.close()
                logger.info("Drone disconnected")
                print("Drone disconnected.")
    
    def _execute_takeoff(self):
        """Execute takeoff and initialize odometry."""
        print("Takeoff")
        self.drone.takeoff()
        time.sleep(0.8)
        
        # Initialize odometry at start position
        self.odo.zero()
        self.odo.step()
        
        x, y, z, theta = self.odo.pose()
        logger.info(f"Takeoff complete. Pose: x={x:.1f}, y={y:.1f}, z={z:.1f}, θ={theta:.1f}")
    
    def _execute_pass_through(self, waypoint, cumulative_distance):
        """Execute gate pass-through maneuver."""
        target_height = waypoint.get('height_cm', 0)
        distance = waypoint.get('distance_from_previous_cm', 0)
        wp_id = waypoint.get('id', 'gate')
        
        # Rise to gate height
        print(f"Rising to {target_height} cm")
        logger.info(f"Rising to {target_height} cm for {wp_id}")
        success = self._rise_to_height(target_height)
        
        if not success:
            logger.warning(f"Height timeout for {wp_id}")
        
        # Move forward to gate
        target_forward = cumulative_distance + distance
        print(f"Moving forward {distance} cm to {wp_id}")
        logger.info(f"Moving to forward position: {target_forward} cm")
        self._go_forward_until(target_forward)
        
        # Pass through gate
        print(f"Passing through {wp_id}...")
        self.drone.go(Direction.FORWARD, 20)
        time.sleep(0.2)
        self.odo.step()
        
        x, y, z, theta = self.odo.pose()
        logger.info(f"Passed {wp_id}. Pose: x={x:.1f}, y={y:.1f}, z={z:.1f}")
    
    def _execute_landing(self, waypoint, cumulative_distance):
        """Execute approach and landing sequence."""
        distance = waypoint.get('distance_from_previous_cm', 0)
        target_height = waypoint.get('height_cm', 0)
        wp_id = waypoint.get('id', 'target')
        
        # Move to target location
        print(f"Moving forward {distance} cm to {wp_id}")
        logger.info(f"Approaching {wp_id} at forward: {cumulative_distance} cm")
        self._go_forward_until(cumulative_distance)
        
        # Descend to landing height
        print(f"Descending to {target_height} cm")
        logger.info(f"Descending to landing height: {target_height} cm")
        self._rise_to_height(target_height)
        time.sleep(0.2)
        self.odo.step()
        
        x, y, z, theta = self.odo.pose()
        logger.info(f"At {wp_id}. Final pose: x={x:.1f}, y={y:.1f}, z={z:.1f}")
        
        # Land
        print("Landing...")
        logger.info("Executing landing")
        self.drone.land()
        time.sleep(0.5)
    
    def _rise_to_height(self, target_cm):
        """
        Rise or descend to target height with improved stability.
        Returns True if successful, False if timeout.
        """
        tolerance = self.tuning.get('height_tolerance_cm', 6)
        timeout = self.tuning.get('height_timeout_sec', 6)
        
        start = time.time()
        time.sleep(0.2)  # Initial settle time
        
        while time.time() - start < timeout:
            # Take multiple samples for stability
            heights = []
            for _ in range(3):
                h = self.drone.get_height()
                if h is not None:
                    heights.append(h)
                time.sleep(0.02)
            
            if not heights:
                continue
            
            current = sum(heights) / len(heights)
            diff = target_cm - current
            
            logger.debug(f"Height: current={current:.1f}, target={target_cm}, diff={diff:.1f}")
            
            if abs(diff) <= tolerance:
                self.drone.hover(0.3)
                logger.info(f"Reached target height: {current:.1f} cm")
                return True
            
            # Calculate movement step
            step = min(20, abs(diff))
            if diff > 0:
                self.drone.go(Direction.UP, step)
            else:
                self.drone.go(Direction.DOWN, step)
            
            time.sleep(0.15)
        
        logger.warning(f"Height control timeout. Target={target_cm}, Current≈{current:.1f}")
        return False
    
    def _go_forward_until(self, target_forward_cm):
        """
        Move forward using odometry until target distance is reached.
        Includes drift protection through position snapping.
        """
        fwd_chunk = self.tuning.get('forward_chunk_cm', 30)
        stop_eps = self.tuning.get('forward_stop_epsilon_cm', 5.0)
        
        while True:
            self.odo.step()
            x, y, z, theta = self.odo.pose()
            
            remaining = target_forward_cm - y
            
            logger.debug(f"Forward: y={y:.1f}, target={target_forward_cm:.1f}, remaining={remaining:.1f}")
            
            if remaining <= stop_eps:
                # Snap to exact distance to prevent drift accumulation
                self.odo.y = float(target_forward_cm)
                logger.info(f"Reached forward target: {target_forward_cm:.1f} cm")
                break
            
            # Adaptive chunk size - slow down near target
            if remaining < 50:
                chunk = min(10, remaining)
            elif remaining < 100:
                chunk = min(20, remaining)
            else:
                chunk = fwd_chunk
            
            self.drone.go(Direction.FORWARD, int(chunk))
            time.sleep(0.05)
            
            # Multiple estimator steps while drone settles
            for _ in range(3):
                time.sleep(0.03)
                self.odo.step()


def run(config_path=None):
    """
    Main entry point for autonomous flight.
    
    Args:
        config_path: Path to JSON configuration file. 
                    Defaults to data/phase1_params.json for backward compatibility.
    """
    if config_path is None:
        config_path = Path("data/phase1_params.json")
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}\n"
                              "Run the recorder first to create configuration.")
    
    # Setup logging
    from datetime import datetime
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"flight_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger.info(f"Starting autonomous flight with config: {config_path}")
    
    try:
        navigator = WaypointNavigator(config_path)
        navigator.execute_flight()
    except Exception as e:
        logger.error(f"Flight failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run()

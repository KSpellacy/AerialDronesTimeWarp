# phases/autonomous_flight_hybrid_v2.py
"""
Hybrid autonomous flight controller using time-based navigation.
FIXED VERSION - Uses correct CoDrone EDU movement API
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


import json
import time
import logging
from codrone_edu.drone import Drone

logger = logging.getLogger(__name__)


class HybridWaypointNavigator:
    """
    Time-based waypoint navigation with precise height control.
    Optimized for repeatability and competition performance.
    """

    def __init__(self, config_path: Path):
        """Initialize navigator with course configuration."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.waypoints = self.config['waypoints']
        self.tuning = self.config.get('tuning', {})
        self.metadata = self.config.get('metadata', {})
        self.drone = None

        # Time-based navigation parameters
        self.cm_per_second = self.tuning.get('cm_per_second', 30.0)
        self.forward_power = self.tuning.get('forward_power', 30)

        logger.info(f"Loaded config: {self.metadata.get('competition', 'Unknown')}")
        logger.info(f"Waypoints: {len(self.waypoints)}")
        logger.info(f"Time-based navigation: {self.cm_per_second} cm/s at power {self.forward_power}")

    def execute_flight(self):
        """Execute full autonomous flight based on waypoints."""
        self.drone = Drone()

        try:
            logger.info("Pairing drone...")
            print("Pairing drone...")
            self.drone.pair()

            battery = self.drone.get_battery()
            print(f"Battery: {battery}%")
            logger.info(f"Battery: {battery}%")

            if battery < 30:
                print("⚠ Warning: Low battery! Consider charging before flight.")
                input("Press Enter to continue anyway, or Ctrl+C to abort...")

            # Process each waypoint sequentially
            for i, waypoint in enumerate(self.waypoints):
                wp_id = waypoint.get('id', f'waypoint_{i}')
                logger.info(f"Processing waypoint {i}: {wp_id}")
                print(f"\n{'=' * 60}")
                print(f"Waypoint {i}: {wp_id}")
                print(f"{'=' * 60}")

                action = waypoint.get('action', '')

                if action == 'takeoff':
                    self._execute_takeoff(waypoint)

                elif action == 'pass_through':
                    self._execute_pass_through(waypoint)

                elif action == 'land':
                    self._execute_landing(waypoint)

                elif action == 'hover':
                    self._execute_hover(waypoint)

                else:
                    logger.warning(f"Unknown action: {action}")
                    print(f"⚠ Unknown action: {action}")

            logger.info("Flight sequence complete!")
            print(f"\n{'=' * 60}")
            print("✓ Flight complete!")
            print(f"{'=' * 60}")

        except KeyboardInterrupt:
            print("\n⚠ Flight interrupted by user")
            logger.warning("Flight interrupted by user")
            self.drone.emergency_stop()
            time.sleep(1)

        except Exception as e:
            logger.error(f"Flight error: {e}", exc_info=True)
            print(f"\n✗ Error: {e}")
            raise

        finally:
            if self.drone:
                self.drone.close()
                logger.info("Drone disconnected")
                print("Drone disconnected.")

    def _execute_takeoff(self, waypoint):
        """Execute takeoff to initial height."""
        initial_height = waypoint.get('height_cm', 80)

        print(f"Taking off to {initial_height} cm...")
        logger.info(f"Takeoff to {initial_height} cm")

        self.drone.takeoff()
        time.sleep(2)  # Allow stabilization

        # Adjust to target height
        success = self._rise_to_height(initial_height)

        if success:
            print(f"✓ At takeoff height: {initial_height} cm")
        else:
            print(f"⚠ Height adjustment timeout")

        # Brief hover for stabilization
        self.drone.hover(0.5)

        current_height = self.drone.get_height()
        logger.info(f"Takeoff complete at {current_height} cm")

    def _execute_pass_through(self, waypoint):
        """Execute gate pass-through maneuver."""
        target_height = waypoint.get('height_cm', 100)
        distance = waypoint.get('distance_from_previous_cm', 200)
        wp_id = waypoint.get('id', 'gate')

        print(f"\nApproaching {wp_id}...")

        # Step 1: Adjust to gate height
        print(f"  → Rising to {target_height} cm")
        logger.info(f"Adjusting to gate height: {target_height} cm for {wp_id}")
        success = self._rise_to_height(target_height)

        if not success:
            logger.warning(f"Height timeout for {wp_id}")
            print(f"  ⚠ Height timeout (continuing anyway)")
        else:
            print(f"  ✓ At gate height")

        # Brief stabilization
        self.drone.hover(0.3)

        # Step 2: Move forward to gate
        print(f"  → Moving forward {distance} cm")
        logger.info(f"Moving forward {distance} cm to {wp_id}")
        self._move_forward_time_based(distance)

        # Brief stabilization after passing through
        self.drone.hover(0.3)

        current_height = self.drone.get_height()
        print(f"✓ Passed through {wp_id} (height: {current_height} cm)")
        logger.info(f"Passed {wp_id} at height {current_height} cm")

    def _execute_landing(self, waypoint):
        """Execute approach and landing sequence."""
        distance = waypoint.get('distance_from_previous_cm', 150)
        landing_height = waypoint.get('height_cm', 50)
        wp_id = waypoint.get('id', 'target')

        print(f"\nApproaching landing target...")

        # Step 1: Move to landing zone
        print(f"  → Moving forward {distance} cm to {wp_id}")
        logger.info(f"Approaching {wp_id}, distance: {distance} cm")
        self._move_forward_time_based(distance)

        # Brief stabilization
        self.drone.hover(0.5)

        # Step 2: Descend to landing height
        print(f"  → Descending to {landing_height} cm")
        logger.info(f"Descending to landing height: {landing_height} cm")
        success = self._rise_to_height(landing_height)

        if not success:
            print(f"  ⚠ Descent timeout (continuing to land)")
        else:
            print(f"  ✓ At landing height")

        # Brief stabilization
        self.drone.hover(0.5)

        # Step 3: Final landing
        print(f"  → Landing...")
        logger.info("Executing landing")
        self.drone.land()
        time.sleep(2)

        print(f"✓ Landed at {wp_id}")
        logger.info(f"Landing complete at {wp_id}")

    def _execute_hover(self, waypoint):
        """Execute hover at current position."""
        duration = waypoint.get('duration_sec', 1.0)
        wp_id = waypoint.get('id', 'hover')

        print(f"\nHovering for {duration} seconds...")
        logger.info(f"Hovering at {wp_id} for {duration} sec")

        self.drone.hover(duration)

        print(f"✓ Hover complete")

    def _rise_to_height(self, target_cm):
        """
        Adjust to target height using height sensor.
        Most reliable sensor on CoDrone EDU.

        Returns:
            bool: True if successful, False if timeout
        """
        tolerance = self.tuning.get('height_tolerance_cm', 5)
        timeout = self.tuning.get('height_timeout_sec', 10)
        throttle_power = self.tuning.get('throttle_power', 25)

        start = time.time()
        time.sleep(0.2)  # Initial settle time

        while time.time() - start < timeout:
            # Take multiple height samples for stability
            heights = []
            for _ in range(3):
                h = self.drone.get_height()
                if h is not None and h < 500:  # Filter out invalid readings (999.9)
                    heights.append(h)
                time.sleep(0.02)

            if not heights:
                logger.warning("No valid height readings")
                continue

            current = sum(heights) / len(heights)
            diff = target_cm - current

            logger.debug(f"Height: {current:.1f} cm, target: {target_cm} cm, diff: {diff:.1f} cm")

            # Check if within tolerance
            if abs(diff) <= tolerance:
                self.drone.hover(0.3)
                logger.info(f"Reached target height: {current:.1f} cm")
                return True

            # Calculate throttle power (proportional control)
            if abs(diff) > 20:
                power = throttle_power
            elif abs(diff) > 10:
                power = int(throttle_power * 0.7)
            else:
                power = int(throttle_power * 0.5)

            # Apply throttle
            if diff > 0:
                # Move up
                self.drone.set_throttle(power)
                time.sleep(0.1)
                self.drone.set_throttle(0)
            else:
                # Move down
                self.drone.set_throttle(-power)
                time.sleep(0.1)
                self.drone.set_throttle(0)

            time.sleep(0.15)

        current = self.drone.get_height()
        logger.warning(f"Height timeout. Target: {target_cm}, Current: {current} cm")
        return False

    def _move_forward_time_based(self, distance_cm):
        """
        Move forward using time-based navigation with CONTINUOUS pitch control.
        CoDrone EDU requires continuous commands, not single set/reset.

        Args:
            distance_cm: Distance to travel in centimeters
        """
        # Calculate travel time
        travel_time = distance_cm / self.cm_per_second

        logger.info(f"Time-based forward: {distance_cm} cm at {self.cm_per_second} cm/s = {travel_time:.2f} sec")

        # Use continuous control loop
        start = time.time()
        update_interval = 0.1  # Send command every 100ms

        while time.time() - start < travel_time:
            # Continuously send pitch command
            self.drone.set_pitch(self.forward_power)
            time.sleep(update_interval)

        # Stop movement
        self.drone.set_pitch(0)
        time.sleep(0.2)  # Allow drone to settle

        logger.info(f"Forward movement complete: {distance_cm} cm")


def run(config_path=None):
    """
    Main entry point for hybrid autonomous flight.

    Args:
        config_path: Path to JSON configuration file
    """
    if config_path is None:
        config_path = Path("data/phase1_params.json")

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}\n"
                                "Create a configuration file first.")

    # Setup logging
    from datetime import datetime
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"flight_hybrid_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logger.info(f"Starting hybrid autonomous flight with config: {config_path}")

    try:
        navigator = HybridWaypointNavigator(config_path)
        navigator.execute_flight()
    except Exception as e:
        logger.error(f"Flight failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run()
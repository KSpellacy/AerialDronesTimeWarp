#!/usr/bin/env python3
"""
Mission 2026: Time Warp - Autonomous Flight Mission
REC Aerial Drone Competition 2025/2026

** TIME-BASED NAVIGATION VERSION **
Uses calibrated cm_per_second like calibrate_hybrid.py
More reliable than position estimation!

** FIXED HEIGHT CONTROL **
Now uses continuous throttle feedback loop instead of time-based vertical movement.

Usage:
    python autonomous_mission_time_based.py

Requirements:
    - CoDrone EDU library installed
    - mission_2026_autonomous_waypoints.json in same directory
    - Run calibration first to get cm_per_second value
"""

import json
import time
import sys
import math
from pathlib import Path

try:
    from codrone_edu.drone import Drone
except ImportError:
    print("ERROR: CoDrone EDU library not found!")
    print("Install with: pip install codrone-edu")
    sys.exit(1)


class TimeBasedAutonomousMission:
    """
    Autonomous drone mission using TIME-BASED navigation.
    Like calibrate_hybrid.py: set_pitch() then move(duration)
    """

    def __init__(self, json_file='data/Mission26AutonWapointsV1.json'):
        """Initialize mission with JSON waypoints file"""
        self.json_file = json_file
        self.drone = None
        self.mission_data = None
        self.waypoints = []
        self.start_time = None
        self.current_waypoint_index = 0

        # TIME-BASED NAVIGATION PARAMETERS (from calibration)
        # Default values - should be calibrated for your drone
        self.cm_per_second = 35.0  # Calibrate this! Run calibrate_hybrid.py
        self.forward_power = 30  # Power used during calibration
        self.throttle_power = 25  # For vertical movement
        self.turn_power = 30  # For yaw rotation

        # Current estimated position (in inches)
        self.current_position = {'x': 0, 'y': 0, 'z': 0}

    def load_mission(self):
        """Load mission data from JSON file"""
        try:
            json_path = Path(self.json_file)
            if not json_path.exists():
                print(f"ERROR: File not found: {self.json_file}")
                print(f"Current directory: {Path.cwd()}")
                return False

            with open(self.json_file, 'r') as f:
                self.mission_data = json.load(f)

            self.waypoints = self.mission_data.get('waypoints', [])

            if not self.waypoints:
                print("ERROR: No waypoints found in JSON file")
                return False

            # Check for tuning parameters in JSON
            tuning = self.mission_data.get('tuning', {})
            if tuning:
                self.cm_per_second = tuning.get('cm_per_second', self.cm_per_second)
                self.forward_power = tuning.get('forward_power', self.forward_power)
                self.throttle_power = tuning.get('throttle_power', self.throttle_power)
                print(f"✓ Loaded tuning: {self.cm_per_second:.1f} cm/s @ power {self.forward_power}")
            else:
                print(f"⚠️  Using default tuning: {self.cm_per_second:.1f} cm/s")
                print(f"   Run calibrate_hybrid.py to get accurate values!")

            print(f"✓ Loaded mission: {self.mission_data.get('mission', 'Unknown')}")
            print(f"✓ Waypoints: {len(self.waypoints)}")
            print(
                f"✓ Estimated duration: {self.mission_data.get('timing_analysis', {}).get('total_estimated_duration', '?')} seconds")
            return True

        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON file: {e}")
            return False
        except Exception as e:
            print(f"ERROR loading mission: {e}")
            return False

    def connect_drone(self):
        """Initialize and pair with CoDrone"""
        try:
            print("\nConnecting to drone...")
            self.drone = Drone()
            self.drone.pair()
            battery = self.drone.get_battery()
            print(f"✓ Drone connected successfully - Battery: {battery}%")

            if battery < 40:
                print("⚠️  Warning: Low battery may affect performance")
                print("   Height control needs >60% battery for reliability")

            time.sleep(1)
            return True
        except Exception as e:
            print(f"ERROR connecting to drone: {e}")
            return False

    def inches_to_cm(self, inches):
        """Convert inches to centimeters"""
        return inches * 2.54

    def cm_to_inches(self, cm):
        """Convert centimeters to inches"""
        return cm / 2.54

    def calculate_move_time(self, distance_cm, power=None):
        """
        Calculate how long to move based on distance and calibrated speed.

        Args:
            distance_cm: Distance to travel in centimeters
            power: Power setting (uses forward_power if None)

        Returns:
            float: Time in seconds to move
        """
        if power is None:
            power = self.forward_power

        # Adjust speed based on power ratio
        speed_ratio = power / self.forward_power
        effective_speed = self.cm_per_second * speed_ratio

        if effective_speed == 0:
            return 0

        return distance_cm / effective_speed

    def move_time_based(self, pitch=0, roll=0, throttle=0, yaw=0, duration=0):
        """
        Move drone for specific duration with given controls.
        This is the key function like in calibrate_hybrid.py

        NOTE: Only use this for horizontal movement (pitch/roll/yaw).
        For vertical movement, use move_to_height_continuous() instead.

        Args:
            pitch: Forward/backward power (-100 to 100)
            roll: Left/right power (-100 to 100)
            throttle: Up/down power (-100 to 100) - AVOID, use move_to_height_continuous
            yaw: Rotation power (-100 to 100)
            duration: How long to move in seconds
        """
        if duration <= 0:
            return

        # Set controls
        self.drone.set_pitch(pitch)
        self.drone.set_roll(roll)
        self.drone.set_yaw(yaw)
        self.drone.set_throttle(throttle)

        # CRITICAL: Move for the specified duration
        # This is exactly like calibrate_hybrid.py
        self.drone.move(duration)

        # Stop movement
        self.drone.set_pitch(0)
        self.drone.set_roll(0)
        self.drone.set_yaw(0)
        self.drone.set_throttle(0)

    def get_hybrid_height(self):
        """
        Get height using hybrid sensor approach.
        - Below 120cm: Use bottom range sensor
        - Above 120cm or invalid: Use estimated height from throttle commands
        """
        SENSOR_MAX = 120  # cm - where bottom range becomes unreliable

        try:
            bottom_height = self.drone.get_height()

            # Check for invalid readings
            if bottom_height is None or bottom_height > 900 or bottom_height <= 0:
                # Sensor failed - use estimated height from position tracking
                estimated = self.inches_to_cm(self.current_position['z'])
                print(f"    (Sensor invalid: {bottom_height}, using estimate: {estimated:.1f}cm)")
                return estimated

            # If below sensor max, trust it
            if bottom_height < SENSOR_MAX:
                return bottom_height

            # Above sensor max - use estimated height
            estimated = self.inches_to_cm(self.current_position['z'])
            return estimated

        except Exception as e:
            # Sensor error - use estimate
            estimated = self.inches_to_cm(self.current_position['z'])
            return estimated

    def move_to_height_continuous(self, target_height_cm, max_attempts=2):
        """
        ** NEW HEIGHT CONTROL METHOD **

        Move to target height using CONTINUOUS THROTTLE with feedback loop.
        Uses hybrid height sensing for reliability.

        Args:
            target_height_cm: Target height in centimeters
            max_attempts: Maximum attempts if timeout occurs

        Returns:
            bool: True if reached target height
        """
        print(f"  → Target height: {target_height_cm}cm")

        # Adjust tolerance based on target height
        if target_height_cm > 100:
            TOLERANCE = 15  # cm - larger tolerance for high altitudes
            print(f"    (High altitude mode: ±{TOLERANCE}cm tolerance)")
        else:
            TOLERANCE = 5  # cm - tighter tolerance for low altitudes

        TIMEOUT = 20  # seconds - longer for high altitudes
        MIN_MOVE_TIME = 0.2  # Minimum time between adjustments

        for attempt in range(max_attempts):
            start_time = time.time()
            time.sleep(0.3)  # Initial settle

            consecutive_good = 0
            required_consecutive = 3  # Need 3 good readings
            last_print_time = 0

            while time.time() - start_time < TIMEOUT:
                # Get current height using hybrid method
                current_height = self.get_hybrid_height()
                diff = target_height_cm - current_height

                # Debug output every 1.5 seconds
                current_time = time.time() - start_time
                if current_time - last_print_time >= 1.5:
                    print(f"    Height: {current_height:.1f}cm (target: {target_height_cm}cm, diff: {diff:.1f}cm)")
                    last_print_time = current_time

                # Check if at target
                if abs(diff) <= TOLERANCE:
                    consecutive_good += 1
                    if consecutive_good >= required_consecutive:
                        print(f"  ✓ Reached {current_height:.1f}cm (target: {target_height_cm}cm)")
                        self.drone.set_throttle(0)
                        time.sleep(0.5)

                        # Update position estimate
                        self.current_position['z'] = self.cm_to_inches(target_height_cm)
                        return True
                    # Close to target - use minimal power
                    power = int(self.throttle_power * 0.3)
                else:
                    consecutive_good = 0

                    # Calculate power based on error (adaptive control)
                    if abs(diff) > 50:
                        power = self.throttle_power  # Full power for large errors
                    elif abs(diff) > 25:
                        power = int(self.throttle_power * 0.7)  # 70% power
                    elif abs(diff) > 10:
                        power = int(self.throttle_power * 0.5)  # 50% power
                    else:
                        power = int(self.throttle_power * 0.35)  # Gentle for fine adjustment

                # Apply throttle in correct direction
                if diff > 0:
                    self.drone.set_throttle(power)  # Go UP
                else:
                    self.drone.set_throttle(-power)  # Go DOWN

                # Move briefly then check again
                time.sleep(MIN_MOVE_TIME)

                # Update position estimate based on throttle
                throttle_speed = (power / self.throttle_power) * self.cm_per_second * 0.7  # 70% efficiency for vertical
                height_change_cm = throttle_speed * MIN_MOVE_TIME
                if diff > 0:
                    self.current_position['z'] += self.cm_to_inches(height_change_cm)
                else:
                    self.current_position['z'] -= self.cm_to_inches(height_change_cm)

            # Timeout occurred
            print(f"  ⚠ Attempt {attempt + 1} timed out, retrying...")
            self.drone.set_throttle(0)
            time.sleep(0.5)

        # Failed after all attempts
        current_height = self.get_hybrid_height()
        print(f"  ⚠ Height control failed: at {current_height:.1f}cm, target was {target_height_cm}cm")
        print(f"    Continuing with current height...")
        self.drone.set_throttle(0)

        # Update position to current height even if failed
        self.current_position['z'] = self.cm_to_inches(current_height)
        return False

    def update_position_time_based(self, pitch, roll, throttle, duration):
        """
        Update estimated position based on time-based movement.

        Args:
            pitch: Forward power used
            roll: Sideways power used
            throttle: Vertical power used
            duration: How long the movement lasted
        """
        # Calculate actual distance moved
        pitch_speed = (pitch / self.forward_power) * self.cm_per_second
        roll_speed = (roll / self.forward_power) * self.cm_per_second
        throttle_speed = (throttle / self.throttle_power) * self.cm_per_second

        # Update position (convert cm to inches)
        self.current_position['x'] += (pitch_speed * duration) / 2.54
        self.current_position['y'] += (roll_speed * duration) / 2.54
        self.current_position['z'] += (throttle_speed * duration) / 2.54

    def execute_takeoff(self, waypoint):
        """Execute takeoff waypoint"""
        print("  → Taking off...")
        self.drone.takeoff()
        time.sleep(3)  # Stable hover

        # Update estimated position to takeoff height
        # Typically 50-60cm after takeoff
        try:
            actual_height = self.drone.get_height()
            self.current_position['z'] = self.cm_to_inches(actual_height)
            print(f"  ✓ Takeoff complete - altitude: {actual_height:.1f}cm")
        except:
            # Fallback if sensor fails
            self.current_position['z'] = waypoint['position']['z']
            print(f"  ✓ Takeoff complete - estimated altitude: {waypoint['position']['z']}\"")

        return True

    def execute_navigate(self, waypoint):
        """
        Execute navigation waypoint using TIME-BASED movement.
        Like calibrate_hybrid.py: calculate time, set_pitch(), then move(time)

        ** UPDATED: Now uses move_to_height_continuous() for vertical movement **
        """
        pos = waypoint['position']
        task = waypoint['task']

        print(f"  → Navigating to: x={pos['x']}\", y={pos['y']}\", z={pos['z']}\"")

        # Determine if precision mode needed
        precision_mode = any(keyword in task for keyword in
                             ['SMALL_HOLE', 'BULLSEYE', 'TUNNEL', 'KEYHOLE'])

        # Power settings
        if precision_mode:
            forward_power = 25  # Slower for precision
            throttle_power = 20
            print("    (Precision mode: slow speed)")
        else:
            forward_power = self.forward_power
            throttle_power = self.throttle_power

        try:
            # Calculate distances to target (in cm)
            dx = self.inches_to_cm(pos['x'] - self.current_position['x'])
            dy = self.inches_to_cm(pos['y'] - self.current_position['y'])
            dz = self.inches_to_cm(pos['z'] - self.current_position['z'])

            print(f"    Distances: dx={dx:.1f}cm, dy={dy:.1f}cm, dz={dz:.1f}cm")

            # PHASE 1: VERTICAL MOVEMENT FIRST (using new continuous method)
            if abs(dz) > 5:  # Only if significant height change
                target_height_cm = self.inches_to_cm(pos['z'])
                print(f"  → Phase 1: Adjusting height to {target_height_cm:.1f}cm")

                success = self.move_to_height_continuous(target_height_cm)

                if success:
                    self.current_position['z'] = pos['z']
                else:
                    print("  ⚠ Height adjustment incomplete, continuing anyway...")

                time.sleep(0.5)  # Extra stabilization after height change

            # PHASE 2: HORIZONTAL MOVEMENT (existing time-based method works great)
            if abs(dx) > 2 or abs(dy) > 2:  # Only if significant horizontal movement
                print(f"  → Phase 2: Horizontal movement")

                # Calculate horizontal distance and angle
                horizontal_distance = math.sqrt(dx ** 2 + dy ** 2)

                if horizontal_distance > 2:
                    # Calculate target heading
                    target_angle = math.atan2(dy, dx) * 180 / math.pi
                    print(f"    Target heading: {target_angle:.1f}°, distance: {horizontal_distance:.1f}cm")

                    # Yaw rotation if needed (simplified - assumes forward motion)
                    # For full implementation, add yaw rotation logic here

                    # Calculate movement time
                    forward_time = self.calculate_move_time(horizontal_distance, forward_power)

                    print(f"    Moving forward {horizontal_distance:.1f}cm for {forward_time:.2f}s")

                    # Execute forward movement
                    self.move_time_based(pitch=forward_power, duration=forward_time)

                    # Update position
                    self.current_position['x'] = pos['x']
                    self.current_position['y'] = pos['y']

                    time.sleep(0.3)  # Stabilize

            # PHASE 3: PRECISION ADJUSTMENTS (if in precision mode)
            if precision_mode:
                print("    Final precision positioning...")
                time.sleep(0.5)

                # Re-check height
                try:
                    current_height = self.drone.get_height()
                    target_height = self.inches_to_cm(pos['z'])
                    if abs(current_height - target_height) > 8:
                        print(f"    Correcting height: {current_height:.1f} → {target_height:.1f}cm")
                        self.move_to_height_continuous(target_height)
                except:
                    pass

        except Exception as e:
            print(f"  ✗ Navigation error: {e}")
            self.drone.set_pitch(0)
            self.drone.set_roll(0)
            self.drone.set_yaw(0)
            self.drone.set_throttle(0)
            return False

        print(f"  ✓ Completed: {task}")
        return True

    def execute_sensor_read(self, waypoint):
        """
        Execute sensor reading waypoint (e.g., color detection)
        Uses time-based navigation to reach position first
        """
        pos = waypoint['position']

        print("  → Moving to sensor reading position...")

        # Use navigation to reach sensor position
        if not self.execute_navigate(waypoint):
            return False

        # Read sensor
        print("  → Reading color sensor...")
        time.sleep(1)  # Additional stabilization

        try:
            # Attempt to read color (method depends on CoDrone version)
            # color_data = self.drone.get_color_data()
            # print(f"  ✓ Color detected: {color_data}")
            print("  ⚠ Color sensor reading - implement based on your drone model")
        except Exception as e:
            print(f"  ⚠ Color sensor error: {e}")

        return True

    def execute_landing(self, waypoint):
        """Execute landing waypoint"""
        pos = waypoint['position']

        print("  → Beginning landing sequence...")

        # If bullseye landing, add precision positioning
        if 'bullseye' in waypoint.get('description', '').lower():
            print("    Precision positioning over bullseye...")

            # Navigate to position just above landing pad
            landing_waypoint = waypoint.copy()
            landing_waypoint['duration_estimate'] = 1

            hover_height_inches = 6
            hover_height_cm = self.inches_to_cm(hover_height_inches)

            print(f"    Hovering at {hover_height_cm:.1f}cm before landing")
            self.move_to_height_continuous(hover_height_cm)

            time.sleep(1)  # Extra stabilization over bullseye

        # Ensure stopped before landing
        self.drone.set_pitch(0)
        self.drone.set_roll(0)
        self.drone.set_yaw(0)
        self.drone.set_throttle(0)
        time.sleep(0.5)

        print("  → Landing...")
        self.drone.land()
        time.sleep(2)

        print("  ✓ Landing complete")
        return True

    def execute_waypoint(self, waypoint):
        """Execute a single waypoint based on its action type"""
        wp_id = waypoint['id']
        task = waypoint['task']
        action = waypoint['action']

        print(f"\n[Waypoint {wp_id}] {task}")
        print(f"  Action: {action}")
        print(f"  Description: {waypoint.get('description', 'N/A')}")

        try:
            if action == 'takeoff':
                return self.execute_takeoff(waypoint)

            elif action == 'navigate':
                return self.execute_navigate(waypoint)

            elif action == 'sensor_read':
                return self.execute_sensor_read(waypoint)

            elif action == 'land':
                return self.execute_landing(waypoint)

            else:
                print(f"  ⚠ Unknown action type: {action}")
                return False

        except Exception as e:
            print(f"  ✗ ERROR executing waypoint: {e}")
            self.drone.set_pitch(0)
            self.drone.set_roll(0)
            self.drone.set_yaw(0)
            self.drone.set_throttle(0)
            return False

    def run_mission(self):
        """Execute complete autonomous mission with time-based navigation"""
        print("\n" + "=" * 70)
        print(f"  MISSION: {self.mission_data.get('mission', 'Unknown')}")
        print(f"  Waypoints: {len(self.waypoints)}")
        print(f"  Navigation: TIME-BASED (like calibrate_hybrid.py)")
        print(f"  Height Control: CONTINUOUS FEEDBACK (FIXED)")
        print(f"  Speed: {self.cm_per_second:.1f} cm/s @ power {self.forward_power}")
        print(f"  Max Duration: {self.mission_data.get('duration_seconds', 180)} seconds")
        print("=" * 70)

        input("\nPress ENTER to start mission (Ctrl+C to abort)...")

        self.start_time = time.time()
        completed_waypoints = 0

        try:
            for i, waypoint in enumerate(self.waypoints):
                self.current_waypoint_index = i

                # Execute waypoint
                success = self.execute_waypoint(waypoint)

                if success:
                    completed_waypoints += 1
                    elapsed = time.time() - self.start_time
                    print(f"  ⏱ Elapsed time: {elapsed:.1f}s")
                else:
                    print(f"\n✗ Mission failed at waypoint {i + 1}")
                    print("  Attempting emergency landing...")
                    try:
                        self.drone.land()
                    except:
                        pass
                    return False

            # Mission complete
            total_time = time.time() - self.start_time
            print("\n" + "=" * 70)
            print("  ✓ MISSION COMPLETE!")
            print(f"  Waypoints completed: {completed_waypoints}/{len(self.waypoints)}")
            print(f"  Total time: {total_time:.1f} seconds")
            print(f"  Time remaining: {180 - total_time:.1f} seconds")
            print("=" * 70)
            return True

        except KeyboardInterrupt:
            print("\n\n✗ Mission interrupted by user!")
            print("  Executing emergency stop...")
            try:
                self.drone.set_pitch(0)
                self.drone.set_roll(0)
                self.drone.set_yaw(0)
                self.drone.set_throttle(0)
                self.drone.emergency_stop()
            except:
                pass
            return False

        except Exception as e:
            print(f"\n\n✗ Mission failed with error: {e}")
            print("  Executing emergency stop...")
            try:
                self.drone.emergency_stop()
            except:
                pass
            return False

    def cleanup(self):
        """Clean up drone connection"""
        if self.drone:
            try:
                print("\nClosing drone connection...")
                self.drone.close()
                print("✓ Drone connection closed")
            except Exception as e:
                print(f"⚠ Error closing drone: {e}")

    def execute(self):
        """Main execution method"""
        try:
            # Load mission data
            if not self.load_mission():
                return False

            # Connect to drone
            if not self.connect_drone():
                return False

            # Run mission
            success = self.run_mission()

            return success

        finally:
            self.cleanup()


def main():
    """Main entry point"""
    print("=" * 70)
    print("  Mission 2026: Time Warp - Autonomous Flight")
    print("  REC Aerial Drone Competition 2025/2026")
    print("  ** TIME-BASED NAVIGATION WITH FIXED HEIGHT CONTROL **")
    print("=" * 70)

    print("\n💡 TIP: Run calibrate_hybrid.py first to get accurate cm_per_second!")
    print("   Then add the tuning values to your JSON file.\n")

    # Create and execute mission
    mission = TimeBasedAutonomousMission()
    success = mission.execute()

    if success:
        print("\n✓ Program completed successfully")
        return 0
    else:
        print("\n✗ Program completed with errors")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
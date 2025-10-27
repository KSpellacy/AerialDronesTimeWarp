#!/usr/bin/env python3
"""
Mission 2026: Time Warp - Autonomous Flight Mission
REC Aerial Drone Competition 2025/2026

** TIME-BASED NAVIGATION VERSION **
Uses calibrated cm_per_second like calibrate_hybrid.py
More reliable than position estimation!

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

            time.sleep(1)
            return True
        except Exception as e:
            print(f"ERROR connecting to drone: {e}")
            return False

    def inches_to_cm(self, inches):
        """Convert inches to centimeters"""
        return inches * 2.54

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

        Args:
            pitch: Forward/backward power (-100 to 100)
            roll: Left/right power (-100 to 100)
            throttle: Up/down power (-100 to 100)
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

        # Update estimated position
        self.current_position['z'] = waypoint['position']['z']

        print("  ✓ Takeoff complete - hovering at starting altitude")
        return True

    def execute_navigate(self, waypoint):
        """
        Execute navigation waypoint using TIME-BASED movement.
        Like calibrate_hybrid.py: calculate time, set_pitch(), then move(time)
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

        # Calculate distances to target (in cm)
        error_x = pos['x'] - self.current_position['x']
        error_y = pos['y'] - self.current_position['y']
        error_z = pos['z'] - self.current_position['z']

        error_x_cm = self.inches_to_cm(error_x)
        error_y_cm = self.inches_to_cm(error_y)
        error_z_cm = self.inches_to_cm(error_z)

        distance_3d = math.sqrt(error_x ** 2 + error_y ** 2 + error_z ** 2)

        print(f"    Distance: {distance_3d:.1f}\" (x:{error_x:.1f}\" y:{error_y:.1f}\" z:{error_z:.1f}\")")

        # ====================================================================
        # TIME-BASED MOVEMENT SEQUENCE - START
        # ====================================================================

        try:
            # Move in Z (vertical) first if needed
            if abs(error_z) > 2.0:  # More than 2 inches
                print(f"    Step 1: Adjusting altitude...")

                throttle = throttle_power if error_z > 0 else -throttle_power
                move_time = self.calculate_move_time(abs(error_z_cm), throttle_power)

                print(f"      Moving {'up' if error_z > 0 else 'down'} for {move_time:.1f}s")

                # TIME-BASED MOVEMENT (like calibration script)
                self.move_time_based(throttle=throttle, duration=move_time)

                # Update position
                self.update_position_time_based(0, 0, throttle, move_time)

                # Brief hover
                self.drone.hover(1)

            # Move in X (forward/backward) if needed
            if abs(error_x) > 2.0:  # More than 2 inches
                print(f"    Step 2: Moving {'forward' if error_x > 0 else 'backward'}...")

                pitch = forward_power if error_x > 0 else -forward_power
                move_time = self.calculate_move_time(abs(error_x_cm), forward_power)

                print(f"      Moving for {move_time:.1f}s @ power {forward_power}")

                # TIME-BASED MOVEMENT (like calibration script)
                self.move_time_based(pitch=pitch, duration=move_time)

                # Update position
                self.update_position_time_based(pitch, 0, 0, move_time)

                # Brief hover
                self.drone.hover(1)

            # Move in Y (left/right) if needed
            if abs(error_y) > 2.0:  # More than 2 inches
                print(f"    Step 3: Moving {'right' if error_y > 0 else 'left'}...")

                roll = forward_power if error_y > 0 else -forward_power
                move_time = self.calculate_move_time(abs(error_y_cm), forward_power)

                print(f"      Moving for {move_time:.1f}s @ power {forward_power}")

                # TIME-BASED MOVEMENT (like calibration script)
                self.move_time_based(roll=roll, duration=move_time)

                # Update position
                self.update_position_time_based(0, roll, 0, move_time)

                # Brief hover
                self.drone.hover(1)

            # Final position reached
            print(f"  ✓ Arrived at target position")

            # Hover at waypoint for specified duration
            hover_time = waypoint.get('duration_estimate', 2)
            print(f"  → Hovering for {hover_time} seconds...")
            self.drone.hover(hover_time)

        # ====================================================================
        # TIME-BASED MOVEMENT SEQUENCE - END
        # ====================================================================

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

            hover_height = {'x': pos['x'], 'y': pos['y'], 'z': 6}
            landing_waypoint['position'] = hover_height

            if not self.execute_navigate(landing_waypoint):
                print("  ⚠ Could not reach landing position precisely")

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
    print("  ** TIME-BASED NAVIGATION **")
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
# VEX Aerial Drones Time Warp - Autonomous Flight System

Version 2.0 - Improved Generic Architecture

## Overview

This Python project provides autonomous flight control for CoDrone EDU drones competing in the VEX Robotics Aerial Drones Time Warp event. The system uses optical flow odometry for navigation and supports flexible, year-agnostic course configurations.

## Key Features

✅ **Generic Waypoint System** - Add/remove/modify waypoints without code changes  
✅ **Year-Agnostic Configuration** - Course layouts stored in JSON files  
✅ **Drift Mitigation** - Outlier rejection and sensor fusion for accurate navigation  
✅ **Calibration Support** - Built-in flow sensor calibration  
✅ **Comprehensive Logging** - Flight data logging for analysis  
✅ **Error Recovery** - Timeout protection and safety features  
✅ **Backward Compatible** - Quick recorder mode for Phase 1  

## Installation

### Requirements

- Python 3.7+
- CoDrone EDU Python SDK
- CoDrone EDU drone with optical flow sensor

### Setup

```bash
# Install CoDrone EDU SDK
pip install codrone-edu

# Clone or download this project
cd AerialDronesTimeWarp

# Verify structure
python main.py
```

## Project Structure

```
AerialDronesTimeWarp/
├── main.py                          # Main entry point
├── data/                            # Configuration files
│   ├── phase1_params.json           # Default Phase 1 config
│   └── example_course_2025.json     # Example configuration
├── phases/
│   └── autonomous_flight.py         # Generic flight controller
├── nav/
│   └── estimator.py                 # Odometry system with drift mitigation
├── recorder/
│   └── generic_recorder.py          # Waypoint recorder
├── logs/                            # Flight logs (auto-created)
└── tests/                           # Unit tests
```

## Quick Start

### 1. Record Course Parameters

**Option A: Quick Phase 1 Recorder (Backward Compatible)**
```bash
python main.py record --quick
```
Records arch and cube heights with distances.

**Option B: Generic Waypoint Recorder**
```bash
python main.py record
```
Interactive recorder supporting any number of waypoints.

### 2. Calibrate (Optional but Recommended)

```bash
python main.py calibrate --calibrate-distance 100
```

This determines the optimal `flow_scale` parameter for your drone. Add the result to your configuration file.

### 3. Fly Autonomous Mission

```bash
python main.py fly
```

Or specify a custom configuration:
```bash
python main.py fly --config data/my_course.json
```

## Configuration File Format

### Example: `data/course_2025.json`

```json
{
  "metadata": {
    "competition": "VEX Aerial Drones Time Warp",
    "year": 2025,
    "date_recorded": "2025-10-25T10:30:00",
    "recorded_by": "Team Name",
    "notes": "Practice field configuration"
  },
  "waypoints": [
    {
      "id": "start",
      "type": "takeoff",
      "height_cm": 0,
      "action": "takeoff"
    },
    {
      "id": "arch",
      "type": "gate",
      "height_cm": 85.0,
      "distance_from_previous_cm": 180.0,
      "action": "pass_through"
    },
    {
      "id": "cube",
      "type": "target",
      "height_cm": 40.0,
      "distance_from_previous_cm": 120.0,
      "action": "land"
    }
  ],
  "tuning": {
    "height_tolerance_cm": 6,
    "height_timeout_sec": 6,
    "forward_chunk_cm": 30,
    "forward_stop_epsilon_cm": 5.0,
    "flow_scale": 1.0
  }
}
```

### Waypoint Actions

- `takeoff` - Initial takeoff (always first waypoint)
- `pass_through` - Navigate to height, move forward, pass through gate
- `land` - Navigate to position, descend, and land

### Tuning Parameters

| Parameter | Description | Default | Recommended Range |
|-----------|-------------|---------|-------------------|
| `height_tolerance_cm` | Acceptable height error | 6 | 5-10 |
| `height_timeout_sec` | Max time to reach height | 6 | 5-10 |
| `forward_chunk_cm` | Distance per forward move | 30 | 20-40 |
| `forward_stop_epsilon_cm` | Stop threshold | 5.0 | 3-10 |
| `flow_scale` | Optical flow calibration | 1.0 | 0.8-1.5 |

## Usage Examples

### Interactive Menu
```bash
python main.py
```
Displays menu for mode selection.

### Record New Course
```bash
# Interactive recorder with 3 waypoints
python main.py record

# Quick Phase 1 recorder (arch + cube)
python main.py record --quick
```

### Fly Mission
```bash
# Use default configuration
python main.py fly

# Use custom configuration
python main.py fly --config data/regional_2025.json
```

### Calibrate Flow Sensor
```bash
# Calibrate over 100cm (default)
python main.py calibrate

# Calibrate over 150cm
python main.py calibrate --calibrate-distance 150
```

## Improvements Over Original Code

### 1. Generic Architecture
- **Before:** Hardcoded arch and cube waypoints
- **After:** Flexible JSON-based waypoint system

### 2. Drift Mitigation
- Outlier rejection for impossible velocities
- Moving average height filtering
- Position snapping at waypoints

### 3. Error Handling
- Timeout protection on all movements
- Sensor read failure handling
- Graceful degradation

### 4. Calibration
- Built-in flow sensor calibration
- Configurable scale factor
- No code changes needed for different surfaces

### 5. Logging
- Comprehensive flight logs
- Trajectory export for analysis
- Debug information

## Tuning Tips

### If Drone Undershoots Distances
1. Run calibration: `python main.py calibrate`
2. Increase `flow_scale` in configuration
3. Typical range: 1.0-1.3

### If Drone Overshoots Distances
1. Decrease `flow_scale` in configuration
2. Typical range: 0.8-1.0

### If Height Control is Unstable
1. Increase `height_tolerance_cm` (try 8-10)
2. Increase `height_timeout_sec` (try 8-10)
3. Check for air currents in flight area

### If Movements are Jerky
1. Reduce `forward_chunk_cm` (try 20-25)
2. Ensure good lighting for optical flow
3. Check surface texture visibility

## Safety Features

- **Timeout Protection:** All movements have maximum time limits
- **Bounds Checking:** Rejects physically impossible sensor readings
- **Position Snapping:** Prevents unbounded drift accumulation
- **Graceful Shutdown:** Proper cleanup on errors or interruption

## Troubleshooting

### "Configuration file not found"
Run recorder first: `python main.py record`

### Drone drifts off course
1. Run calibration
2. Check surface has good texture for optical flow
3. Ensure adequate lighting
4. Increase `forward_stop_epsilon_cm`

### Height control fails
1. Check battery level
2. Verify `get_height()` returns valid readings
3. Increase timeout and tolerance

### Flow sensor reads zero
1. Check surface texture (needs pattern, not solid color)
2. Verify lighting (not too bright or dark)
3. Clean optical flow sensor lens

## Competition Day Checklist

- [ ] Fully charge drone battery
- [ ] Test flight in practice area
- [ ] Record course parameters with recorder
- [ ] Run calibration to determine flow_scale
- [ ] Update configuration with calibrated values
- [ ] Test autonomous flight 2-3 times
- [ ] Check logs for any warnings
- [ ] Have backup configurations ready
- [ ] Know how to emergency stop (power button)

## Advanced Features

### Export Trajectory Data
```python
from nav.estimator import EnhancedOdometry

# Use EnhancedOdometry in your flight code
odo = EnhancedOdometry(drone, flow_scale=1.0, enable_logging=True)

# After flight, export trajectory
odo.export_trajectory("logs/trajectory.json")
```

### Custom Waypoint Actions
Extend `WaypointNavigator` class to add custom behaviors:

```python
def _execute_custom_action(self, waypoint):
    # Your custom action code
    pass
```

### Multiple Courses
Organize configurations by year or event:
```
data/
├── 2025_regional_north.json
├── 2025_regional_south.json
├── 2025_state.json
└── 2026_regional.json
```

## Testing Without Hardware

### Simulation Mode
```python
# In main.py, add simulation flag
SIMULATION_MODE = True  # Set to False for real hardware

if SIMULATION_MODE:
    from tests.simulated_drone import SimulatedDrone
    drone = SimulatedDrone()
else:
    from codrone_edu.drone import Drone
    drone = Drone()
```

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review configuration file format
3. Verify drone sensors are working
4. Test individual components (calibration, recording, etc.)

## License

MIT License - Feel free to modify and adapt for your team's needs.

## Credits

Original code by Keaton Spellacy  
Improvements and refactoring for generic architecture  
Team Etowah Eagles  

---

**Good luck at competition!** 🚁🏆

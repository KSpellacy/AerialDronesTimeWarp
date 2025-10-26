# Migration Guide: Original → Improved Version

## Overview

This guide helps you transition from the original hardcoded implementation to the improved generic architecture.

## What Changed?

### Code Structure
| Original | Improved |
|----------|----------|
| `recorder/position_recorder.py` | `recorder/generic_recorder.py` |
| `phases/phase1.py` | `phases/autonomous_flight.py` |
| `nav/estimator.py` | `nav/estimator.py` (enhanced) |
| Hardcoded heights/distances | JSON configuration files |

### Configuration Format

**Original (embedded in recorder):**
```python
data["arch_height"] = {"height_cm": 85.0}
data["cube_height"] = {"height_cm": 40.0}
data["forward_to_arch_cm"] = 180.0
data["forward_arch_to_cube_cm"] = 120.0
```

**Improved (waypoint-based JSON):**
```json
{
  "waypoints": [
    {"id": "start", "action": "takeoff"},
    {"id": "arch", "height_cm": 85.0, "distance_from_previous_cm": 180.0, "action": "pass_through"},
    {"id": "cube", "height_cm": 40.0, "distance_from_previous_cm": 120.0, "action": "land"}
  ]
}
```

## Migration Steps

### Step 1: Backup Original Code
```bash
cp -r AerialDronesTimeWarp AerialDronesTimeWarp_backup
```

### Step 2: Copy Improved Files
```bash
# Copy new files to your project
cp improved_project/phases/autonomous_flight.py phases/
cp improved_project/navigation/estimator.py navigation/
cp improved_project/recorder/generic_recorder.py recorder/
cp improved_project/main.py .
```

### Step 3: Convert Existing Config (if you have one)

If you have an existing `data/phase1_params.json`, convert it:

**Old format:**
```json
{
  "_meta": {...},
  "arch_height": {"height_cm": 85.0},
  "cube_height": {"height_cm": 40.0},
  "forward_to_arch_cm": 180.0,
  "forward_arch_to_cube_cm": 120.0
}
```

**Convert to new format:**
```json
{
  "metadata": {
    "competition": "VEX Aerial Drones Time Warp",
    "year": 2025,
    "date_recorded": "2025-10-25T10:00:00",
    "recorded_by": "Team"
  },
  "waypoints": [
    {"id": "start", "type": "takeoff", "height_cm": 0, "action": "takeoff"},
    {"id": "arch", "type": "gate", "height_cm": 85.0, "distance_from_previous_cm": 180.0, "action": "pass_through"},
    {"id": "cube", "type": "target", "height_cm": 40.0, "distance_from_previous_cm": 120.0, "action": "land"}
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

### Step 4: Update Import Statements

**In main.py:**

Original:
```python
from phases.phase1 import run as run_phase1
```

Improved:
```python
from phases.autonomous_flight import run as run_autonomous_flight
```

### Step 5: Test

```bash
# Test recording
python main.py record --quick

# Test flight (simulation recommended first)
python main.py fly
```

## Backward Compatibility

The improved version maintains backward compatibility:

✅ **Quick recorder mode** works exactly like original  
✅ **Default config location** unchanged (`data/phase1_params.json`)  
✅ **Same workflow** for Phase 1 courses  
✅ **All original features** still work  

### Using Backward Compatible Mode

```bash
# Record in quick mode (just like original)
python main.py record --quick

# Fly using default config
python main.py fly
```

This creates the same `phase1_params.json` but in the new format.

## Code Mapping

### Original → Improved Function Mapping

| Original Function | Improved Function | Location |
|------------------|------------------|----------|
| `recorder.position_recorder.run()` | `recorder.generic_recorder.run(quick_mode=True)` | generic_recorder.py |
| `phases.phase1.run()` | `phases.autonomous_flight.run()` | autonomous_flight.py |
| `phases.phase1.rise_to_height()` | `WaypointNavigator._rise_to_height()` | autonomous_flight.py |
| `phases.phase1.go_forward_until()` | `WaypointNavigator._go_forward_until()` | autonomous_flight.py |
| `nav.estimator.Odometry` | `nav.estimator.Odometry` | estimator.py (enhanced) |

### New Functions Added

| Function | Purpose | Location |
|----------|---------|----------|
| `calibrate_flow_sensor()` | Calibrate optical flow | estimator.py |
| `WaypointNavigator.execute_flight()` | Generic flight execution | autonomous_flight.py |
| `run_interactive()` | Full waypoint recorder | generic_recorder.py |
| `EnhancedOdometry` | Extended odometry with logging | estimator.py |

## Benefits of Migrating

1. **Flexibility:** Add/remove waypoints without code changes
2. **Accuracy:** Drift mitigation improves position tracking
3. **Calibration:** Built-in sensor calibration
4. **Logging:** Comprehensive flight logs
5. **Reusability:** Same code works for any year/course
6. **Debugging:** Better error messages and recovery

## Gradual Migration Path

You can migrate gradually:

### Phase 1: Add new files alongside old
```
project/
├── phases/
│   ├── phase1.py (keep old)
│   └── autonomous_flight.py (add new)
├── recorder/
│   ├── position_recorder.py (keep old)
│   └── generic_recorder.py (add new)
```

### Phase 2: Test new system
```bash
# Use new recorder
python -c "from recorder.generic_recorder import run; run(quick_mode=True)"

# Use new flight controller
python -c "from phases.autonomous_flight import run; run()"
```

### Phase 3: Switch main.py imports
Update main.py to use new modules.

### Phase 4: Remove old files
Once confident, remove old implementations.

## Troubleshooting Migration

### "Module not found"
- Ensure file paths are correct
- Check Python path includes project directory
- Verify `__init__.py` exists in package directories

### "Config format error"
- Use example config as template
- Validate JSON syntax
- Check all required fields present

### "Flight behavior different"
- Run calibration to get correct flow_scale
- Adjust tuning parameters
- Review logs for drift issues

## Support During Migration

1. Keep original code as backup
2. Test in simulation mode first
3. Start with quick/backward compatible mode
4. Gradually adopt advanced features
5. Review logs after each test

## Rollback Procedure

If you need to rollback:

```bash
# Restore backup
rm -rf AerialDronesTimeWarp
cp -r AerialDronesTimeWarp_backup AerialDronesTimeWarp
cd AerialDronesTimeWarp

# Use original commands
python main.py
```

## Next Steps After Migration

1. ✅ Run calibration
2. ✅ Create configurations for different courses
3. ✅ Test with multiple waypoints
4. ✅ Tune parameters for your drone
5. ✅ Set up logging and analysis
6. ✅ Practice autonomous flights

## Questions?

Common migration questions:

**Q: Will my old config files work?**  
A: No, but conversion is simple (see Step 3 above).

**Q: Do I need to re-record everything?**  
A: No, you can manually convert old data to new format.

**Q: Is the new system compatible with my CoDrone EDU?**  
A: Yes, uses same SDK methods.

**Q: What if I only need Phase 1?**  
A: Use `--quick` mode, works exactly like original.

**Q: Can I use both old and new code?**  
A: Yes, they can coexist during migration.

---

**Ready to migrate?** Start with Step 1 and work through systematically. Test at each step!

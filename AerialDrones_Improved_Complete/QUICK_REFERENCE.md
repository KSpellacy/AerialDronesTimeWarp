# Quick Reference Card - VEX Aerial Drones Time Warp

## Common Commands

### Record Course
```bash
# Interactive full recorder
python main.py record

# Quick Phase 1 (arch + cube only)
python main.py record --quick
```

### Calibrate Sensor
```bash
python main.py calibrate
```

### Fly Mission
```bash
# Default config
python main.py fly

# Custom config
python main.py fly --config data/my_course.json
```

## Pre-Flight Checklist

1. ✅ Charge battery
2. ✅ Record course parameters
3. ✅ Calibrate flow sensor
4. ✅ Update config with flow_scale
5. ✅ Test flight 2-3 times
6. ✅ Review logs for warnings

## Quick Tuning Guide

### Undershooting Distances?
→ Increase `flow_scale` (try 1.1-1.3)

### Overshooting Distances?
→ Decrease `flow_scale` (try 0.8-0.9)

### Height Unstable?
→ Increase `height_tolerance_cm` (try 8-10)

### Jerky Movements?
→ Reduce `forward_chunk_cm` (try 20-25)

## Configuration Template

```json
{
  "metadata": {
    "year": 2025,
    "recorded_by": "Your Name"
  },
  "waypoints": [
    {"id": "start", "action": "takeoff"},
    {"id": "gate1", "height_cm": 85, "distance_from_previous_cm": 180, "action": "pass_through"},
    {"id": "target", "height_cm": 40, "distance_from_previous_cm": 120, "action": "land"}
  ],
  "tuning": {
    "flow_scale": 1.0
  }
}
```

## Emergency Stop

**Press drone power button** - stops all motors immediately

## Key Improvements

✅ No hardcoded values - all in config files  
✅ Drift mitigation - outlier rejection  
✅ Year-agnostic - works for any course layout  
✅ Calibration built-in - automatic scale factor  
✅ Comprehensive logging - debugging made easy  

## File Locations

- **Configs:** `data/*.json`
- **Logs:** `logs/*.log`
- **Code:** `phases/`, `nav/`, `recorder/`

## Typical Values

| Parameter | Range | Default |
|-----------|-------|---------|
| arch_height | 70-100 cm | 85 |
| cube_height | 30-50 cm | 40 |
| distance_to_arch | 150-200 cm | 180 |
| arch_to_cube | 100-150 cm | 120 |
| flow_scale | 0.8-1.3 | 1.0 |

---
**Remember:** Test in practice area before competition!

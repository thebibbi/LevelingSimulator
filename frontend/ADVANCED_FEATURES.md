# Advanced Features Documentation

## Overview

The Stewart Platform Visualizer now includes comprehensive advanced visualization and analysis tools to help you understand workspace limitations, force distributions, and platform behavior.

---

## 1. Workspace Envelope Visualization

### What It Does
Displays a **dynamic, color-coded** 3D volume of all reachable positions for the platform. The envelope updates in real-time as you move the platform, with colors changing based on distance from the current position.

### Color Coding (Vibrant Gradient)
- **Cyan/Turquoise**: Positions very close to current location
- **Green**: Nearby positions
- **Yellow**: Medium distance from current position
- **Orange**: Far from current position
- **Magenta/Hot Pink**: Positions at extreme workspace boundaries

### How It Works
- Samples a grid of positions in 3D space (X, Y, Z)
- Tests each position for reachability based on:
  - Leg length limits
  - Joint angle constraints (max 75° from vertical)
  - **Current platform orientation** (roll, pitch, yaw)
- Calculates distance from current position to each reachable point
- Colors each point based on distance (green → yellow → red gradient)
- **Fully Dynamic**: Updates as you move or rotate the platform

### Usage
1. Enable "Workspace Envelope" checkbox in Advanced Visualizations panel
2. Colored spheres appear showing reachable workspace
3. **Move the platform**: Colors shift as distances change
4. **Rotate the platform**: Envelope shape and colors update
5. Watch colors change to red as you approach workspace limits

### Performance Notes
- Calculation is intensive - may take a few seconds
- Lower resolution = faster rendering
- Recalculates when position OR orientation changes
- Color gradient updates in real-time

### Interpretation
- **Cyan/turquoise spheres**: Very close reachable positions
- **Green spheres**: Nearby reachable positions
- **Yellow spheres**: Moderate distance away
- **Orange spheres**: Far positions
- **Magenta/pink spheres**: Extreme workspace boundaries
- **More magenta**: Platform is near its limits
- **More cyan/green**: Platform has room to move

---

## 2. Leg Length Heatmap

### What It Does
Colors each leg based on its current length using a gradient from green (short) to red (long).

### Color Coding
- **Green**: Leg near minimum length (compressed)
- **Yellow**: Leg at mid-range
- **Red**: Leg near maximum length (extended)

### Usage
1. Enable "Leg Length Heatmap" checkbox
2. Legs change color in real-time as you move the platform
3. Replaces normal gray legs with colored visualization

### Applications
- **Load balancing**: See which legs are most extended
- **Optimization**: Find poses with even leg distribution
- **Safety**: Identify legs approaching limits

---

## 3. Force/Torque Visualization

### What It Does
Displays compression force vectors on each leg as colored arrows.

### Color Coding
- **Green**: Normal force (< 1.0x nominal)
- **Yellow**: Moderate force (1.0-1.2x nominal)
- **Red**: High force (> 1.2x nominal)

### How It Works
- Calculates force based on leg length deviation from nominal
- Longer legs = higher compression force
- Arrows point from platform toward base (compression direction)

### Usage
1. Enable "Force/Torque Vectors" checkbox
2. Colored arrows appear on each leg
3. Arrow length indicates force magnitude

### Applications
- **Structural analysis**: Identify high-stress configurations
- **Load distribution**: See force balance across platform
- **Safety margins**: Avoid excessive forces

---

## 4. Multiple View Modes

### Available Views

#### Perspective (Default)
- 3D view from angle (260, 220, 280)
- Best for general visualization
- Full depth perception

#### Top View
- Looking straight down (Z-axis)
- See X-Y plane clearly
- Useful for circular motion analysis

#### Side View
- Looking from the side (Y-axis)
- See X-Z plane clearly
- Useful for vertical motion analysis

#### Front View
- Looking from front (X-axis)
- See Y-Z plane clearly
- Useful for tilt analysis

### Usage
Click the view mode buttons in Advanced Visualizations panel to switch between views.

---

## 5. Grid and Axes Controls

### Grid Helper
- **Toggle**: Show/hide grid
- **Size**: 400mm x 400mm
- **Divisions**: 20 lines
- **Purpose**: Spatial reference, scale indication

### Coordinate Axes
- **X-axis**: Red (horizontal)
- **Y-axis**: Green (horizontal)
- **Z-axis**: Blue (vertical)
- **Length**: 100mm each
- **Purpose**: Orientation reference

---

## 6. Workspace Analysis Panel

### Real-time Metrics

#### Reachability
- ✓ **Yes**: Current pose is achievable
- ✕ **No**: Pose violates constraints

#### Singularity Detection
- Detects when legs become nearly parallel
- Warns about extreme joint angles (>70°)
- Shows which legs are problematic

#### Collision Detection
- Checks if legs are too close (< 20mm)
- Prevents physical interference
- Identifies specific leg pairs

#### Workspace Utilization
- **Average**: Overall leg extension usage
- **Min/Max**: Range across all legs
- **Color bar**:
  - Green: < 60% (safe)
  - Yellow: 60-80% (moderate)
  - Red: > 80% (near limits)

---

## 7. Joint Angles Display

### Features
- Shows angle of each leg from vertical
- Real-time updates
- Color-coded warnings:
  - **Green**: < 45° (good)
  - **Yellow**: 45-60° (warning)
  - **Red**: > 60° (critical)

### Applications
- Avoid extreme angles
- Optimize joint wear
- Identify singularities

---

## 8. Preset Poses

### Available Presets

1. **Home**: Neutral position (0, 0, 160, 0, 0, 0)
2. **Max X**: Maximum X translation (+40mm)
3. **Max Y**: Maximum Y translation (+40mm)
4. **Max Z**: Maximum height (200mm)
5. **Min Z**: Minimum height (130mm)
6. **Tilt X**: Roll rotation (8°)
7. **Tilt Y**: Pitch rotation (8°)
8. **Rotate**: Yaw rotation (15°)
9. **Combined**: Multi-axis movement

### Usage
Click any preset button to instantly move to that pose.

---

## Technical Details

### Workspace Envelope Algorithm
```
Get current orientation (roll, pitch, yaw)
For each point (x, y, z) in grid:
  1. Create pose [x, y, z, roll, pitch, yaw]
  2. Calculate inverse kinematics
  3. Check if all legs within limits
  4. Check if all angles < 75°
  5. If valid, add to envelope
  
Recalculate when orientation changes
```

### Force Calculation
```
force = (current_length / nominal_length)
color = force > 1.2 ? red : force > 1.0 ? yellow : green
```

### Heatmap Gradient
```
normalized = (length - min) / (max - min)
if normalized < 0.5:
  color = lerp(green, yellow, normalized * 2)
else:
  color = lerp(yellow, red, (normalized - 0.5) * 2)
```

---

## Performance Optimization

### Workspace Envelope
- **Resolution**: 15mm default (adjustable)
- **Range**: ±40mm X/Y, 130-200mm Z
- **Points**: ~1000-2000 depending on geometry
- **Caching**: Recalculates when orientation (roll/pitch/yaw) changes
- **Dynamic**: Updates in real-time as you rotate the platform

### Real-time Updates
- Joint angles: Every frame
- Workspace analysis: Every pose change
- Force vectors: Every pose change
- Heatmap: Every pose change

---

## Best Practices

### For Analysis
1. Start with workspace envelope to understand limits
2. Use heatmap to see leg distribution
3. Check force vectors for load balancing
4. Monitor workspace utilization percentage

### For Safety
1. Keep workspace utilization < 80%
2. Avoid red zones in joint angles
3. Watch for singularity warnings
4. Check collision detection

### For Optimization
1. Use heatmap to find even leg distribution
2. Minimize force vector magnitudes
3. Stay in green zones for all metrics
4. Test with preset poses first

---

## Troubleshooting

### Workspace Envelope Not Showing
- Check if "Workspace Envelope" is enabled
- Ensure limits are reasonable (140-220mm default)
- May take a few seconds to calculate

### Heatmap Colors Not Changing
- Verify "Leg Length Heatmap" is enabled
- Check if pose is actually changing
- Ensure limits are set correctly

### Force Vectors Too Small/Large
- Vectors scale with force magnitude
- Adjust nominal leg length (l0) if needed
- Check leg length limits

### View Mode Not Changing
- Click view mode button again
- Manually rotate with mouse to reset
- Refresh application if stuck

---

## Keyboard Shortcuts (Future Enhancement)

Planned shortcuts:
- `W`: Toggle workspace envelope
- `H`: Toggle heatmap
- `F`: Toggle force vectors
- `G`: Toggle grid
- `A`: Toggle axes
- `1-4`: Switch view modes
- `R`: Reset view
- `Space`: Toggle animation

---

## API Reference

### Visualization State
```javascript
{
  showWorkspaceEnvelope: boolean,
  showHeatmap: boolean,
  showForces: boolean,
  showGrid: boolean,
  showAxes: boolean,
  showMeasurements: boolean
}
```

### View Modes
```javascript
'perspective' | 'top' | 'side' | 'front'
```

### Workspace Analysis Result
```javascript
{
  singularity: {
    isSingular: boolean,
    message: string
  },
  collision: {
    hasCollision: boolean,
    message: string
  },
  utilization: {
    average: number,
    perLeg: number[],
    max: number,
    min: number
  },
  reachable: boolean
}
```

---

## Future Enhancements

### Planned Features
1. **Measurement Tools**: Click-to-measure distances
2. **Path Recording**: Record and replay motion paths
3. **Stiffness Visualization**: Show platform rigidity
4. **Velocity Vectors**: Display motion direction/speed
5. **Acceleration Heatmap**: Show dynamic forces
6. **Workspace Slicing**: 2D cross-sections of workspace
7. **Export Visualizations**: Save images/videos
8. **Custom Color Schemes**: User-defined gradients

### Under Consideration
- Real-time performance graphs
- Jacobian matrix visualization
- Dexterity index display
- Manipulability ellipsoid
- Optimal pose suggestions

---

## Credits

Advanced visualization features implemented using:
- **React Three Fiber**: 3D rendering
- **Three.js**: Graphics engine
- **@react-three/drei**: Helper components
- **Custom algorithms**: Workspace analysis, force calculation

---

## Support

For issues or feature requests:
1. Check this documentation first
2. Review console for error messages
3. Test with default geometry parameters
4. Try different configurations

---

## Version History

### v2.0.0 (Current)
- Added workspace envelope visualization
- Implemented leg length heatmap
- Added force/torque vectors
- Multiple view modes
- Comprehensive workspace analysis
- Joint angle monitoring
- Preset poses

### v1.0.0
- Basic Stewart platform visualization
- Multiple configurations
- Configurable geometry
- Self-tests

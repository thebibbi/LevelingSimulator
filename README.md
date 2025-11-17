# Stewart Platform Visualizer

A 3D visualization tool for Stewart platforms using React Three Fiber. This application allows you to interactively control and visualize the kinematics of different Stewart platform configurations with configurable geometry parameters.

**Available as both a web application and a desktop app (Electron).**

## Features

- Interactive 3D visualization of Stewart platform
- Support for multiple configurations (8-8, 6-6, 6-3-redundant, 6-3-asymmetric, 6-3, 4-4, 3-3)
- Configurable geometry parameters (base radius, platform radius, nominal leg length)
- Real-time inverse kinematics calculations
- Manual control via sliders for all 6 degrees of freedom
- Automatic animation mode
- Leg length monitoring with configurable limits
- Self-testing functionality to verify calculations

## Prerequisites

- Node.js (v14 or higher)
- npm or yarn

## Getting Started

### Web Application

1. Clone or download this repository
2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Desktop Application (Electron)

1. Install dependencies (if not already done):
```bash
npm install
```

2. Run in development mode:
```bash
npm run electron-dev
```

3. Build executable for your platform:
```bash
# For macOS
npm run electron-build-mac

# For Windows
npm run electron-build-win

# For Linux
npm run electron-build-linux
```

See [ELECTRON.md](ELECTRON.md) for detailed Electron-specific instructions.

## Usage

### Controls

- **Manual Control**: Use the sliders in the left panel to adjust the platform position (X, Y, Z) and orientation (Roll, Pitch, Yaw)
- **Animation**: Click the "Animate" button to start automatic motion
- **Reset**: Click the "Reset" button to return to the home position
- **3D View**: Use mouse controls to rotate, pan, and zoom the 3D view

### Parameters

- Adjust minimum and maximum leg lengths to set operational limits
- Monitor leg extensions in real-time
- Visual indicators show when legs are outside operational limits

## Stewart Platform Configurations

The application supports seven different Stewart platform configurations:

### 8-8 Configuration
- 8 base attachment points arranged in an octagon
- 8 platform attachment points arranged in an octagon
- 1:1 leg mapping (leg 0 connects to platform point 0, etc.)
- Highest redundancy and stability

### 6-6 Configuration
- 6 base attachment points arranged in a hexagon
- 6 platform attachment points arranged in a hexagon
- 1:1 leg mapping (leg 0 connects to platform point 0, etc.)
- Good balance of complexity and redundancy

### 6-3 Redundant Configuration
- 6 base attachment points arranged in a hexagon
- 3 platform attachment points arranged in a triangle
- Redundant leg pairing: each platform point connects to 2 base points
- Increased stability through redundancy

### 6-3 Asymmetric Configuration
- 6 base attachment points arranged in a hexagon
- 3 platform attachment points arranged in a triangle
- Asymmetric leg pairing: [0, 1, 1, 2, 2, 0]
- Different kinematic properties than standard 6-3

### 6-3 Configuration (Standard)
- 6 base attachment points arranged in a hexagon
- 3 platform attachment points arranged in a triangle
- Leg pairing: (0,1)-(2,3)-(4,5)
- Best for understanding basic Stewart platform kinematics

### 4-4 Configuration
- 4 base attachment points arranged in a square
- 4 platform attachment points arranged in a square
- 1:1 leg mapping (leg 0 connects to platform point 0, etc.)
- Simpler configuration for basic understanding

### 3-3 Configuration
- 3 base attachment points arranged in a triangle
- 3 platform attachment points arranged in a triangle
- 1:1 leg mapping (leg 0 connects to platform point 0, etc.)
- Most simplified platform for basic understanding

## Configurable Geometry Parameters

The application allows you to customize the geometry of the Stewart platform:

### Base Radius
- Controls the size of the base platform
- Default: 120 mm
- Larger values create a wider base

### Platform Radius
- Controls the size of the moving platform
- Default: 70 mm
- Larger values create a wider moving platform

### Nominal Leg Length
- Controls the resting length of the actuators
- Default: 150 mm
- Affects the working height of the platform

These parameters can be adjusted in real-time to see how they affect the kinematics and workspace of the Stewart platform.

## Technical Details

### Kinematics

The application implements inverse kinematics for Stewart platforms with configurable parameters:

- Base radius: 120 mm (default, adjustable)
- Platform radius: 70 mm (default, adjustable)
- Nominal leg length: 150 mm (default, adjustable)

### Self-Tests

The application includes built-in self-tests that verify:

1. Rotation matrix orthogonality
2. Platform radial distance preservation under yaw rotation
3. Correct Z translation application
4. Leg pair symmetry at neutral pose (6-3 configuration)
5. Positive leg lengths at neutral pose
6. Correct data structure shapes for all configurations
7. Proper functioning of 8-8 configuration
8. Proper functioning of 4-4 configuration
9. Proper functioning of 6-3 asymmetric configuration
10. Proper functioning of 6-3 redundant configuration

## Dependencies

- React
- Three.js
- React Three Fiber
- React Three Drei
- Tailwind CSS

## License

This project is licensed under the MIT License.

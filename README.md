# Platform Leveling System - Integrated Monorepo

A comprehensive platform leveling system combining interactive 3D visualization with real-time hardware control for Stewart platforms and tripod configurations.

## 🏗️ Project Structure

```
LevelingSimulator/
├── frontend/              # React/Three.js visualization & UI
│   ├── src/
│   │   ├── stewart_6_3_browser_visualizer.jsx  # Main visualizer
│   │   ├── api-client.js                        # Backend API client
│   │   ├── useBackendAPI.js                     # React hooks for API
│   │   └── BackendPanel.jsx                     # Backend connection UI
│   ├── package.json
│   └── README.md
│
├── backend/               # Python control system & API
│   ├── inverse_kinematics.py    # Core IK solver
│   ├── leveling_system.py       # Integrated system
│   ├── esp32_controller.py      # Hardware controller
│   ├── api.py                   # FastAPI REST/WebSocket server
│   ├── requirements.txt
│   └── README.md
│
└── README.md             # This file
```

## 🎯 What's Inside

### Frontend (React + Three.js)
- **Interactive 3D Visualization**: Real-time Stewart platform rendering using React Three Fiber
- **Multiple Configurations**: Support for 3-3, 4-4, 6-3 (standard/asymmetric/redundant), 6-6, and 8-8 platforms
- **Configurable Geometry**: Adjustable base radius, platform radius, and leg lengths
- **Dual Mode**: Works standalone or connected to Python backend
- **Electron Support**: Available as both web and desktop application

### Backend (Python + FastAPI)
- **Inverse Kinematics**: Precise calculations for tripod and Stewart platforms
- **Hardware Control**: ESP32 integration for real actuators
- **IMU Integration**: BNO055 sensor support with iPhone fallback for testing
- **REST API**: RESTful endpoints for calculations
- **WebSocket**: Real-time bidirectional communication
- **Production Ready**: Designed for vehicle-mounted leveling systems

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v14 or higher) for frontend
- **Python** (3.8 or higher) for backend
- **npm** or **yarn** for JavaScript packages
- **pip** for Python packages

### Option 1: Full Stack (Frontend + Backend)

#### 1. Start the Backend API

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI server
python api.py
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

#### 2. Start the Frontend

In a new terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start development server
npm start
```

The app will open at `http://localhost:3000`

#### 3. Connect Frontend to Backend

In the web app:
1. Look for the "Backend Connection" panel
2. Verify connection status shows "Connected"
3. Enable "Use Backend Calculations" to use Python IK solver
4. Click "Test Backend" to verify integration

### Option 2: Frontend Only (Standalone)

```bash
cd frontend
npm install
npm start
```

The visualizer works independently with built-in JavaScript IK calculations.

### Option 3: Backend Only (API Server)

```bash
cd backend
pip install -r requirements.txt
python api.py
```

Use the API directly via HTTP requests or explore at `http://localhost:8000/docs`

## 📚 Usage Examples

### REST API Examples

**Calculate IK for a pose:**
```bash
curl -X POST http://localhost:8000/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "x": 0, "y": 0, "z": 10,
    "roll": 5, "pitch": -3, "yaw": 0,
    "configuration": "6-3"
  }'
```

**Calculate leveling corrections:**
```bash
curl "http://localhost:8000/level?roll=10&pitch=5&configuration=6-3"
```

**Get available configurations:**
```bash
curl http://localhost:8000/configurations
```

### JavaScript API Examples

```javascript
import apiClient from './api-client';

// Check backend connection
const { connected } = await apiClient.checkHealth();

// Calculate IK
const result = await apiClient.calculateIK({
  x: 0, y: 0, z: 10,
  roll: 5, pitch: -3, yaw: 0,
  configuration: '6-3'
});

console.log('Leg lengths:', result.leg_lengths);
console.log('Valid:', result.valid);
```

### React Hook Examples

```jsx
import { useBackendConnection, useBackendIK } from './useBackendAPI';

function MyComponent() {
  const { connected, health } = useBackendConnection();
  const { calculate, result } = useBackendIK();

  const handleCalculate = async () => {
    await calculate({
      x: 0, y: 0, z: 10,
      roll: 5, pitch: -3, yaw: 0,
      configuration: '6-3'
    });
  };

  return (
    <div>
      <p>Backend: {connected ? 'Connected' : 'Disconnected'}</p>
      <button onClick={handleCalculate}>Calculate</button>
      {result && <p>Leg 1: {result.leg_lengths[0]} mm</p>}
    </div>
  );
}
```

## 🎨 Platform Configurations

| Configuration | Base Points | Platform Points | Legs | Use Case |
|--------------|-------------|-----------------|------|----------|
| 3-3 | 3 (triangle) | 3 (triangle) | 3 | Simplest tripod |
| 4-4 | 4 (square) | 4 (square) | 4 | Square platform |
| 6-3 | 6 (hexagon) | 3 (triangle) | 6 | Standard paired |
| 6-3 Asymmetric | 6 (hexagon) | 3 (triangle) | 6 | Alternative pairing |
| 6-3 Redundant | 6 (hexagon) | 3 (triangle) | 6 | Extra stability |
| 6-6 | 6 (hexagon) | 6 (hexagon) | 6 | Classic Stewart |
| 8-8 | 8 (octagon) | 8 (octagon) | 8 | Maximum redundancy |

## 🛠️ Development

### Frontend Development

```bash
cd frontend

# Development server
npm start

# Build for production
npm run build

# Build Electron app
npm run electron-build
```

### Backend Development

```bash
cd backend

# Run with auto-reload
uvicorn api:app --reload

# Run tests
python inverse_kinematics.py
python -m pytest  # If tests are configured
```

## 🔧 Configuration

### Backend Configuration

Edit geometry parameters in `backend/api.py` or send via API:

```python
{
  "base_radius": 120.0,        # mm
  "platform_radius": 70.0,     # mm
  "nominal_leg_length": 150.0, # mm
  "min_leg_length": 100.0,     # mm
  "max_leg_length": 200.0      # mm
}
```

### Frontend Configuration

Adjust parameters in the UI or modify defaults in the source code:
- Base radius
- Platform radius
- Nominal leg length
- Min/max leg limits

## 🌐 API Documentation

Once the backend is running, visit:
- **Interactive docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc
- **OpenAPI spec**: http://localhost:8000/openapi.json

## 🚢 Deployment

### Frontend Deployment

**As Web App:**
```bash
cd frontend
npm run build
# Deploy 'build' folder to any static hosting
```

**As Electron App:**
```bash
cd frontend
npm run electron-build-mac    # macOS
npm run electron-build-win    # Windows
npm run electron-build-linux  # Linux
```

### Backend Deployment

**Using Docker:**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Using systemd (Linux):**
```ini
[Unit]
Description=Platform Leveling API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/leveling/backend
ExecStart=/usr/bin/python3 api.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## 🔌 Hardware Integration

The backend is designed to work with:
- **ESP32 microcontroller** for actuator control
- **BNO055 IMU sensor** for orientation measurement
- **Linear actuators** (3 or 6 depending on configuration)

See `backend/ESP32_FIRMWARE.md` and `backend/HARDWARE_SPEC.md` for details.

## 📖 Additional Documentation

- **Frontend Details**: See `frontend/README.md`
- **Backend Details**: See `backend/README.md`
- **Advanced Features**: See `frontend/ADVANCED_FEATURES.md`
- **Electron Guide**: See `frontend/ELECTRON.md`
- **Quick Start**: See `frontend/QUICKSTART.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- React Three Fiber for 3D rendering
- FastAPI for the Python backend framework
- Three.js for 3D graphics
- NumPy for numerical computations

## 📧 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation in `frontend/` and `backend/` directories
- Review API docs at `http://localhost:8000/docs` when backend is running

---

**Built with ❤️ for robotics and automation**

"""
FastAPI REST API for Platform Leveling System
Exposes inverse kinematics calculations and platform control
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import numpy as np
import json
from dataclasses import asdict

from inverse_kinematics import TripodIK, StewartPlatformIK, PlatformConfig

app = FastAPI(
    title="Platform Leveling API",
    description="API for Stewart Platform and Tripod inverse kinematics calculations",
    version="1.0.0"
)

# CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class PlatformConfigModel(BaseModel):
    """Platform geometry configuration"""
    base_radius: float = Field(default=120.0, description="Base radius in mm")
    platform_radius: float = Field(default=70.0, description="Platform radius in mm")
    nominal_leg_length: float = Field(default=150.0, description="Nominal leg length in mm")
    min_leg_length: float = Field(default=100.0, description="Minimum leg length in mm")
    max_leg_length: float = Field(default=200.0, description="Maximum leg length in mm")


class PoseRequest(BaseModel):
    """Request for inverse kinematics calculation"""
    x: float = Field(default=0.0, description="X translation in mm")
    y: float = Field(default=0.0, description="Y translation in mm")
    z: float = Field(default=0.0, description="Z translation in mm")
    roll: float = Field(default=0.0, description="Roll angle in degrees")
    pitch: float = Field(default=0.0, description="Pitch angle in degrees")
    yaw: float = Field(default=0.0, description="Yaw angle in degrees")

    configuration: Literal["3-3", "4-4", "6-3", "6-3-asymmetric", "6-3-redundant", "6-6", "8-8"] = Field(
        default="6-3",
        description="Platform configuration"
    )

    geometry: Optional[PlatformConfigModel] = Field(
        default=None,
        description="Optional custom geometry parameters"
    )


class LegLengthResponse(BaseModel):
    """Response with calculated leg lengths"""
    leg_lengths: List[float] = Field(description="Leg lengths in mm")
    valid: bool = Field(description="Whether the solution is within limits")
    configuration: str = Field(description="Platform configuration used")
    pose: dict = Field(description="The requested pose")


class HealthResponse(BaseModel):
    """API health check response"""
    status: str
    message: str
    version: str


# Global configuration cache
current_config = PlatformConfigModel()


def get_configuration_mapping(config: str) -> dict:
    """Get base and platform point configurations for each setup"""
    configurations = {
        "3-3": {
            "num_base": 3,
            "num_platform": 3,
            "leg_pairs": list(range(3))  # 1:1 mapping
        },
        "4-4": {
            "num_base": 4,
            "num_platform": 4,
            "leg_pairs": list(range(4))
        },
        "6-3": {
            "num_base": 6,
            "num_platform": 3,
            "leg_pairs": [0, 0, 1, 1, 2, 2]  # Paired mapping
        },
        "6-3-asymmetric": {
            "num_base": 6,
            "num_platform": 3,
            "leg_pairs": [0, 1, 1, 2, 2, 0]  # Asymmetric pairing
        },
        "6-3-redundant": {
            "num_base": 6,
            "num_platform": 3,
            "leg_pairs": [0, 1, 1, 2, 2, 0]  # Alternative pairing
        },
        "6-6": {
            "num_base": 6,
            "num_platform": 6,
            "leg_pairs": list(range(6))
        },
        "8-8": {
            "num_base": 8,
            "num_platform": 8,
            "leg_pairs": list(range(8))
        }
    }
    return configurations.get(config, configurations["6-3"])


def generate_points(n: int, radius: float, angle_offset: float = 0) -> np.ndarray:
    """Generate n points in a circular pattern"""
    points = []
    for i in range(n):
        angle = 2 * np.pi * i / n + angle_offset
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        points.append([x, y, 0])
    return np.array(points)


def calculate_ik(pose: PoseRequest) -> LegLengthResponse:
    """Calculate inverse kinematics for given pose"""

    # Use provided geometry or default
    geometry = pose.geometry if pose.geometry else current_config

    # Convert angles to radians
    roll_rad = np.deg2rad(pose.roll)
    pitch_rad = np.deg2rad(pose.pitch)
    yaw_rad = np.deg2rad(pose.yaw)

    # Get configuration mapping
    config_map = get_configuration_mapping(pose.configuration)
    num_base = config_map["num_base"]
    num_platform = config_map["num_platform"]
    leg_pairs = config_map["leg_pairs"]

    # Generate base and platform points
    base_points = generate_points(num_base, geometry.base_radius, 0)
    platform_points = generate_points(
        num_platform,
        geometry.platform_radius,
        np.pi / num_platform if num_platform < 6 else np.pi / 6
    )

    # Create rotation matrix
    def rotation_matrix(roll, pitch, yaw):
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(roll), -np.sin(roll)],
            [0, np.sin(roll), np.cos(roll)]
        ])

        Ry = np.array([
            [np.cos(pitch), 0, np.sin(pitch)],
            [0, 1, 0],
            [-np.sin(pitch), 0, np.cos(pitch)]
        ])

        Rz = np.array([
            [np.cos(yaw), -np.sin(yaw), 0],
            [np.sin(yaw), np.cos(yaw), 0],
            [0, 0, 1]
        ])

        return Rz @ Ry @ Rx

    R = rotation_matrix(roll_rad, pitch_rad, yaw_rad)

    # Translation vector
    translation = np.array([pose.x, pose.y, pose.z + geometry.nominal_leg_length])

    # Calculate leg lengths
    leg_lengths = []
    for i in range(num_base):
        # Get corresponding platform point
        platform_idx = leg_pairs[i]

        # Transform platform point
        platform_point = platform_points[platform_idx].copy()
        platform_point[2] = geometry.nominal_leg_length

        # Apply rotation and translation
        rotated_point = R @ platform_point + translation

        # Calculate distance from base to transformed platform point
        base_point_with_z = base_points[i].copy()
        leg_length = np.linalg.norm(rotated_point - base_point_with_z)
        leg_lengths.append(float(leg_length))

    # Check validity
    valid = all(geometry.min_leg_length <= length <= geometry.max_leg_length
                for length in leg_lengths)

    return LegLengthResponse(
        leg_lengths=leg_lengths,
        valid=valid,
        configuration=pose.configuration,
        pose={
            "x": pose.x,
            "y": pose.y,
            "z": pose.z,
            "roll": pose.roll,
            "pitch": pose.pitch,
            "yaw": pose.yaw
        }
    )


# API Endpoints

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        message="Platform Leveling API is running",
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Detailed health check"""
    return HealthResponse(
        status="healthy",
        message="All systems operational",
        version="1.0.0"
    )


@app.post("/calculate", response_model=LegLengthResponse)
async def calculate_leg_lengths(pose: PoseRequest):
    """
    Calculate inverse kinematics for a given pose

    Returns the required leg lengths to achieve the specified position and orientation
    """
    try:
        return calculate_ik(pose)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/level", response_model=LegLengthResponse)
async def calculate_leveling(
    roll: float = Field(description="Current roll angle in degrees"),
    pitch: float = Field(description="Current pitch angle in degrees"),
    yaw: float = Field(default=0.0, description="Current yaw angle in degrees"),
    configuration: str = Field(default="6-3", description="Platform configuration")
):
    """
    Calculate leg lengths needed to level the platform

    Given current orientation, returns leg lengths to achieve level position
    """
    try:
        # To level, we apply opposite rotation
        pose = PoseRequest(
            x=0, y=0, z=0,
            roll=-roll,
            pitch=-pitch,
            yaw=-yaw,
            configuration=configuration
        )
        return calculate_ik(pose)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config", response_model=PlatformConfigModel)
async def get_config():
    """Get current platform configuration"""
    return current_config


@app.post("/config", response_model=PlatformConfigModel)
async def update_config(config: PlatformConfigModel):
    """Update platform configuration"""
    global current_config
    current_config = config
    return current_config


@app.get("/configurations")
async def get_available_configurations():
    """Get list of available platform configurations"""
    return {
        "configurations": [
            {
                "id": "3-3",
                "name": "3-3 Tripod",
                "description": "3 base points, 3 platform points - simplest configuration",
                "num_legs": 3
            },
            {
                "id": "4-4",
                "name": "4-4 Square",
                "description": "4 base points, 4 platform points - square configuration",
                "num_legs": 4
            },
            {
                "id": "6-3",
                "name": "6-3 Standard",
                "description": "6 base points, 3 platform points - standard pairing",
                "num_legs": 6
            },
            {
                "id": "6-3-asymmetric",
                "name": "6-3 Asymmetric",
                "description": "6 base points, 3 platform points - asymmetric pairing",
                "num_legs": 6
            },
            {
                "id": "6-3-redundant",
                "name": "6-3 Redundant",
                "description": "6 base points, 3 platform points - redundant configuration",
                "num_legs": 6
            },
            {
                "id": "6-6",
                "name": "6-6 Hexagonal",
                "description": "6 base points, 6 platform points - classic Stewart platform",
                "num_legs": 6
            },
            {
                "id": "8-8",
                "name": "8-8 Octagonal",
                "description": "8 base points, 8 platform points - maximum redundancy",
                "num_legs": 8
            }
        ]
    }


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time pose updates

    Client sends pose data, server responds with leg lengths
    """
    await websocket.accept()
    try:
        while True:
            # Receive pose data
            data = await websocket.receive_text()
            pose_data = json.loads(data)

            # Create PoseRequest from received data
            pose = PoseRequest(**pose_data)

            # Calculate IK
            result = calculate_ik(pose)

            # Send back result
            await websocket.send_json(result.dict())

    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    print("Starting Platform Leveling API...")
    print("API will be available at http://localhost:8000")
    print("Documentation at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

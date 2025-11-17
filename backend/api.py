"""
FastAPI REST API for Platform Leveling System - Production Ready
Includes: Authentication, Rate Limiting, Caching, Logging, Monitoring, Database
"""

import json
import logging
import math
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Literal, Optional

import numpy as np
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from auth import optional_api_key, verify_api_key
from cache import generate_cache_key, get_cache_stats, get_cached, init_cache, set_cached
from config import settings
from database import init_db
from logging_config import log_request, setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting Platform Leveling API...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # Initialize cache
    if settings.redis_enabled:
        init_cache()

    # Initialize database
    if settings.database_enabled:
        init_db()
        logger.info("✓ Database initialized")

    logger.info("✓ API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down API...")


# Create FastAPI app
app = FastAPI(
    title="Platform Leveling API",
    description="Production-ready API for Stewart Platform and Tripod inverse kinematics",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware with proper configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # No more "*"!
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key"],
    max_age=3600,
)

# Request logging middleware
app.middleware("http")(log_request)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Prometheus metrics
instrumentator = Instrumentator().instrument(app)


@app.on_event("startup")
async def _startup():
    """Expose Prometheus metrics"""
    instrumentator.expose(app)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(
        "Unhandled exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error": str(exc),
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "path": request.url.path,
        },
    )


# Pydantic models with validation
class PlatformConfigModel(BaseModel):
    """Platform geometry configuration with validation"""

    base_radius: float = Field(default=120.0, ge=10.0, le=500.0, description="Base radius in mm")
    platform_radius: float = Field(
        default=70.0, ge=10.0, le=500.0, description="Platform radius in mm"
    )
    nominal_leg_length: float = Field(
        default=150.0, ge=50.0, le=1000.0, description="Nominal leg length in mm"
    )
    min_leg_length: float = Field(
        default=100.0, ge=10.0, le=1000.0, description="Minimum leg length in mm"
    )
    max_leg_length: float = Field(
        default=200.0, ge=10.0, le=2000.0, description="Maximum leg length in mm"
    )

    @validator("*")
    def check_finite(cls, v):
        """Ensure all values are finite"""
        if isinstance(v, (int, float)) and not math.isfinite(v):
            raise ValueError("Value must be finite (not NaN or Inf)")
        return v

    @validator("max_leg_length")
    def check_max_greater_than_min(cls, v, values):
        """Ensure max > min"""
        if "min_leg_length" in values and v <= values["min_leg_length"]:
            raise ValueError("max_leg_length must be greater than min_leg_length")
        return v


class PoseRequest(BaseModel):
    """Request for inverse kinematics calculation with strict validation"""

    x: float = Field(default=0.0, ge=-1000.0, le=1000.0, description="X translation in mm")
    y: float = Field(default=0.0, ge=-1000.0, le=1000.0, description="Y translation in mm")
    z: float = Field(default=0.0, ge=-500.0, le=500.0, description="Z translation in mm")
    roll: float = Field(default=0.0, ge=-90.0, le=90.0, description="Roll angle in degrees")
    pitch: float = Field(default=0.0, ge=-90.0, le=90.0, description="Pitch angle in degrees")
    yaw: float = Field(default=0.0, ge=-180.0, le=180.0, description="Yaw angle in degrees")

    configuration: Literal["3-3", "4-4", "6-3", "6-3-asymmetric", "6-3-redundant", "6-6", "8-8"] = (
        Field(default="6-3", description="Platform configuration")
    )

    geometry: Optional[PlatformConfigModel] = Field(
        default=None, description="Optional custom geometry parameters"
    )

    @validator("x", "y", "z", "roll", "pitch", "yaw")
    def check_finite(cls, v):
        """Ensure all pose values are finite"""
        if not math.isfinite(v):
            raise ValueError("Value must be finite (not NaN or Inf)")
        return v


class LegLengthResponse(BaseModel):
    """Response with calculated leg lengths"""

    leg_lengths: List[float] = Field(description="Leg lengths in mm")
    valid: bool = Field(description="Whether the solution is within limits")
    configuration: str = Field(description="Platform configuration used")
    pose: dict = Field(description="The requested pose")
    cached: bool = Field(default=False, description="Whether result was from cache")
    calculation_time_ms: float = Field(description="Calculation time in milliseconds")


class HealthResponse(BaseModel):
    """API health check response"""

    status: str
    message: str
    version: str
    environment: str
    timestamp: datetime
    services: dict


# Global configuration cache
current_config = PlatformConfigModel()


def get_configuration_mapping(config: str) -> dict:
    """Get base and platform point configurations for each setup"""
    configurations = {
        "3-3": {"num_base": 3, "num_platform": 3, "leg_pairs": list(range(3))},
        "4-4": {"num_base": 4, "num_platform": 4, "leg_pairs": list(range(4))},
        "6-3": {"num_base": 6, "num_platform": 3, "leg_pairs": [0, 0, 1, 1, 2, 2]},
        "6-3-asymmetric": {
            "num_base": 6,
            "num_platform": 3,
            "leg_pairs": [0, 1, 1, 2, 2, 0],
        },
        "6-3-redundant": {
            "num_base": 6,
            "num_platform": 3,
            "leg_pairs": [0, 1, 1, 2, 2, 0],
        },
        "6-6": {"num_base": 6, "num_platform": 6, "leg_pairs": list(range(6))},
        "8-8": {"num_base": 8, "num_platform": 8, "leg_pairs": list(range(8))},
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


def calculate_ik(pose: PoseRequest, request: Optional[Request] = None) -> dict:
    """
    Calculate inverse kinematics for given pose

    Args:
        pose: Pose request with configuration and geometry
        request: Optional FastAPI request object for logging

    Returns:
        Dictionary with leg lengths and metadata
    """
    start_time = time.time()

    try:
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
            np.pi / num_platform if num_platform < 6 else np.pi / 6,
        )

        # Create rotation matrix
        def rotation_matrix(roll, pitch, yaw):
            Rx = np.array(
                [
                    [1, 0, 0],
                    [0, np.cos(roll), -np.sin(roll)],
                    [0, np.sin(roll), np.cos(roll)],
                ]
            )

            Ry = np.array(
                [
                    [np.cos(pitch), 0, np.sin(pitch)],
                    [0, 1, 0],
                    [-np.sin(pitch), 0, np.cos(pitch)],
                ]
            )

            Rz = np.array(
                [
                    [np.cos(yaw), -np.sin(yaw), 0],
                    [np.sin(yaw), np.cos(yaw), 0],
                    [0, 0, 1],
                ]
            )

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
        valid = all(
            geometry.min_leg_length <= length <= geometry.max_leg_length for length in leg_lengths
        )

        calculation_time = (time.time() - start_time) * 1000  # ms

        result = {
            "leg_lengths": leg_lengths,
            "valid": valid,
            "configuration": pose.configuration,
            "pose": {
                "x": pose.x,
                "y": pose.y,
                "z": pose.z,
                "roll": pose.roll,
                "pitch": pose.pitch,
                "yaw": pose.yaw,
            },
            "calculation_time_ms": calculation_time,
        }

        logger.info(
            "IK calculation completed",
            extra={
                "configuration": pose.configuration,
                "valid": valid,
                "calculation_time_ms": calculation_time,
            },
        )

        return result

    except Exception as e:
        logger.error(f"IK calculation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


# API Endpoints


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with basic health info"""
    return HealthResponse(
        status="ok",
        message="Platform Leveling API is running",
        version="2.0.0",
        environment=settings.environment,
        timestamp=datetime.utcnow(),
        services={
            "cache": settings.redis_enabled,
            "database": settings.database_enabled,
            "auth": bool(settings.api_key),
        },
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Detailed health check with service status"""
    services = {
        "api": "healthy",
        "cache": "enabled" if settings.redis_enabled else "disabled",
        "database": "enabled" if settings.database_enabled else "disabled",
        "auth": "enabled" if settings.api_key else "disabled",
    }

    # Check cache if enabled
    if settings.redis_enabled:
        cache_stats = get_cache_stats()
        services["cache_stats"] = cache_stats

    return HealthResponse(
        status="healthy",
        message="All systems operational",
        version="2.0.0",
        environment=settings.environment,
        timestamp=datetime.utcnow(),
        services=services,
    )


@app.post("/calculate", response_model=LegLengthResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def calculate_leg_lengths(
    request: Request,
    pose: PoseRequest,
    api_key: Optional[str] = Depends(optional_api_key),
):
    """
    Calculate inverse kinematics for a given pose

    Returns the required leg lengths to achieve the specified position and orientation.
    Results are cached for improved performance.
    """
    # Check cache first
    cache_key = generate_cache_key("ik", pose.dict())
    cached_result = get_cached(cache_key)

    if cached_result:
        cached_result["cached"] = True
        return LegLengthResponse(**cached_result)

    # Calculate IK
    result = calculate_ik(pose, request)
    result["cached"] = False

    # Cache the result
    set_cached(cache_key, result, expiration=300)  # 5 minutes

    return LegLengthResponse(**result)


@app.post("/level")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def calculate_leveling(
    request: Request,
    roll: float = Field(description="Current roll angle in degrees"),
    pitch: float = Field(description="Current pitch angle in degrees"),
    yaw: float = Field(default=0.0, description="Current yaw angle in degrees"),
    configuration: str = Field(default="6-3", description="Platform configuration"),
):
    """
    Calculate leg lengths needed to level the platform

    Given current orientation, returns leg lengths to achieve level position
    """
    # To level, we apply opposite rotation
    pose = PoseRequest(
        x=0,
        y=0,
        z=0,
        roll=-roll,
        pitch=-pitch,
        yaw=-yaw,
        configuration=configuration,
    )

    result = calculate_ik(pose, request)
    result["cached"] = False
    return LegLengthResponse(**result)


@app.get("/config", response_model=PlatformConfigModel)
async def get_config():
    """Get current platform configuration"""
    return current_config


@app.post("/config", response_model=PlatformConfigModel)
async def update_config(config: PlatformConfigModel, api_key: str = Depends(verify_api_key)):
    """Update platform configuration (requires authentication)"""
    global current_config
    current_config = config

    logger.info(
        "Configuration updated",
        extra={
            "base_radius": config.base_radius,
            "platform_radius": config.platform_radius,
            "nominal_leg_length": config.nominal_leg_length,
        },
    )

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
                "num_legs": 3,
            },
            {
                "id": "4-4",
                "name": "4-4 Square",
                "description": "4 base points, 4 platform points - square configuration",
                "num_legs": 4,
            },
            {
                "id": "6-3",
                "name": "6-3 Standard",
                "description": "6 base points, 3 platform points - standard pairing",
                "num_legs": 6,
            },
            {
                "id": "6-3-asymmetric",
                "name": "6-3 Asymmetric",
                "description": "6 base points, 3 platform points - asymmetric pairing",
                "num_legs": 6,
            },
            {
                "id": "6-3-redundant",
                "name": "6-3 Redundant",
                "description": "6 base points, 3 platform points - redundant configuration",
                "num_legs": 6,
            },
            {
                "id": "6-6",
                "name": "6-6 Hexagonal",
                "description": "6 base points, 6 platform points - classic Stewart platform",
                "num_legs": 6,
            },
            {
                "id": "8-8",
                "name": "8-8 Octagonal",
                "description": "8 base points, 8 platform points - maximum redundancy",
                "num_legs": 8,
            },
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
    logger.info("WebSocket client connected")

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
            await websocket.send_json(result)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("Starting Platform Leveling API (Production Ready)")
    print("=" * 60)
    print(f"Environment: {settings.environment}")
    print(f"API URL: http://{settings.api_host}:{settings.api_port}")
    print(f"Docs: http://{settings.api_host}:{settings.api_port}/docs")
    print(f"Metrics: http://{settings.api_host}:{settings.api_port}/metrics")
    print("=" * 60)

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )

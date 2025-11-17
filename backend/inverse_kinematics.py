"""
Inverse Kinematics Solver for Platform Leveling
Supports both 3-actuator tripod and Stewart platform (3-DOF/6-DOF)
"""

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


@dataclass
class PlatformConfig:
    """Configuration for platform geometry"""

    length: float  # meters (platform length)
    width: float  # meters (platform width)
    min_height: float  # meters (minimum platform height)
    max_height: float  # meters (maximum platform height)
    actuator_stroke: float  # meters (maximum actuator extension)


class TripodIK:
    """
    Inverse kinematics for 3-actuator tripod configuration

    Three actuators positioned at vertices of a triangle define a plane.
    The platform can achieve roll and pitch control (2-DOF).

    Coordinate system:
    - Origin at center of platform when level
    - X: along length (forward)
    - Y: along width (sideways)
    - Z: vertical (up)
    """

    def __init__(self, config: PlatformConfig):
        self.config = config

        # Define actuator mounting points on base (fixed frame)
        # Triangular configuration for stability
        # Format: [x, y, z] in meters
        self.base_points = np.array(
            [
                [config.length / 3, 0, 0],  # Front center
                [-config.length / 6, config.width / 2, 0],  # Rear right
                [-config.length / 6, -config.width / 2, 0],  # Rear left
            ]
        )

        # Corresponding attachment points on platform (moving frame)
        # When level, these are at height = min_height
        self.platform_points = np.array(
            [
                [config.length / 3, 0, config.min_height],
                [-config.length / 6, config.width / 2, config.min_height],
                [-config.length / 6, -config.width / 2, config.min_height],
            ]
        )

        print("Tripod IK initialized:")
        print(f"  Platform: {config.length*1000:.0f}mm x {config.width*1000:.0f}mm")
        print(f"  Height range: {config.min_height*1000:.0f}mm - {config.max_height*1000:.0f}mm")
        print(f"  Actuator stroke: {config.actuator_stroke*1000:.0f}mm")

    def rotation_matrix(self, roll: float, pitch: float, yaw: float = 0) -> np.ndarray:
        """
        Create rotation matrix from Euler angles (in radians)
        Order: Yaw (Z) -> Pitch (Y) -> Roll (X)
        """
        # Roll (rotation about X)
        Rx = np.array(
            [[1, 0, 0], [0, np.cos(roll), -np.sin(roll)], [0, np.sin(roll), np.cos(roll)]]
        )

        # Pitch (rotation about Y)
        Ry = np.array(
            [[np.cos(pitch), 0, np.sin(pitch)], [0, 1, 0], [-np.sin(pitch), 0, np.cos(pitch)]]
        )

        # Yaw (rotation about Z)
        Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])

        # Combined rotation: R = Rz * Ry * Rx
        return Rz @ Ry @ Rx

    def solve(
        self, roll: float, pitch: float, yaw: float = 0, height_offset: float = 0
    ) -> Tuple[np.ndarray, bool]:
        """
        Solve inverse kinematics for desired orientation

        Args:
            roll: Roll angle in radians (rotation about X)
            pitch: Pitch angle in radians (rotation about Y)
            yaw: Yaw angle in radians (rotation about Z) - not used in tripod
            height_offset: Additional vertical offset in meters

        Returns:
            actuator_lengths: Array of 3 actuator lengths in meters
            valid: Boolean indicating if solution is within limits
        """
        # Get rotation matrix
        R = self.rotation_matrix(roll, pitch, yaw)

        # Center position of platform (when level)
        center = np.array([0, 0, self.config.min_height + height_offset])

        # Calculate rotated platform points
        rotated_platform_points = []
        for point in self.platform_points:
            # Translate to origin, rotate, translate back
            local_point = point - center
            rotated_point = R @ local_point + center
            rotated_platform_points.append(rotated_point)

        rotated_platform_points = np.array(rotated_platform_points)

        # Calculate actuator lengths (distance from base to platform attachment)
        actuator_lengths = np.linalg.norm(rotated_platform_points - self.base_points, axis=1)

        # Check if solution is valid (within actuator stroke limits)
        min_length = self.config.min_height
        max_length = self.config.min_height + self.config.actuator_stroke

        valid = np.all(actuator_lengths >= min_length) and np.all(actuator_lengths <= max_length)

        return actuator_lengths, valid

    def level_platform(
        self, measured_roll: float, measured_pitch: float
    ) -> Tuple[np.ndarray, bool]:
        """
        Calculate actuator lengths to level platform

        Args:
            measured_roll: Current roll angle in radians
            measured_pitch: Current pitch angle in radians

        Returns:
            actuator_lengths: Required actuator lengths to achieve level
            valid: Boolean indicating if solution is achievable
        """
        # To level, we need to apply opposite rotation
        return self.solve(-measured_roll, -measured_pitch)

    def get_actuator_positions(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get base and platform attachment points for visualization"""
        return self.base_points, self.platform_points


class StewartPlatformIK:
    """
    Inverse kinematics for Stewart Platform (6-DOF or 3-DOF)

    Six actuators in pairs provide full 6-DOF control:
    - Translation: X, Y, Z
    - Rotation: Roll, Pitch, Yaw

    For 3-DOF mode, we only use Z translation + Roll + Pitch
    """

    def __init__(self, config: PlatformConfig, dof_mode: str = "3DOF"):
        self.config = config
        self.dof_mode = dof_mode  # '3DOF' or '6DOF'

        # Define actuator mounting points - hexagonal pattern
        # Base platform (fixed) - 6 points in hexagonal arrangement
        angle_offset = np.pi / 6  # 30 degrees
        base_radius = min(config.length, config.width) / 3

        self.base_points = []
        for i in range(6):
            angle = 2 * np.pi * i / 6 + angle_offset
            x = base_radius * np.cos(angle)
            y = base_radius * np.sin(angle)
            self.base_points.append([x, y, 0])
        self.base_points = np.array(self.base_points)

        # Platform attachment points (moving) - slightly smaller hexagon
        platform_radius = base_radius * 0.8
        self.platform_points = []
        for i in range(6):
            angle = 2 * np.pi * i / 6 + angle_offset + np.pi / 6  # Offset by 30°
            x = platform_radius * np.cos(angle)
            y = platform_radius * np.sin(angle)
            self.platform_points.append([x, y, config.min_height])
        self.platform_points = np.array(self.platform_points)

        print(f"Stewart Platform IK initialized ({dof_mode}):")
        print(f"  Platform: {config.length*1000:.0f}mm x {config.width*1000:.0f}mm")
        print(f"  Height range: {config.min_height*1000:.0f}mm - {config.max_height*1000:.0f}mm")
        print(f"  Actuator stroke: {config.actuator_stroke*1000:.0f}mm")
        print(f"  Base radius: {base_radius*1000:.0f}mm")

    def rotation_matrix(self, roll: float, pitch: float, yaw: float) -> np.ndarray:
        """Create rotation matrix from Euler angles (in radians)"""
        # Same as TripodIK
        Rx = np.array(
            [[1, 0, 0], [0, np.cos(roll), -np.sin(roll)], [0, np.sin(roll), np.cos(roll)]]
        )

        Ry = np.array(
            [[np.cos(pitch), 0, np.sin(pitch)], [0, 1, 0], [-np.sin(pitch), 0, np.cos(pitch)]]
        )

        Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])

        return Rz @ Ry @ Rx

    def solve(
        self,
        roll: float,
        pitch: float,
        yaw: float,
        x_offset: float = 0,
        y_offset: float = 0,
        z_offset: float = 0,
    ) -> Tuple[np.ndarray, bool]:
        """
        Solve inverse kinematics for desired pose

        Args:
            roll, pitch, yaw: Rotation angles in radians
            x_offset, y_offset, z_offset: Translation offsets in meters

        Returns:
            actuator_lengths: Array of 6 actuator lengths in meters
            valid: Boolean indicating if solution is within limits
        """
        # Get rotation matrix
        R = self.rotation_matrix(roll, pitch, yaw)

        # Center position of platform
        center = np.array([x_offset, y_offset, self.config.min_height + z_offset])

        # Calculate rotated and translated platform points
        rotated_platform_points = []
        for point in self.platform_points:
            # Translate to origin, rotate, translate to desired position
            local_point = point - np.array([0, 0, self.config.min_height])
            rotated_point = R @ local_point + center
            rotated_platform_points.append(rotated_point)

        rotated_platform_points = np.array(rotated_platform_points)

        # Calculate actuator lengths
        actuator_lengths = np.linalg.norm(rotated_platform_points - self.base_points, axis=1)

        # Check validity
        min_length = self.config.min_height
        max_length = self.config.min_height + self.config.actuator_stroke

        valid = np.all(actuator_lengths >= min_length) and np.all(actuator_lengths <= max_length)

        return actuator_lengths, valid

    def level_platform(
        self, measured_roll: float, measured_pitch: float, measured_yaw: float = 0
    ) -> Tuple[np.ndarray, bool]:
        """
        Calculate actuator lengths to level platform

        Args:
            measured_roll, measured_pitch: Current angles in radians
            measured_yaw: Current yaw (used in 6-DOF mode)

        Returns:
            actuator_lengths: Required actuator lengths
            valid: Boolean indicating if solution is achievable
        """
        if self.dof_mode == "3DOF":
            # Only correct roll and pitch
            return self.solve(-measured_roll, -measured_pitch, 0)
        else:
            # Full 6-DOF correction
            return self.solve(-measured_roll, -measured_pitch, -measured_yaw)

    def get_actuator_positions(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get base and platform attachment points for visualization"""
        return self.base_points, self.platform_points


# Test both configurations
if __name__ == "__main__":
    # Define platform configuration
    config = PlatformConfig(
        length=1.83,  # 6 feet in meters
        width=1.22,  # 4 feet in meters
        min_height=0.3,  # 300mm minimum
        max_height=0.7,  # 700mm maximum
        actuator_stroke=0.4,  # 400mm stroke
    )

    print("=" * 60)
    print("TRIPOD CONFIGURATION TEST")
    print("=" * 60)

    tripod = TripodIK(config)

    # Test: Level platform
    lengths, valid = tripod.solve(0, 0, 0)
    print(f"\nLevel position:")
    print(f"  Actuator lengths: {lengths * 1000:.1f} mm")
    print(f"  Valid: {valid}")

    # Test: 10 degree pitch
    pitch_10deg = np.deg2rad(10)
    lengths, valid = tripod.solve(0, pitch_10deg, 0)
    print(f"\n10° pitch:")
    print(f"  Actuator lengths: {lengths * 1000} mm")
    print(f"  Valid: {valid}")

    # Test: 10 degree roll
    roll_10deg = np.deg2rad(10)
    lengths, valid = tripod.solve(roll_10deg, 0, 0)
    print(f"\n10° roll:")
    print(f"  Actuator lengths: {lengths * 1000} mm")
    print(f"  Valid: {valid}")

    print("\n" + "=" * 60)
    print("STEWART PLATFORM CONFIGURATION TEST (3-DOF)")
    print("=" * 60)

    stewart_3dof = StewartPlatformIK(config, dof_mode="3DOF")

    # Test: Level platform
    lengths, valid = stewart_3dof.solve(0, 0, 0)
    print(f"\nLevel position:")
    print(f"  Actuator lengths: {lengths * 1000} mm")
    print(f"  Valid: {valid}")

    # Test: 10 degree pitch
    lengths, valid = stewart_3dof.solve(0, pitch_10deg, 0)
    print(f"\n10° pitch:")
    print(f"  Actuator lengths: {lengths * 1000} mm")
    print(f"  Valid: {valid}")

    # Test: Combined roll and pitch
    lengths, valid = stewart_3dof.solve(roll_10deg, pitch_10deg, 0)
    print(f"\n10° roll + 10° pitch:")
    print(f"  Actuator lengths: {lengths * 1000} mm")
    print(f"  Valid: {valid}")

    print("\n" + "=" * 60)
    print("STEWART PLATFORM CONFIGURATION TEST (6-DOF)")
    print("=" * 60)

    stewart_6dof = StewartPlatformIK(config, dof_mode="6DOF")

    # Test with yaw
    yaw_15deg = np.deg2rad(15)
    lengths, valid = stewart_6dof.solve(roll_10deg, pitch_10deg, yaw_15deg)
    print(f"\n10° roll + 10° pitch + 15° yaw:")
    print(f"  Actuator lengths: {lengths * 1000} mm")
    print(f"  Valid: {valid}")

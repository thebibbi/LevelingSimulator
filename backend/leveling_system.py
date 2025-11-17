"""
Integrated Platform Leveling System
Combines IMU data, inverse kinematics, and ESP32 controller
"""

import struct
import threading
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np

from esp32_controller import ESP32Controller, SerialProtocol
from imu_streamer import IMUStreamer
from inverse_kinematics import PlatformConfig, StewartPlatformIK, TripodIK


@dataclass
class LevelingConfig:
    """Configuration for leveling system"""

    level_threshold: float = 2.0  # degrees - acceptable tilt
    update_rate: float = 2.0  # Hz - how often to update actuators
    deadband: float = 0.5  # degrees - ignore changes smaller than this
    max_correction_rate: float = 5.0  # degrees/second - max rate of correction


class PlatformLevelingSystem:
    """
    Complete platform leveling system

    Integrates:
    - IMU sensor (BNO055 or iPhone for testing)
    - Inverse kinematics solver
    - ESP32 controller with actuators
    """

    def __init__(
        self,
        platform_type: str = "tripod",
        config: Optional[PlatformConfig] = None,
        leveling_config: Optional[LevelingConfig] = None,
        use_iphone_imu: bool = False,
    ):
        """
        Args:
            platform_type: 'tripod', 'stewart_3dof', or 'stewart_6dof'
            config: Platform physical configuration
            leveling_config: Leveling algorithm configuration
            use_iphone_imu: Use iPhone IMU (True) or BNO055 (False)
        """
        # Default configurations
        if config is None:
            config = PlatformConfig(
                length=1.83, width=1.22, min_height=0.3, max_height=0.7, actuator_stroke=0.4
            )

        if leveling_config is None:
            leveling_config = LevelingConfig()

        self.config = config
        self.leveling_config = leveling_config
        self.platform_type = platform_type

        # Initialize subsystems
        print("Initializing Platform Leveling System...")
        print("=" * 60)

        # 1. Inverse Kinematics
        if platform_type == "tripod":
            self.ik_solver = TripodIK(config)
            num_actuators = 3
        elif platform_type == "stewart_3dof":
            self.ik_solver = StewartPlatformIK(config, dof_mode="3DOF")
            num_actuators = 6
        elif platform_type == "stewart_6dof":
            self.ik_solver = StewartPlatformIK(config, dof_mode="6DOF")
            num_actuators = 6
        else:
            raise ValueError(f"Unknown platform type: {platform_type}")

        # 2. IMU Sensor
        if use_iphone_imu:
            print("\nUsing iPhone IMU (for testing)...")
            self.imu = IMUStreamer()
            self.imu.start()
        else:
            print("\nUsing BNO055 IMU (production)...")
            # TODO: Initialize BNO055 via I2C
            # For now, use iPhone as fallback
            self.imu = IMUStreamer()
            self.imu.start()

        # 3. ESP32 Controller
        print("\nInitializing ESP32 Controller...")
        self.controller = ESP32Controller(
            num_actuators=num_actuators,
            stroke_mm=config.actuator_stroke * 1000,
            min_position_mm=config.min_height * 1000,
            max_position_mm=config.max_height * 1000,
        )
        self.controller.start()

        # 4. Serial protocol
        self.protocol = SerialProtocol(self.controller)
        self.protocol.connect(simulated=True)

        # State variables
        self.leveling_enabled = False
        self.auto_level_enabled = False
        self.last_orientation = np.array([0.0, 0.0, 0.0])  # roll, pitch, yaw
        self.leveling_thread: Optional[threading.Thread] = None
        self.running = False

        print("\n" + "=" * 60)
        print("System initialized successfully!")
        print("=" * 60)

    def calibrate_imu(self):
        """Calibrate IMU to set current position as level"""
        print("\nCalibrating IMU...")
        self.imu.calibrate()
        print("IMU calibrated")

    def calibrate_actuators(self):
        """Run actuator calibration (move to home position)"""
        print("\nCalibrating actuators...")
        self.protocol.send_command(ESP32Controller.CMD_CALIBRATE, b"")
        time.sleep(5)  # Wait for calibration to complete
        print("Actuators calibrated")

    def enable_leveling(self, enable: bool = True):
        """Enable or disable active leveling"""
        self.leveling_enabled = enable

        if enable:
            # Enable actuators
            self.protocol.send_command(ESP32Controller.CMD_ENABLE, struct.pack("B", 1))
            print("Leveling ENABLED")
        else:
            # Disable actuators
            self.protocol.send_command(ESP32Controller.CMD_ENABLE, struct.pack("B", 0))
            print("Leveling DISABLED")

    def enable_auto_level(self, enable: bool = True):
        """Enable or disable automatic continuous leveling"""
        self.auto_level_enabled = enable

        if enable and not self.running:
            self.running = True
            self.leveling_thread = threading.Thread(target=self._auto_level_loop, daemon=True)
            self.leveling_thread.start()
            print("Auto-leveling ENABLED")
        elif not enable:
            print("Auto-leveling DISABLED")

    def level_once(self):
        """Perform single leveling operation"""
        imu_data = self.imu.get_latest()

        if imu_data is None:
            print("No IMU data available")
            return False

        # Convert to radians
        roll = np.deg2rad(imu_data.roll)
        pitch = np.deg2rad(imu_data.pitch)
        yaw = np.deg2rad(imu_data.yaw)

        # Check if leveling is needed
        tilt_magnitude = np.sqrt(imu_data.roll**2 + imu_data.pitch**2)

        if tilt_magnitude < self.leveling_config.level_threshold:
            print(f"Platform already level (tilt: {tilt_magnitude:.2f}°)")
            return True

        print(f"Leveling platform (tilt: {tilt_magnitude:.2f}°)...")
        print(f"  Current orientation: Roll={imu_data.roll:.2f}°, Pitch={imu_data.pitch:.2f}°")

        # Calculate required actuator positions
        if self.platform_type == "tripod":
            actuator_lengths, valid = self.ik_solver.level_platform(roll, pitch)
        else:
            actuator_lengths, valid = self.ik_solver.level_platform(roll, pitch, yaw)

        if not valid:
            print("ERROR: Cannot level - solution outside actuator limits")
            return False

        # Convert to mm
        targets_mm = actuator_lengths * 1000

        print(f"  Target positions: {[f'{t:.1f}' for t in targets_mm]} mm")

        # Send to controller
        data = struct.pack(f"{len(targets_mm)}f", *targets_mm)
        self.protocol.send_command(ESP32Controller.CMD_SET_TARGET, data)

        return True

    def _auto_level_loop(self):
        """Automatic leveling loop (runs in background)"""
        dt = 1.0 / self.leveling_config.update_rate

        while self.running and self.auto_level_enabled:
            start_time = time.time()

            if self.leveling_enabled:
                imu_data = self.imu.get_latest()

                if imu_data:
                    # Get current orientation
                    current_orientation = np.array([imu_data.roll, imu_data.pitch, imu_data.yaw])

                    # Check if change exceeds deadband
                    orientation_change = np.linalg.norm(current_orientation - self.last_orientation)

                    if orientation_change > self.leveling_config.deadband:
                        # Check tilt magnitude
                        tilt_mag = np.sqrt(imu_data.roll**2 + imu_data.pitch**2)

                        if tilt_mag > self.leveling_config.level_threshold:
                            # Level the platform
                            self.level_once()
                            self.last_orientation = current_orientation

            # Sleep to maintain update rate
            elapsed = time.time() - start_time
            sleep_time = max(0, dt - elapsed)
            time.sleep(sleep_time)

    def get_status(self) -> dict:
        """Get complete system status"""
        imu_data = self.imu.get_latest()
        controller_status = self.controller.get_status()

        status = {
            "leveling_enabled": self.leveling_enabled,
            "auto_level_enabled": self.auto_level_enabled,
            "imu": {
                "roll": imu_data.roll if imu_data else None,
                "pitch": imu_data.pitch if imu_data else None,
                "yaw": imu_data.yaw if imu_data else None,
                "tilt_magnitude": (
                    np.sqrt(imu_data.roll**2 + imu_data.pitch**2) if imu_data else None
                ),
            },
            "controller": controller_status,
        }

        return status

    def shutdown(self):
        """Shutdown the system"""
        print("\nShutting down system...")

        self.running = False
        self.auto_level_enabled = False

        if self.leveling_thread:
            self.leveling_thread.join()

        # Disable actuators
        self.enable_leveling(False)

        # Stop subsystems
        self.controller.stop()
        self.imu.stop()

        print("System shutdown complete")


# Command-line interface
def main():
    import sys

    print("=" * 60)
    print("PLATFORM LEVELING SYSTEM")
    print("=" * 60)

    # Parse arguments
    platform_type = "tripod"
    if len(sys.argv) > 1:
        platform_type = sys.argv[1].lower()

    # Create system
    system = PlatformLevelingSystem(
        platform_type=platform_type, use_iphone_imu=True  # Use iPhone for testing
    )

    print("\nCommands:")
    print("  'c' - Calibrate IMU")
    print("  'a' - Calibrate actuators")
    print("  'e' - Enable/disable leveling")
    print("  'l' - Level once")
    print("  'auto' - Enable/disable auto-leveling")
    print("  's' - Show status")
    print("  'q' - Quit")
    print()

    try:
        while True:
            cmd = input("> ").strip().lower()

            if cmd == "c":
                system.calibrate_imu()

            elif cmd == "a":
                system.calibrate_actuators()

            elif cmd == "e":
                system.leveling_enabled = not system.leveling_enabled
                system.enable_leveling(system.leveling_enabled)

            elif cmd == "l":
                if not system.leveling_enabled:
                    print("Enable leveling first (press 'e')")
                else:
                    system.level_once()

            elif cmd == "auto":
                system.auto_level_enabled = not system.auto_level_enabled
                system.enable_auto_level(system.auto_level_enabled)

            elif cmd == "s":
                status = system.get_status()
                print("\nSystem Status:")
                print(f"  Leveling: {'ENABLED' if status['leveling_enabled'] else 'DISABLED'}")
                print(f"  Auto-level: {'ENABLED' if status['auto_level_enabled'] else 'DISABLED'}")

                if status["imu"]["roll"] is not None:
                    print(f"\n  IMU:")
                    print(f"    Roll:  {status['imu']['roll']:7.2f}°")
                    print(f"    Pitch: {status['imu']['pitch']:7.2f}°")
                    print(f"    Yaw:   {status['imu']['yaw']:7.2f}°")
                    print(f"    Tilt:  {status['imu']['tilt_magnitude']:7.2f}°")

                print(f"\n  Controller:")
                print(
                    f"    Positions: {[f'{p:.1f}' for p in status['controller']['positions']]} mm"
                )
                print(f"    Targets:   {[f'{t:.1f}' for t in status['controller']['targets']]} mm")
                print()

            elif cmd == "q":
                break

            else:
                print("Unknown command")

    except KeyboardInterrupt:
        print()

    finally:
        system.shutdown()


if __name__ == "__main__":
    main()

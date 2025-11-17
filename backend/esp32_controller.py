"""
ESP32 Controller Simulator
Simulates the ESP32 microcontroller communication protocol and control logic
"""

import serial
import time
import numpy as np
from typing import Optional, Callable
from dataclasses import dataclass
import threading
import struct


@dataclass
class ActuatorState:
    """State of a single actuator"""
    position: float  # Current position in mm
    target: float    # Target position in mm
    speed: float     # Movement speed in mm/s
    current: float   # Current draw in amps
    limit_min: bool  # Min limit switch triggered
    limit_max: bool  # Max limit switch triggered
    enabled: bool    # Actuator enabled


class ESP32Controller:
    """
    ESP32 Controller for Platform Leveling
    
    This class simulates the ESP32 microcontroller that controls the actuators.
    In production, this would be replaced with actual ESP32 firmware.
    
    Communication Protocol (Binary over Serial):
    - Commands from PC to ESP32
    - Status/telemetry from ESP32 to PC
    """
    
    # Command bytes
    CMD_SET_TARGET = 0x01      # Set target positions for all actuators
    CMD_ENABLE = 0x02          # Enable/disable actuators
    CMD_EMERGENCY_STOP = 0x03  # Emergency stop
    CMD_GET_STATUS = 0x04      # Request status
    CMD_CALIBRATE = 0x05       # Run calibration routine
    CMD_SET_SPEED = 0x06       # Set movement speed
    
    # Response bytes
    RESP_STATUS = 0x10
    RESP_ACK = 0x11
    RESP_ERROR = 0x12
    
    def __init__(self, num_actuators: int = 3, stroke_mm: float = 400,
                 min_position_mm: float = 300, max_position_mm: float = 700):
        """
        Args:
            num_actuators: Number of actuators (3 or 6)
            stroke_mm: Actuator stroke length in mm
            min_position_mm: Minimum actuator length
            max_position_mm: Maximum actuator length
        """
        self.num_actuators = num_actuators
        self.stroke_mm = stroke_mm
        self.min_position = min_position_mm
        self.max_position = max_position_mm
        
        # Initialize actuator states
        self.actuators = []
        for i in range(num_actuators):
            self.actuators.append(ActuatorState(
                position=min_position_mm,
                target=min_position_mm,
                speed=20.0,  # mm/s default
                current=0.0,
                limit_min=True,
                limit_max=False,
                enabled=False
            ))
        
        # Control state
        self.emergency_stop = False
        self.calibrated = False
        
        # Simulation parameters
        self.update_rate = 50  # Hz
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Callbacks for external monitoring
        self.position_callback: Optional[Callable] = None
        
        print(f"ESP32 Controller initialized:")
        print(f"  Actuators: {num_actuators}")
        print(f"  Stroke: {stroke_mm}mm")
        print(f"  Range: {min_position_mm}mm - {max_position_mm}mm")
    
    def start(self):
        """Start the controller simulation"""
        self.running = True
        self.thread = threading.Thread(target=self._control_loop, daemon=True)
        self.thread.start()
        print("Controller started")
    
    def stop(self):
        """Stop the controller"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("Controller stopped")
    
    def _control_loop(self):
        """Main control loop (runs in background thread)"""
        dt = 1.0 / self.update_rate
        
        while self.running:
            start_time = time.time()
            
            if not self.emergency_stop:
                # Update each actuator
                for actuator in self.actuators:
                    if actuator.enabled:
                        self._update_actuator(actuator, dt)
            
            # Call position callback if registered
            if self.position_callback:
                positions = [a.position for a in self.actuators]
                self.position_callback(positions)
            
            # Sleep to maintain update rate
            elapsed = time.time() - start_time
            sleep_time = max(0, dt - elapsed)
            time.sleep(sleep_time)
    
    def _update_actuator(self, actuator: ActuatorState, dt: float):
        """Update single actuator position"""
        # Calculate position error
        error = actuator.target - actuator.position
        
        if abs(error) < 0.5:  # Within 0.5mm is close enough
            return
        
        # Calculate movement
        max_movement = actuator.speed * dt
        movement = np.clip(error, -max_movement, max_movement)
        
        # Update position
        new_position = actuator.position + movement
        
        # Check limits
        if new_position <= self.min_position:
            new_position = self.min_position
            actuator.limit_min = True
        else:
            actuator.limit_min = False
        
        if new_position >= self.max_position:
            new_position = self.max_position
            actuator.limit_max = True
        else:
            actuator.limit_max = False
        
        actuator.position = new_position
        
        # Simulate current draw (proportional to speed and load)
        if abs(movement) > 0.1:
            actuator.current = 0.5 + abs(movement) * 0.1  # Simplified model
        else:
            actuator.current = 0.1  # Holding current
    
    def set_targets(self, targets_mm: list):
        """
        Set target positions for all actuators
        
        Args:
            targets_mm: List of target positions in mm
        """
        if len(targets_mm) != self.num_actuators:
            raise ValueError(f"Expected {self.num_actuators} targets, got {len(targets_mm)}")
        
        for i, target in enumerate(targets_mm):
            # Clamp target to valid range
            clamped = np.clip(target, self.min_position, self.max_position)
            self.actuators[i].target = clamped
            
            if clamped != target:
                print(f"Warning: Target {i} clamped from {target:.1f} to {clamped:.1f}mm")
    
    def enable_actuators(self, enable: bool = True):
        """Enable or disable all actuators"""
        for actuator in self.actuators:
            actuator.enabled = enable
        
        status = "enabled" if enable else "disabled"
        print(f"All actuators {status}")
    
    def emergency_stop_trigger(self):
        """Trigger emergency stop"""
        self.emergency_stop = True
        self.enable_actuators(False)
        print("EMERGENCY STOP TRIGGERED")
    
    def reset_emergency_stop(self):
        """Reset emergency stop"""
        self.emergency_stop = False
        print("Emergency stop reset")
    
    def get_positions(self) -> list:
        """Get current positions of all actuators"""
        return [a.position for a in self.actuators]
    
    def get_status(self) -> dict:
        """Get complete status of all actuators"""
        return {
            'positions': [a.position for a in self.actuators],
            'targets': [a.target for a in self.actuators],
            'currents': [a.current for a in self.actuators],
            'enabled': [a.enabled for a in self.actuators],
            'limit_min': [a.limit_min for a in self.actuators],
            'limit_max': [a.limit_max for a in self.actuators],
            'emergency_stop': self.emergency_stop,
            'calibrated': self.calibrated
        }
    
    def calibrate(self):
        """Run calibration routine (move to home position)"""
        print("Starting calibration...")
        
        # Move all actuators to minimum position
        self.enable_actuators(True)
        home_positions = [self.min_position] * self.num_actuators
        self.set_targets(home_positions)
        
        # Wait for movement to complete
        max_wait = 30  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            positions = self.get_positions()
            errors = [abs(p - t) for p, t in zip(positions, home_positions)]
            
            if all(e < 1.0 for e in errors):  # Within 1mm
                break
            
            time.sleep(0.1)
        
        self.calibrated = True
        print("Calibration complete")
    
    def set_speed(self, speed_mm_s: float):
        """Set movement speed for all actuators"""
        for actuator in self.actuators:
            actuator.speed = speed_mm_s
        print(f"Speed set to {speed_mm_s} mm/s")


class SerialProtocol:
    """
    Serial communication protocol for ESP32
    
    This would handle actual serial communication in production.
    For simulation, we use direct function calls.
    """
    
    def __init__(self, controller: ESP32Controller, port: str = '/dev/ttyUSB0', 
                 baudrate: int = 115200):
        self.controller = controller
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        
    def connect(self, simulated: bool = True):
        """Connect to ESP32 (or simulate connection)"""
        if simulated:
            print(f"Simulated serial connection on {self.port}")
            return True
        
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"Connected to {self.port} at {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect: {e}")
            return False
    
    def send_command(self, command: int, data: bytes = b''):
        """Send command to ESP32"""
        if self.serial_conn:
            # Binary protocol: [START_BYTE][COMMAND][LENGTH][DATA][CHECKSUM]
            packet = struct.pack('BBB', 0xAA, command, len(data)) + data
            checksum = sum(packet) & 0xFF
            packet += struct.pack('B', checksum)
            self.serial_conn.write(packet)
        else:
            # Simulated mode - execute directly
            self._execute_command(command, data)
    
    def _execute_command(self, command: int, data: bytes):
        """Execute command directly (simulation mode)"""
        if command == ESP32Controller.CMD_SET_TARGET:
            # Data format: float32 for each actuator
            num_actuators = len(data) // 4
            targets = struct.unpack(f'{num_actuators}f', data)
            self.controller.set_targets(list(targets))
            
        elif command == ESP32Controller.CMD_ENABLE:
            enable = struct.unpack('B', data)[0] == 1
            self.controller.enable_actuators(enable)
            
        elif command == ESP32Controller.CMD_EMERGENCY_STOP:
            self.controller.emergency_stop_trigger()
            
        elif command == ESP32Controller.CMD_CALIBRATE:
            self.controller.calibrate()
            
        elif command == ESP32Controller.CMD_SET_SPEED:
            speed = struct.unpack('f', data)[0]
            self.controller.set_speed(speed)


# Test/demo
if __name__ == "__main__":
    # Create controller
    controller = ESP32Controller(num_actuators=3)
    controller.start()
    
    # Create protocol handler
    protocol = SerialProtocol(controller)
    protocol.connect(simulated=True)
    
    print("\nTesting controller...")
    
    # Enable actuators
    protocol.send_command(ESP32Controller.CMD_ENABLE, struct.pack('B', 1))
    time.sleep(0.5)
    
    # Set targets
    targets = [350.0, 400.0, 375.0]  # mm
    data = struct.pack('3f', *targets)
    protocol.send_command(ESP32Controller.CMD_SET_TARGET, data)
    
    print(f"Moving to targets: {targets}")
    
    # Monitor progress
    for i in range(50):
        status = controller.get_status()
        positions = status['positions']
        print(f"\rPositions: {[f'{p:.1f}' for p in positions]} mm", end='')
        time.sleep(0.1)
    
    print("\n\nFinal status:")
    status = controller.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    controller.stop()

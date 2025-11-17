"""
iPhone IMU Data Streamer
Receives IMU data from iPhone via UDP and broadcasts to simulation

On iPhone, use an app like "Sensor Logger" or "UDP Sender" to stream IMU data
Expected format: JSON with roll, pitch, yaw in degrees

Example apps:
- iOS: "Sensor Logger" or "UDP Sender" 
- Send to computer's IP on port 5555
"""

import socket
import json
import struct
import numpy as np
from dataclasses import dataclass
from typing import Optional
import threading
import time


@dataclass
class IMUData:
    """Container for IMU orientation data"""
    roll: float   # degrees, rotation about X axis
    pitch: float  # degrees, rotation about Y axis
    yaw: float    # degrees, rotation about Z axis
    timestamp: float
    
    def to_radians(self):
        """Convert angles to radians"""
        return np.array([
            np.deg2rad(self.roll),
            np.deg2rad(self.pitch),
            np.deg2rad(self.yaw)
        ])


class IMUStreamer:
    """Receives and processes IMU data from iPhone via UDP"""
    
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.settimeout(0.1)  # Non-blocking with timeout
        
        self.latest_data: Optional[IMUData] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Calibration offsets (set when platform is level)
        self.roll_offset = 0.0
        self.pitch_offset = 0.0
        self.yaw_offset = 0.0
        
        print(f"IMU Streamer initialized on {host}:{port}")
        print("Waiting for iPhone IMU data...")
        print("\nOn your iPhone:")
        print("1. Download 'Sensor Logger' or similar IMU streaming app")
        print("2. Set target IP to your computer's IP address")
        print(f"3. Set target port to {port}")
        print("4. Start streaming accelerometer/gyroscope data\n")
    
    def start(self):
        """Start receiving data in background thread"""
        self.running = True
        self.thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop receiving data"""
        self.running = False
        if self.thread:
            self.thread.join()
        self.socket.close()
    
    def _receive_loop(self):
        """Background thread that receives UDP packets"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)
                self._parse_data(data)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error receiving data: {e}")
                continue
    
    def _parse_data(self, data: bytes):
        """Parse incoming IMU data (supports multiple formats)"""
        try:
            # Try JSON format first (most common)
            json_data = json.loads(data.decode('utf-8'))
            
            # Support various JSON formats
            if 'roll' in json_data and 'pitch' in json_data:
                roll = float(json_data.get('roll', 0))
                pitch = float(json_data.get('pitch', 0))
                yaw = float(json_data.get('yaw', 0))
            elif 'attitude' in json_data:
                att = json_data['attitude']
                roll = float(att.get('roll', 0))
                pitch = float(att.get('pitch', 0))
                yaw = float(att.get('yaw', 0))
            elif 'rotationRate' in json_data:
                # Some apps send gyro data, integrate to get angles
                # This is a simplified approach
                return  # Skip for now
            else:
                print(f"Unknown JSON format: {json_data.keys()}")
                return
            
            # Apply calibration offsets
            roll -= self.roll_offset
            pitch -= self.pitch_offset
            yaw -= self.yaw_offset
            
            self.latest_data = IMUData(
                roll=roll,
                pitch=pitch,
                yaw=yaw,
                timestamp=time.time()
            )
            
        except json.JSONDecodeError:
            # Try binary format (custom protocol)
            if len(data) == 12:  # 3 floats
                try:
                    roll, pitch, yaw = struct.unpack('fff', data)
                    roll = np.rad2deg(roll)
                    pitch = np.rad2deg(pitch)
                    yaw = np.rad2deg(yaw)
                    
                    self.latest_data = IMUData(
                        roll=roll - self.roll_offset,
                        pitch=pitch - self.pitch_offset,
                        yaw=yaw - self.yaw_offset,
                        timestamp=time.time()
                    )
                except struct.error:
                    pass
    
    def calibrate(self):
        """Set current orientation as zero reference"""
        if self.latest_data:
            self.roll_offset = self.latest_data.roll + self.roll_offset
            self.pitch_offset = self.latest_data.pitch + self.pitch_offset
            self.yaw_offset = self.latest_data.yaw + self.yaw_offset
            print(f"Calibrated: Roll={self.roll_offset:.2f}°, Pitch={self.pitch_offset:.2f}°, Yaw={self.yaw_offset:.2f}°")
        else:
            print("No data received yet, cannot calibrate")
    
    def get_latest(self) -> Optional[IMUData]:
        """Get most recent IMU data"""
        return self.latest_data
    
    def get_tilt_angles(self) -> tuple[float, float]:
        """Get roll and pitch for platform leveling (ignores yaw)"""
        if self.latest_data:
            return self.latest_data.roll, self.latest_data.pitch
        return 0.0, 0.0


# Test/demo mode
if __name__ == "__main__":
    import sys
    
    streamer = IMUStreamer()
    streamer.start()
    
    print("\nPress 'c' to calibrate, 'q' to quit\n")
    
    try:
        while True:
            data = streamer.get_latest()
            if data:
                print(f"\rRoll: {data.roll:6.2f}° | Pitch: {data.pitch:6.2f}° | Yaw: {data.yaw:6.2f}°", end='')
                sys.stdout.flush()
            
            # Simple keyboard input (non-blocking would be better)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        streamer.stop()

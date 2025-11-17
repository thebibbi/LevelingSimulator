"""
iPhone IMU Data Streamer - HTTP Version
Receives IMU data from iPhone via HTTP POST (for Sensor Logger app)

Configure Sensor Logger:
- Push via HTTP enabled
- Target URL: http://YOUR_COMPUTER_IP:8080/imu
- Format: JSON
- Method: POST
"""

import json
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

import numpy as np


@dataclass
class IMUData:
    """Container for IMU orientation data"""

    roll: float  # degrees, rotation about X axis
    pitch: float  # degrees, rotation about Y axis
    yaw: float  # degrees, rotation about Z axis
    timestamp: float

    def to_radians(self):
        """Convert angles to radians"""
        return np.array([np.deg2rad(self.roll), np.deg2rad(self.pitch), np.deg2rad(self.yaw)])


class IMUHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for IMU data"""

    # Class variable to store latest data (shared across requests)
    latest_data: Optional[IMUData] = None
    roll_offset = 0.0
    pitch_offset = 0.0
    yaw_offset = 0.0

    def do_POST(self):
        """Handle POST requests from Sensor Logger"""
        if self.path == "/imu" or self.path == "/":
            try:
                # Read the POST data
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = self.rfile.read(content_length)

                # Parse JSON
                data = json.loads(post_data.decode("utf-8"))

                # Debug: Print first message to see format
                if not hasattr(IMUHTTPHandler, "_first_message_printed"):
                    print("\n" + "=" * 60)
                    print("First message received from Sensor Logger:")
                    print(json.dumps(data, indent=2))
                    print("=" * 60 + "\n")
                    IMUHTTPHandler._first_message_printed = True

                # Extract orientation data
                # Sensor Logger can send different formats, try common ones
                roll, pitch, yaw = self._extract_orientation(data)

                # Apply calibration offsets
                roll -= IMUHTTPHandler.roll_offset
                pitch -= IMUHTTPHandler.pitch_offset
                yaw -= IMUHTTPHandler.yaw_offset

                # Store latest data
                IMUHTTPHandler.latest_data = IMUData(
                    roll=roll, pitch=pitch, yaw=yaw, timestamp=time.time()
                )

                # Send success response
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status": "ok"}')

            except Exception as e:
                print(f"Error parsing data: {e}")
                self.send_response(400)
                self.end_headers()
        else:
            # Wrong path
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        """Handle GET requests (for testing)"""
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            if IMUHTTPHandler.latest_data:
                response = {
                    "status": "receiving",
                    "roll": IMUHTTPHandler.latest_data.roll,
                    "pitch": IMUHTTPHandler.latest_data.pitch,
                    "yaw": IMUHTTPHandler.latest_data.yaw,
                    "age": time.time() - IMUHTTPHandler.latest_data.timestamp,
                }
            else:
                response = {"status": "waiting"}

            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = """
            <html>
            <head><title>IMU Receiver</title></head>
            <body>
            <h1>IMU Data Receiver</h1>
            <p>Listening for iPhone IMU data...</p>
            <p>Send POST requests to: http://THIS_IP:8080/imu</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())

    def _extract_orientation(self, data):
        """Extract roll, pitch, yaw from various JSON formats"""

        # Sensor Logger wraps data in a payload field
        if "payload" in data:
            payload = data["payload"]

            # Payload is a list of sensor readings
            if isinstance(payload, list):
                # Find the orientation sensor
                for item in payload:
                    if isinstance(item, dict) and item.get("name") == "orientation":
                        values = item.get("values", {})
                        # Sensor Logger gives angles in radians, convert to degrees
                        roll = np.rad2deg(float(values.get("roll", 0)))
                        pitch = np.rad2deg(float(values.get("pitch", 0)))
                        yaw = np.rad2deg(float(values.get("yaw", 0)))
                        return roll, pitch, yaw

            # If payload is dict, continue with normal parsing
            data = payload

        # Try direct format: {"roll": x, "pitch": y, "yaw": z}
        if "roll" in data and "pitch" in data:
            roll = float(data.get("roll", 0))
            pitch = float(data.get("pitch", 0))
            yaw = float(data.get("yaw", 0))
            return roll, pitch, yaw

        # Try attitude format: {"attitude": {"roll": x, "pitch": y, "yaw": z}}
        if "attitude" in data:
            att = data["attitude"]
            roll = float(att.get("roll", 0))
            pitch = float(att.get("pitch", 0))
            yaw = float(att.get("yaw", 0))
            return roll, pitch, yaw

        # Try iOS motion format (radians)
        if "motion" in data:
            motion = data["motion"]
            if "attitude" in motion:
                att = motion["attitude"]
                roll = np.rad2deg(float(att.get("roll", 0)))
                pitch = np.rad2deg(float(att.get("pitch", 0)))
                yaw = np.rad2deg(float(att.get("yaw", 0)))
                return roll, pitch, yaw

        # Try quaternion conversion (if available)
        if "quaternion" in data:
            q = data["quaternion"]
            qw = q.get("w", 1)
            qx = q.get("x", 0)
            qy = q.get("y", 0)
            qz = q.get("z", 0)

            # Convert quaternion to Euler angles
            roll, pitch, yaw = self._quaternion_to_euler(qw, qx, qy, qz)
            return roll, pitch, yaw

        # Try accelerometer-based tilt calculation
        if "accelerometer" in data or "accel" in data:
            accel_data = data.get("accelerometer", data.get("accel", {}))

            # Handle both dict and list formats
            if isinstance(accel_data, dict):
                ax = float(accel_data.get("x", 0))
                ay = float(accel_data.get("y", 0))
                az = float(accel_data.get("z", 0))
            elif isinstance(accel_data, list) and len(accel_data) >= 3:
                ax, ay, az = accel_data[0], accel_data[1], accel_data[2]
            else:
                ax = ay = az = 0

            # Calculate roll and pitch from accelerometer
            if az != 0:  # Avoid division by zero
                roll = np.rad2deg(np.arctan2(ay, az))
                pitch = np.rad2deg(np.arctan2(-ax, np.sqrt(ay * ay + az * az)))
                yaw = 0.0  # Can't determine yaw from accelerometer alone

                return roll, pitch, yaw

        # Try Sensor Logger specific format with time-series data
        if isinstance(data, dict):
            # Sometimes data is nested in arrays
            for key in data.keys():
                if isinstance(data[key], list) and len(data[key]) > 0:
                    # Try first element if it's an array
                    first_item = data[key][0] if isinstance(data[key], list) else data[key]
                    if isinstance(first_item, dict) and (
                        "x" in first_item or "accelerometer" in first_item
                    ):
                        return self._extract_orientation(first_item)

        # Default: return zeros and print helpful debug info
        print(f"Warning: Could not extract orientation from data.")
        print(f"Top-level keys: {list(data.keys())}")
        if "payload" in data:
            print(f"Payload type: {type(data['payload'])}")
            if isinstance(data["payload"], dict):
                print(f"Payload keys: {list(data['payload'].keys())}")
            elif isinstance(data["payload"], list) and len(data["payload"]) > 0:
                print(f"Payload is list with {len(data['payload'])} items")
                print(f"First item: {data['payload'][0]}")
        return 0.0, 0.0, 0.0

    def _quaternion_to_euler(self, w, x, y, z):
        """Convert quaternion to Euler angles (roll, pitch, yaw) in degrees"""
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = np.rad2deg(np.arctan2(sinr_cosp, cosr_cosp))

        # Pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = np.rad2deg(np.copysign(np.pi / 2, sinp))
        else:
            pitch = np.rad2deg(np.arcsin(sinp))

        # Yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = np.rad2deg(np.arctan2(siny_cosp, cosy_cosp))

        return roll, pitch, yaw

    def log_message(self, format, *args):
        """Suppress logging of every request"""
        pass  # Comment this out to see all requests


class IMUHTTPStreamer:
    """HTTP server for receiving IMU data from iPhone"""

    def __init__(self, host="0.0.0.0", port=8080):
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False

        # Get computer's IP address
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            computer_ip = s.getsockname()[0]
        except:
            computer_ip = "localhost"
        finally:
            s.close()

        print(f"IMU HTTP Receiver initialized")
        print(f"=" * 60)
        print(f"\nOn your iPhone (Sensor Logger app):")
        print(f"1. Go to Settings → Push")
        print(f"2. Enable 'Push via HTTP'")
        print(f"3. Set Target URL to:")
        print(f"   http://{computer_ip}:{port}/imu")
        print(f"4. Set Format to: JSON")
        print(f"5. Set Method to: POST")
        print(f"6. Start recording (red button)")
        print(f"\n{'='*60}\n")

    def start(self):
        """Start the HTTP server in background thread"""
        self.running = True
        self.server = HTTPServer((self.host, self.port), IMUHTTPHandler)
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()
        print(f"HTTP server listening on {self.host}:{self.port}")
        print("Waiting for data from iPhone...\n")

    def _serve(self):
        """Serve HTTP requests"""
        while self.running:
            self.server.handle_request()

    def stop(self):
        """Stop the HTTP server"""
        self.running = False
        if self.server:
            self.server.shutdown()
        if self.thread:
            self.thread.join()

    def calibrate(self):
        """Set current orientation as zero reference"""
        if IMUHTTPHandler.latest_data:
            IMUHTTPHandler.roll_offset = (
                IMUHTTPHandler.latest_data.roll + IMUHTTPHandler.roll_offset
            )
            IMUHTTPHandler.pitch_offset = (
                IMUHTTPHandler.latest_data.pitch + IMUHTTPHandler.pitch_offset
            )
            IMUHTTPHandler.yaw_offset = IMUHTTPHandler.latest_data.yaw + IMUHTTPHandler.yaw_offset
            print(
                f"Calibrated: Roll={IMUHTTPHandler.roll_offset:.2f}°, "
                f"Pitch={IMUHTTPHandler.pitch_offset:.2f}°, "
                f"Yaw={IMUHTTPHandler.yaw_offset:.2f}°"
            )
        else:
            print("No data received yet, cannot calibrate")

    def get_latest(self) -> Optional[IMUData]:
        """Get most recent IMU data"""
        return IMUHTTPHandler.latest_data

    def get_tilt_angles(self) -> tuple[float, float]:
        """Get roll and pitch for platform leveling (ignores yaw)"""
        if IMUHTTPHandler.latest_data:
            return IMUHTTPHandler.latest_data.roll, IMUHTTPHandler.latest_data.pitch
        return 0.0, 0.0


# Test/demo mode
if __name__ == "__main__":
    import sys

    streamer = IMUHTTPStreamer()
    streamer.start()

    print("Commands:")
    print("  'c' - Calibrate")
    print("  's' - Show status")
    print("  'q' - Quit")
    print()

    try:
        while True:
            data = streamer.get_latest()
            if data:
                print(
                    f"\rRoll: {data.roll:6.2f}° | Pitch: {data.pitch:6.2f}° | "
                    f"Yaw: {data.yaw:6.2f}° | Age: {time.time()-data.timestamp:.1f}s",
                    end="",
                )
                sys.stdout.flush()
            else:
                print(
                    "\rWaiting for data from iPhone...                                        ",
                    end="",
                )
                sys.stdout.flush()

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nShutting down...")
        streamer.stop()

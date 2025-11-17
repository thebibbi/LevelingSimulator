"""
Sensor Logger Data Inspector
Simple HTTP server to see exactly what data format Sensor Logger sends
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class InspectorHandler(BaseHTTPRequestHandler):
    """HTTP handler that prints all received data"""

    message_count = 0

    def do_POST(self):
        """Handle POST requests and print everything"""
        try:
            # Read the POST data
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)

            InspectorHandler.message_count += 1

            # Parse and print JSON
            data = json.loads(post_data.decode("utf-8"))

            print("\n" + "=" * 70)
            print(f"MESSAGE #{InspectorHandler.message_count}")
            print("=" * 70)
            print(json.dumps(data, indent=2))
            print("=" * 70)

            # If there's a payload, show what's inside
            if "payload" in data:
                print("\nPAYLOAD CONTENTS:")
                payload = data["payload"]

                if isinstance(payload, dict):
                    print(f"  Type: Dictionary")
                    print(f"  Keys: {list(payload.keys())}")

                    # Show a sample of each key
                    for key, value in payload.items():
                        if isinstance(value, list):
                            print(f"\n  {key}: (list with {len(value)} items)")
                            if len(value) > 0:
                                print(f"    First item: {value[0]}")
                        elif isinstance(value, dict):
                            print(f"\n  {key}: (dict)")
                            print(f"    Keys: {list(value.keys())}")
                        else:
                            print(f"\n  {key}: {value}")

                elif isinstance(payload, list):
                    print(f"  Type: List with {len(payload)} items")
                    if len(payload) > 0:
                        print(f"  First item: {payload[0]}")
                else:
                    print(f"  Type: {type(payload)}")
                    print(f"  Value: {payload}")

            print("\n" + "=" * 70 + "\n")

            # After 5 messages, give analysis
            if InspectorHandler.message_count == 5:
                print("\n" + "🔍 ANALYSIS AFTER 5 MESSAGES " + "=" * 42)
                print("\nNow that we've seen the format, look above for:")
                print("1. Where is the accelerometer data?")
                print("2. What are the field names? (x, y, z or accelX, accelY, accelZ?)")
                print("3. Is data in 'payload' or somewhere else?")
                print("\nCopy the relevant part and I'll update the code!\n")
                print("=" * 70 + "\n")

            # Send success response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')

        except Exception as e:
            print(f"\nError: {e}\n")
            self.send_response(400)
            self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = f"""
        <html>
        <head><title>Sensor Logger Inspector</title></head>
        <body>
        <h1>Sensor Logger Data Inspector</h1>
        <p>Messages received: {InspectorHandler.message_count}</p>
        <p>Send POST requests to: http://THIS_IP:8080/imu</p>
        <p>Check your terminal to see the data format!</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        """Suppress request logging"""
        pass


def main():
    import socket

    # Get computer's IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        computer_ip = s.getsockname()[0]
    except:
        computer_ip = "localhost"
    finally:
        s.close()

    print("=" * 70)
    print("SENSOR LOGGER DATA INSPECTOR")
    print("=" * 70)
    print(f"\nThis tool will show you EXACTLY what Sensor Logger is sending.")
    print(f"\nSteps:")
    print(f"1. In Sensor Logger, set URL to:")
    print(f"   http://{computer_ip}:8080/imu")
    print(f"2. Start recording")
    print(f"3. Watch this terminal to see the data format")
    print(f"4. After 5 messages, you'll see an analysis")
    print("\n" + "=" * 70 + "\n")

    # Start server
    server = HTTPServer(("0.0.0.0", 8080), InspectorHandler)
    print(f"Inspector listening on port 8080...")
    print(f"Waiting for data from Sensor Logger...\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()

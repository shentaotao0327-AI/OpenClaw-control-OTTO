#!/usr/bin/env python3
"""
Otto9 HTTP-to-Serial Bridge Server

Exposes a simple HTTP API on port 8266 that forwards commands
to the Arduino Nano over USB serial. Designed to be accessed
via SSH reverse tunnel from the OpenClaw cloud agent.

Endpoints:
    GET  /health       — Server + serial status check
    GET  /cmd?q=CMD    — Send a command (URL parameter)
    POST /cmd          — Send a command (JSON body: {"cmd": "..."})

Usage:
    python otto_server.py [--port /dev/ttyUSB0] [--baud 115200] [--http-port 8266]

Repository: https://github.com/YOUR_USERNAME/openclaw-otto9
License: MIT
"""

import json
import sys
import time
import argparse
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

try:
    import serial
except ImportError:
    print("Error: pyserial not installed. Run: pip install pyserial")
    sys.exit(1)

# ---------- Global state ----------
ser = None
ser_lock = threading.Lock()
startup_time = time.time()


def send_command(cmd, timeout=5.0):
    """Send a command to Otto and return parsed response."""
    with ser_lock:
        try:
            ser.reset_input_buffer()
            ser.write((cmd.strip() + '\n').encode('utf-8'))
            ser.flush()
        except serial.SerialException as e:
            return {"status": "error", "error": str(e), "raw": []}

        lines = []
        deadline = time.time() + timeout

        while time.time() < deadline:
            try:
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8', errors='replace').strip()
                    if line:
                        # Skip unexpected READY (caused by reset)
                        if "OTTO9 READY" in line and cmd.strip() != "PING":
                            return {
                                "status": "error",
                                "error": "Arduino reset detected (power issue?)",
                                "raw": [line]
                            }
                        lines.append(line)
                        if line.startswith("OK") or line.startswith("ERR"):
                            break
            except serial.SerialException as e:
                return {"status": "error", "error": str(e), "raw": lines}
            time.sleep(0.02)

    if not lines:
        return {"status": "error", "error": "timeout", "raw": []}

    last = lines[-1]
    if last.startswith("OK"):
        parts = last.split(None, 1)
        value = int(parts[1]) if len(parts) > 1 and parts[1].lstrip('-').isdigit() else None
        return {"status": "ok", "value": value, "raw": lines}
    elif last.startswith("ERR"):
        return {"status": "error", "error": last, "raw": lines}
    else:
        return {"status": "ok", "value": None, "raw": lines}


class OttoHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Otto commands."""

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]}")

    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        # Health check
        if parsed.path == '/health':
            self._send_json({
                "status": "ok",
                "uptime": round(time.time() - startup_time, 1),
                "serial_port": ser.port if ser else None,
                "serial_open": ser.is_open if ser else False,
            })
            return

        # Command via GET parameter
        if parsed.path == '/cmd':
            params = parse_qs(parsed.query)
            cmd = params.get('q', [None])[0]
            if not cmd:
                self._send_json({"status": "error", "error": "missing ?q= parameter"}, 400)
                return
            result = send_command(cmd)
            code = 200 if result['status'] == 'ok' else 502
            self._send_json(result, code)
            return

        self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == '/cmd':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                cmd = data.get('cmd', '')
            except (json.JSONDecodeError, AttributeError):
                self._send_json({"status": "error", "error": "invalid JSON"}, 400)
                return

            if not cmd:
                self._send_json({"status": "error", "error": "missing 'cmd' field"}, 400)
                return

            result = send_command(cmd)
            code = 200 if result['status'] == 'ok' else 502
            self._send_json(result, code)
            return

        self._send_json({"error": "not found"}, 404)


def main():
    global ser

    parser = argparse.ArgumentParser(description="Otto9 HTTP-to-Serial Bridge")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Serial port (default: /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--http-port", type=int, default=8266, help="HTTP port (default: 8266)")
    args = parser.parse_args()

    # Open serial connection
    print(f"Opening serial port {args.port} at {args.baud} baud...")
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except serial.SerialException as e:
        print(f"Error: {e}")
        print(f"\nTips:")
        print(f"  - Is the Arduino plugged in? Check: ls /dev/ttyUSB*")
        print(f"  - Permission denied? Run: sudo usermod -a -G dialout $USER")
        sys.exit(1)

    # Wait for Arduino reset
    time.sleep(2)

    # Drain startup messages
    while ser.in_waiting:
        line = ser.readline().decode('utf-8', errors='replace').strip()
        print(f"  [startup] {line}")

    # Start HTTP server
    server = HTTPServer(('127.0.0.1', args.http_port), OttoHandler)
    print(f"\n✓ Otto HTTP bridge running on http://127.0.0.1:{args.http_port}")
    print(f"  GET  /health       — Status check")
    print(f"  GET  /cmd?q=PING   — Send command")
    print(f"  POST /cmd          — Send command (JSON)")
    print(f"\nPress Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()
        ser.close()


if __name__ == "__main__":
    main()

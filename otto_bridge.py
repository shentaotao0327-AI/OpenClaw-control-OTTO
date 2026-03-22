#!/usr/bin/env python3
"""
Otto9 Serial Bridge — Interactive CLI for testing.

Connects to the Arduino Nano over USB serial and provides an
interactive prompt to send text commands and see responses.

Usage:
    python otto_bridge.py [--port /dev/ttyUSB0] [--baud 115200]

Commands:
    Type any Otto command (PING, HOME, WALK 3, DIST, BEEP, etc.)
    Type 'quit' or 'exit' to disconnect.

Repository: https://github.com/YOUR_USERNAME/openclaw-otto9
License: MIT
"""

import sys
import time
import argparse

try:
    import serial
except ImportError:
    print("Error: pyserial not installed. Run: pip install pyserial")
    sys.exit(1)


def wait_for_ready(ser, timeout=5.0):
    """Wait for the 'OTTO9 READY' banner after reset."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='replace').strip()
            print(f"  <- {line}")
            if "OTTO9 READY" in line:
                return True
        time.sleep(0.05)
    return False


def send_command(ser, cmd, timeout=5.0):
    """Send a command and collect response lines."""
    ser.reset_input_buffer()
    ser.write((cmd.strip() + '\n').encode('utf-8'))
    ser.flush()

    lines = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line:
                lines.append(line)
                # If we got an OK or ERR, we're done
                if line.startswith("OK") or line.startswith("ERR"):
                    break
        time.sleep(0.05)
    return lines


def main():
    parser = argparse.ArgumentParser(description="Otto9 Serial Bridge")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Serial port (default: /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    args = parser.parse_args()

    print(f"Connecting to {args.port} at {args.baud} baud...")

    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except serial.SerialException as e:
        print(f"Error: {e}")
        print("\nTips:")
        print(f"  - Is the Arduino plugged in? Check: ls /dev/ttyUSB*")
        print(f"  - Permission denied? Run: sudo usermod -a -G dialout $USER")
        sys.exit(1)

    # Wait for Arduino to reset after serial open
    time.sleep(2)
    print("Waiting for OTTO9 READY...")
    if wait_for_ready(ser):
        print("✓ Otto is ready!\n")
    else:
        print("⚠ No READY received (may already be running). Continuing anyway.\n")

    print("Otto Bridge — type commands (PING, HOME, WALK 3, DIST, BEEP, ...)")
    print("Type 'quit' or 'exit' to disconnect.\n")

    while True:
        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not cmd:
            continue
        if cmd.lower() in ('quit', 'exit'):
            print("Bye!")
            break

        responses = send_command(ser, cmd)
        for line in responses:
            print(f"  <- {line}")
        if not responses:
            print("  (no response — timeout)")

    ser.close()


if __name__ == "__main__":
    main()

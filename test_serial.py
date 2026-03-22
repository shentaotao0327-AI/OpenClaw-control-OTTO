#!/usr/bin/env python3
"""Quick serial tester for Otto firmware."""
import serial
import time
import sys

PORT = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyUSB0'
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=2)
time.sleep(2)  # wait for Arduino reset

# Drain startup message
while ser.in_waiting:
    print(f"<< {ser.readline().decode('utf-8', errors='replace').strip()}")

commands = ["PING", "HOME", "WALK 1", "TURN 1 LEFT", "BEND 1 LEFT", "DIST", "BEEP"]

for cmd in commands:
    print(f"\n>> {cmd}")
    ser.write((cmd + '\n').encode())
    time.sleep(5 if cmd.startswith(("WALK", "TURN", "BEND", "MOON")) else 2)
    while ser.in_waiting:
        line = ser.readline().decode('utf-8', errors='replace').strip()
        print(f"<< {line}")

ser.close()
print("\nDone!")

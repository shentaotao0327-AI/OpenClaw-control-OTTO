#!/usr/bin/env python3
"""
Otto Robot Serial Bridge - Master Controller

Sends commands to Arduino Nano slave via USB serial.
Supports simulator mode (--sim) for testing without hardware.

Usage:
  python3 otto_bridge.py [--sim] [--port /dev/ttyACM0] <command> [args...]
  python3 otto_bridge.py [--sim] choreo <file.json>

Commands:
  ping                           Health check
  walk <steps> <forward|backward> Walk
  turn <steps> <left|right>      Turn
  dance                          Moonwalk dance
  jump                           Jump
  home                           Reset position
  stop                           Emergency stop
  speed <ms>                     Set speed (100-5000, lower=faster)
  swing <steps>                  Swing movement
  updown <steps>                 Up-down movement
  tiptoe <steps>                 Tiptoe walk
  bend <steps> <left|right>      Bend
  shake <steps> <left|right>     Shake leg
  crusaito <steps>               Crusaito dance
  flapping <steps>               Flapping dance
  jitter <steps>                 Jitter dance
  ascend <steps>                 Ascending turn
  sing <id>                      Play sound (0-19)
  dist                           Read ultrasonic distance
  status                         Get robot state
  seq "<cmd1;cmd2;...>"          Run inline sequence
  choreo <file.json>             Run choreography file
  raw "<CMD>"                    Send raw serial command

Simulator mode (--sim):
  No hardware needed. Prints what would happen.
"""

import sys
import time
import json
import os

# ─── Configuration ───────────────────────────────────────────────

DEFAULT_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600
TIMEOUT = 15
CONNECT_DELAY = 2

# ─── Simulator ───────────────────────────────────────────────────

class SimulatorSerial:
    """Fake serial that simulates Otto responses."""
    
    def __init__(self):
        self.speed = 1000
        self.in_waiting = 0
        self._response_queue = []
        print("[SIM] 🤖 Simulator mode — no hardware needed")
        print("[SIM] READY:Otto slave online (simulated)")
    
    def write(self, data):
        cmd = data.decode('utf-8').strip()
        response = self._simulate(cmd)
        self._response_queue.append(response.encode('utf-8') + b'\n')
        self.in_waiting = 1
    
    def readline(self):
        self.in_waiting = 0
        if self._response_queue:
            return self._response_queue.pop(0)
        return b''
    
    def flush(self):
        pass
    
    def close(self):
        print("[SIM] Connection closed")
    
    def _simulate(self, cmd):
        # Simulate movement duration
        move_cmds = ['WALK', 'TURN', 'BEND', 'SHAKE', 'SWING', 'UPDOWN', 
                      'TIPTOE', 'CRUSAITO', 'FLAPPING', 'JITTER', 'ASCEND']
        
        if cmd == 'PING':
            return 'PONG'
        elif cmd == 'STATUS':
            return f'STATUS:speed={self.speed},moving=no,ultrasonic=no'
        elif cmd == 'STOP':
            print(f"[SIM] ⏹️  Stopping and going home")
            return 'OK:STOP'
        elif cmd == 'HOME':
            print(f"[SIM] 🏠 Reset to home position")
            return 'OK:HOME'
        elif cmd == 'JUMP':
            print(f"[SIM] 🦘 Jumping!")
            time.sleep(0.3)
            return 'OK:JUMP'
        elif cmd == 'DANCE':
            print(f"[SIM] 💃 Moonwalk dancing!")
            time.sleep(0.5)
            return 'OK:DANCE'
        elif cmd.startswith('SPEED:'):
            self.speed = int(cmd.split(':')[1])
            print(f"[SIM] ⚡ Speed set to {self.speed}ms")
            return f'OK:SPEED:{self.speed}'
        elif cmd.startswith('SING:'):
            sid = cmd.split(':')[1]
            sounds = {
                '0': '🎵 Connection sound', '1': '🎵 Disconnection', 
                '2': '🎵 Button pushed', '3': '🎵 Mode 1', 
                '4': '🎵 Mode 2', '5': '🎵 Mode 3',
                '6': '🎵 Surprise', '7': '🎵 Oh-ooh', 
                '8': '🎵 Oh-ooh 2', '9': '🎵 Cuddly',
                '10': '🎵 Sleeping', '11': '🎵 Happy',
                '12': '🎵 Super happy', '13': '🎵 Happy short',
                '14': '🎵 Sad', '15': '🎵 Confused',
                '16': '🎵 Fart 1', '17': '🎵 Fart 2',
                '18': '🎵 Fart 3', '19': '🎵 Magic'
            }
            desc = sounds.get(sid, '🎵 Unknown sound')
            print(f"[SIM] {desc}")
            return f'OK:SING:{sid}'
        elif cmd.startswith('DELAY:'):
            ms = int(cmd.split(':')[1])
            print(f"[SIM] ⏳ Waiting {ms}ms...")
            time.sleep(ms / 1000.0)
            return f'OK:DELAY:{ms}'
        elif cmd == 'DIST':
            import random
            dist = random.randint(5, 200)
            print(f"[SIM] 📏 Ultrasonic distance: {dist}cm")
            return f'OK:DIST:{dist}'
        
        # Movement commands
        for mc in move_cmds:
            if cmd.startswith(mc + ':') or cmd == mc:
                parts = cmd.split(':')
                steps = parts[1] if len(parts) > 1 else '4'
                direction = parts[2] if len(parts) > 2 else ''
                
                dir_emoji = {'1': '➡️', '-1': '⬅️'}.get(direction, '🔄')
                move_emoji = {
                    'WALK': '🚶', 'TURN': '🔄', 'BEND': '🙇',
                    'SHAKE': '🦵', 'SWING': '🎵', 'UPDOWN': '⬆️⬇️',
                    'TIPTOE': '🩰', 'CRUSAITO': '🕺', 'FLAPPING': '🦅',
                    'JITTER': '😬', 'ASCEND': '🌀'
                }.get(mc, '🤖')
                
                dir_word = {'1': 'forward/left', '-1': 'backward/right'}.get(direction, '')
                print(f"[SIM] {move_emoji} {mc} {steps} steps {dir_word} {dir_emoji}")
                time.sleep(0.2)
                return f'OK:{cmd}'
        
        # Sequence
        if cmd.startswith('SEQ:'):
            print(f"[SIM] 📋 Running sequence...")
            seq_cmds = cmd[4:].split(';')
            results = []
            for sc in seq_cmds:
                sc = sc.strip()
                if sc:
                    r = self._simulate(sc)
                    results.append(r)
            return f'OK:SEQ:done:{len(results)}'
        
        return f'ERR:Unknown command: {cmd}'

# ─── Real Serial ─────────────────────────────────────────────────

def connect_real(port, baud=BAUD_RATE):
    """Open real serial connection to Arduino."""
    import serial
    try:
        ser = serial.Serial(port, baud, timeout=TIMEOUT)
        # Wait for READY message from Arduino after reset
        deadline = time.time() + 5  # up to 5 seconds for boot
        while time.time() < deadline:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line:
                    print(f"[Arduino] {line}")
                    if line.startswith("READY"):
                        break
            else:
                time.sleep(0.1)
        return ser
    except Exception as e:
        print(f"ERROR: Cannot open {port}: {e}")
        print("Is the Arduino Nano plugged in? Try --sim for simulator mode.")
        sys.exit(1)

# ─── Command Helpers ─────────────────────────────────────────────

def send_command(ser, cmd, timeout=15):
    """Send a command and return the response."""
    cmd = cmd.strip()
    # Drain any stale data in the buffer before sending
    try:
        while ser.in_waiting:
            ser.readline()
    except OSError:
        pass
    ser.write((cmd + '\n').encode('utf-8'))
    ser.flush()
    
    response = ""
    start = time.time()
    while time.time() - start < timeout:
        try:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line and not line.startswith("READY"):
                    response = line
                    break
        except OSError:
            # USB-serial chip busy while servos move — wait and retry
            time.sleep(0.5)
            continue
        time.sleep(0.1)
    
    return response if response else "TIMEOUT: No response from Arduino"

def dir_to_int(direction_str):
    """Convert direction words to integer values."""
    d = direction_str.lower()
    if d in ("forward", "fwd", "f", "left", "l", "1"):
        return 1
    elif d in ("backward", "back", "bwd", "b", "right", "r", "-1"):
        return -1
    print(f"WARNING: Unknown direction '{direction_str}', defaulting to 1")
    return 1

def load_choreography(filepath):
    """Load a choreography JSON file and return a list of commands."""
    with open(filepath, 'r') as f:
        choreo = json.load(f)
    
    print(f"🎭 Choreography: {choreo.get('name', 'Untitled')}")
    if 'description' in choreo:
        print(f"   {choreo['description']}")
    
    commands = []
    for step in choreo.get('steps', []):
        cmd = step.get('command', '')
        repeat = step.get('repeat', 1)
        for _ in range(repeat):
            commands.append(cmd)
            if 'delay_after' in step:
                commands.append(f"DELAY:{step['delay_after']}")
    
    return commands

# ─── Main ────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    
    # Parse flags
    sim_mode = False
    port = DEFAULT_PORT
    
    while args and args[0].startswith('--'):
        flag = args.pop(0)
        if flag == '--sim':
            sim_mode = True
        elif flag == '--port' and args:
            port = args.pop(0)
    
    if not args:
        print(__doc__)
        sys.exit(0)
    
    action = args[0].lower()
    params = args[1:]
    
    # Build command string
    if action == "ping":
        cmd = "PING"
    elif action == "status":
        cmd = "STATUS"
    elif action == "stop":
        cmd = "STOP"
    elif action == "home":
        cmd = "HOME"
    elif action == "jump":
        cmd = "JUMP"
    elif action == "dance":
        cmd = "DANCE"
    elif action == "dist":
        cmd = "DIST"
    elif action == "speed":
        cmd = f"SPEED:{params[0] if params else '1000'}"
    elif action == "sing":
        cmd = f"SING:{params[0] if params else '0'}"
    elif action == "walk":
        steps = params[0] if params else "4"
        direction = dir_to_int(params[1]) if len(params) > 1 else 1
        cmd = f"WALK:{steps}:{direction}"
    elif action == "turn":
        steps = params[0] if params else "4"
        direction = dir_to_int(params[1]) if len(params) > 1 else 1
        cmd = f"TURN:{steps}:{direction}"
    elif action == "bend":
        steps = params[0] if params else "1"
        direction = dir_to_int(params[1]) if len(params) > 1 else 1
        cmd = f"BEND:{steps}:{direction}"
    elif action == "shake":
        steps = params[0] if params else "1"
        direction = dir_to_int(params[1]) if len(params) > 1 else 1
        cmd = f"SHAKE:{steps}:{direction}"
    elif action in ("swing", "updown", "tiptoe", "crusaito", "flapping", "jitter", "ascend"):
        steps = params[0] if params else "4"
        cmd = f"{action.upper()}:{steps}"
    elif action == "seq":
        cmd = f"SEQ:{params[0]}" if params else ""
        if not cmd:
            print("ERROR: seq requires a command string")
            sys.exit(1)
    elif action == "choreo":
        if not params:
            print("ERROR: choreo requires a JSON file path")
            sys.exit(1)
        # Choreography mode — sends multiple commands
        commands = load_choreography(params[0])
        ser = SimulatorSerial() if sim_mode else connect_real(port)
        results = []
        for c in commands:
            print(f"[Sending] {c}")
            resp = send_command(ser, c)
            print(f"[Response] {resp}")
            results.append({"command": c, "response": resp})
        ser.close()
        print(f"\n✅ Choreography complete — {len(results)} steps executed")
        return 0
    elif action == "raw":
        cmd = params[0] if params else ""
        if not cmd:
            print("ERROR: raw requires a command string")
            sys.exit(1)
    else:
        print(f"ERROR: Unknown action '{action}'")
        print("Run with no args to see usage.")
        sys.exit(1)
    
    # Connect and send
    ser = SimulatorSerial() if sim_mode else connect_real(port)
    print(f"[Sending] {cmd}")
    response = send_command(ser, cmd)
    print(f"[Response] {response}")
    
    result = {
        "command": cmd,
        "response": response,
        "success": response.startswith("OK:") or response == "PONG" or response.startswith("STATUS:")
    }
    print(f"[Result] {json.dumps(result)}")
    
    ser.close()
    return 0 if result["success"] else 1

if __name__ == "__main__":
    sys.exit(main())

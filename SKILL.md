# Otto Robot Control

Control an Otto DIY robot (4-servo, 2-leg) via Arduino Nano slave connected over USB serial.

**Activate when:** user mentions Otto robot, robot control, walking robot, make the robot move/dance, choreography, or robot commands.

## Overview

This skill controls a physical Otto robot through a master-slave architecture:
- **Master:** This Linux machine running OpenClaw
- **Slave:** Arduino Nano inside the Otto robot, connected via USB serial
- **Protocol:** Text commands over serial at 9600 baud, newline-terminated

## Quick Reference

### Single Commands

Run via the bridge script:

```bash
python3 {SKILL_DIR}/scripts/otto_bridge.py <command> [args...]
```

| Command | Example | Description |
|---------|---------|-------------|
| `ping` | `ping` | Health check (returns PONG) |
| `walk` | `walk 4 forward` | Walk steps (forward/backward) |
| `turn` | `turn 3 left` | Turn steps (left/right) |
| `dance` | `dance` | Moonwalk dance |
| `jump` | `jump` | Jump |
| `home` | `home` | Reset to home position |
| `stop` | `stop` | Emergency stop |
| `speed` | `speed 800` | Set speed in ms (100-5000, lower=faster) |
| `swing` | `swing 4` | Swing movement |
| `updown` | `updown 4` | Up-down movement |
| `tiptoe` | `tiptoe 4` | Tiptoe walk |
| `bend` | `bend 1 left` | Bend (left/right) |
| `shake` | `shake 1 left` | Shake leg (left/right) |
| `crusaito` | `crusaito 4` | Crusaito dance |
| `flapping` | `flapping 4` | Flapping dance |
| `jitter` | `jitter 4` | Jitter dance |
| `ascend` | `ascend 4` | Ascending turn |
| `sing` | `sing 12` | Play sound (0-19) |
| `dist` | `dist` | Read ultrasonic distance |
| `status` | `status` | Get robot state |

### Sound IDs (for `sing`)

0=connection, 1=disconnection, 2=button, 6=surprise, 7=oh-ooh, 9=cuddly, 10=sleeping, 11=happy, 12=super_happy, 14=sad, 15=confused, 16-18=fart1-3, 19=magic

### Choreography

Run a pre-built choreography file:

```bash
python3 {SKILL_DIR}/scripts/otto_bridge.py choreo {SKILL_DIR}/choreography/<name>.json
```

Available choreographies:
- `greeting.json` — Hello dance with bows and sounds
- `party.json` — Full dance party (moonwalk, jitter, flapping, etc.)
- `patrol.json` — Walk a square patrol route

### Simulator Mode

Test without hardware — add `--sim` flag:

```bash
python3 {SKILL_DIR}/scripts/otto_bridge.py --sim dance
python3 {SKILL_DIR}/scripts/otto_bridge.py --sim choreo {SKILL_DIR}/choreography/party.json
```

### Custom Port

Override the default serial port (`/dev/ttyACM0`):

```bash
python3 {SKILL_DIR}/scripts/otto_bridge.py --port /dev/ttyUSB0 walk 4 forward
```

## Natural Language Mapping

When the user says something casual, map it to commands:

| User says | Command(s) |
|-----------|------------|
| "walk forward" / "go ahead" | `walk 4 forward` |
| "go back" / "walk backward" | `walk 4 backward` |
| "turn left" | `turn 3 left` |
| "turn right" | `turn 3 right` |
| "dance" / "party" | `dance` or `choreo party.json` |
| "say hello" / "greet" | `choreo greeting.json` |
| "patrol" / "walk around" | `choreo patrol.json` |
| "stop" / "freeze" | `stop` |
| "faster" | `speed 600` |
| "slower" | `speed 1500` |
| "normal speed" | `speed 1000` |
| "be happy" | `sing 12` |
| "be sad" | `sing 14` |

## Creating Choreographies

Choreography files are JSON with this structure:

```json
{
  "name": "My Dance",
  "description": "What this routine does",
  "steps": [
    { "command": "WALK:4:1", "delay_after": 300 },
    { "command": "DANCE", "delay_after": 500, "repeat": 2 },
    { "command": "SING:12" },
    { "command": "HOME" }
  ]
}
```

- `command`: Raw serial command string
- `delay_after`: Milliseconds to wait after this step (optional)
- `repeat`: Number of times to repeat this step (optional, default 1)

Save new choreographies to `{SKILL_DIR}/choreography/`.

## Setup (First Time)

### Flash the Arduino Nano

```bash
export PATH="$HOME/bin:$PATH"
arduino-cli compile --fqbn arduino:avr:nano {SKILL_DIR}/firmware/otto_slave
arduino-cli upload --fqbn arduino:avr:nano --port /dev/ttyACM0 {SKILL_DIR}/firmware/otto_slave
```

If upload fails, try old bootloader: `--fqbn arduino:avr:nano:cpu=atmega328old`

### Pin Layout

| Pin | Function |
|-----|----------|
| 2 | Left Leg |
| 3 | Right Leg |
| 4 | Left Foot |
| 5 | Right Foot |
| 13 | Buzzer |
| 8 | Ultrasonic Trigger (optional) |
| 9 | Ultrasonic Echo (optional) |

### Dependencies

- `arduino-cli` with `arduino:avr` core and `OttoDIYLib` library
- Python 3 with `pyserial` (`pip install pyserial`)

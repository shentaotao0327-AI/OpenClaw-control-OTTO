# Otto9 Robot Control Skill

Control an Otto9 biped robot via natural language commands.

## Activation

Activate when the user mentions: Otto, robot, 机器人, walk, dance, 走路, 跳舞, or any robot motion command.

## How It Works

Send HTTP requests to the Otto bridge server at `http://localhost:8266`.

### Endpoints

- `GET /health` — Check if Otto is connected
- `GET /cmd?q=COMMAND` — Send a command
- `POST /cmd` with JSON `{"cmd": "COMMAND"}` — Send a command

### Available Commands

| Command | What it does | Needs battery? |
|---------|-------------|----------------|
| `PING` | Test connection | No |
| `HOME` | Reset to standing position | No |
| `WALK [steps]` | Walk forward | **Yes** |
| `WALKBACK [steps]` | Walk backward | **Yes** |
| `TURNLEFT [steps]` | Turn left | **Yes** |
| `TURNRIGHT [steps]` | Turn right | **Yes** |
| `BEND steps LEFT\|RIGHT` | Bend one leg | Low power OK |
| `MOONWALK [steps]` | Moonwalk dance | **Yes** |
| `SWING [steps]` | Swing dance | **Yes** |
| `FLAPPING [steps]` | Flapping motion | **Yes** |
| `JITTER [steps]` | Jitter motion | **Yes** |
| `CRUSAITO [steps]` | Crusaito dance | **Yes** |
| `TIPTOE [steps]` | Tiptoe walk | **Yes** |
| `JUMP` | Jump | **Yes** |
| `GESTURE id` | Gesture: 0=happy, 1=superhappy, 2=sad | **Yes** |
| `DIST` | Read ultrasonic distance (cm) | No |
| `BEEP` | Play a tone | No |

### Response Format

```json
{"status": "ok", "value": null, "raw": ["OK"]}
{"status": "ok", "value": 42, "raw": ["OK 42"]}
{"status": "error", "error": "Arduino reset detected", "raw": ["OTTO9 READY"]}
```

## Natural Language Mapping

Translate user intent to commands:

- "让Otto走/往前走" → `WALK`
- "后退/往后走" → `WALKBACK`
- "左转/往左转" → `TURNLEFT`
- "右转/往右转" → `TURNRIGHT`
- "弯腿/弯一下" → `BEND`
- "跳舞/月球步" → `MOONWALK`
- "摇摆" → `SWING`
- "测距离/前面有什么" → `DIST`
- "叫一声/响一下" → `BEEP`
- "开心/高兴" → `GESTURE 0`
- "站好/回位" → `HOME`
- "连接测试" → `PING`

## Power Warning

If a movement command returns `"error": "Arduino reset detected"`, tell the user:
- USB power is insufficient for multi-servo movements
- They need 4×AA batteries (6V) connected to servo power
- Low-power commands still work: PING, HOME, BEND, DIST, BEEP

## Example Tool Usage

```bash
# Check connection
curl http://localhost:8266/cmd?q=PING

# Make Otto beep
curl http://localhost:8266/cmd?q=BEEP

# Walk 3 steps
curl http://localhost:8266/cmd?q=WALK%203

# Read distance
curl http://localhost:8266/cmd?q=DIST
```

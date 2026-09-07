# CamJam Robot Zero

Raspberry Pi Zero W robot (CamJam EduKit 3 chassis) controlled over HTTP from a browser joystick. Python stdlib only — no build step, no package.json/requirements.txt.

## Files

- `motorcontrol.py` — the server. Everything of substance lives here:
  - `RobotControlHandler(BaseHTTPRequestHandler)` — class-level (shared, not per-request) instances of `robot`, `buzzer`, `reverse_beeper`, `distance_monitor`, guarded by `control_lock`.
  - `DistanceMonitor` — background thread polling the ultrasonic sensor every 60ms.
  - `ReverseBeeper` — background thread pulsing the buzzer while reversing.
  - `do_GET` serves static files relative to CWD (no path traversal guard — acceptable since this only runs on a closed LAN).
  - `do_POST` handles `/control` (JSON `{left, right}` in ±1023) and `/shutdown` (stops everything, then `sudo shutdown -h now`).
- `joy.html` — browser joystick UI, served at `/`. Vanilla JS, no dependencies.
- `motorcontrol.service` — systemd unit; runs as user `pi`, logs to RAM (`/run/motorcontrol.log`) to reduce SD card wear, `Restart=always`.
- `motortest.py`, `buzzertest.py` — standalone manual hardware smoke tests, not used by the server.

## Key behavior to preserve

- **Safety interlock**: `DISTANCE_THRESHOLD = 15` (cm) in `motorcontrol.py`. `control_motors` clamps forward motion to 0 below this distance; reverse/turning stays allowed. The distance monitor's notifier calls `trigger_control` to re-apply the *last* command whenever a new close-range reading arrives, so the robot brakes even without a fresh joystick input — don't remove this re-trigger path when touching `DistanceMonitor` or `control_motors`.
- **Status LEDs / crazy state**: `StatusLeds` (blue=GPIO27, red=GPIO22) mirrors moving/stationary via `control_motors`'s final (post-safety-clamp) motor values — exactly one LED lit at all times. `RobotControlHandler.crazy` is the single source of truth for crazy state: `POST /crazy` sets it, stops the motors, and starts `StatusLeds` flashing; `trigger_control` no-ops while it's set (so a close-range distance reading can't silently re-engage the motors mid-crazy-state); `POST /control` unconditionally clears it and stops the flashing, since any real control input (joystick move or STOP) is what ends crazy state.
- **Client-side throttling** in `joy.html`: `queueCommand` always records the latest stick position, but `processCommand` (via `requestAnimationFrame`) only POSTs to `/control` at most every `THROTTLE_MS` (200ms), and guarantees one final send after `IDLE_TIMEOUT_MS` so the last position (e.g. centered/stop) always lands. This is intentional — it avoids flooding the Pi's single-threaded-feeling HTTP server with a request per pointer-move event while staying responsive. Keep "send latest, drop intermediate" semantics if you touch this.
- Motor values are ±1023 over the wire, normalized to ±1 before being passed to `CamJamKitRobot.value`.
- `RobotControlHandler`'s hardware objects (`robot`, `buzzer`, sensors) are class attributes, constructed once at import time — this is deliberate singleton sharing across the threaded HTTP server, not an oversight.

## Running / testing

No test suite. Verification is manual, on real hardware (Pi Zero W + CamJam kit wiring):

```
python3 motorcontrol.py          # start the server, browse to http://<pi>:8000/
python3 motortest.py             # forward/stop/backward smoke test
python3 buzzertest.py            # buzzer on/off loop
```

There's no way to exercise gpiozero/hardware paths off-Pi in this repo — don't invent a mock/simulation layer unless asked.

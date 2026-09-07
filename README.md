# CamJam Robot Zero

A little project based on a Raspberry Pi Zero W and the excellent [CamJam Robotics kit](https://camjam.me/?page_id=1035).

A Python HTTP server ([`motorcontrol.py`](motorcontrol.py)) drives the robot via [gpiozero](https://gpiozero.readthedocs.io/en/stable/index.html) and serves an on-page joystick UI ([`joy.html`](joy.html)) for control from a phone/tablet/desktop browser on the same network.

## Features
1. HTML joystick control from any browser on the local network.
2. Client-side throttling keeps at most one command in flight to the webserver, for a responsive feel without flooding requests.
3. Beeps while reversing.
4. Front-facing distance sensor blocks forward motion when an obstacle is closer than 15cm.
5. Shutdown button on the UI cleanly stops the robot and powers down the Pi, to reduce the risk of filesystem corruption from a hard power-off.
6. Status LEDs: blue (GPIO 27) lit while moving, red (GPIO 22) lit while stationary — exactly one is lit at all times.
7. "CRAZY!" button on the UI stops the motors immediately and alternates both LEDs every 200ms, until the next joystick move or STOP.

## Running

```
python3 motorcontrol.py
```

Serves on port 8000; browse to `http://<pi-address>:8000/`. See [`motorcontrol.service`](motorcontrol.service) for running it as a systemd service on boot.

## Todo
1. Line following mode

## Notes

1. Uses the standard wiring expected by the [CamJam Robot kit](https://gpiozero.readthedocs.io/en/stable/api_boards.html#camjamkitrobot) classes in [gpiozero](https://gpiozero.readthedocs.io/en/stable/index.html).
2. [Wiring diagrams and more for the CamJam kit](https://github.com/CamJam-EduKit/EduKit3/tree/master/CamJam%20Edukit%203%20-%20GPIO%20Zero).

## GPIO Pinout

The CamJam motor controller board sits on top of the Pi Zero's 40-pin header but only passes through the first 13 rows (physical pins 1-26) — pins 27-40 are covered and inaccessible. All wiring below uses only pins within that passed-through range.

| BCM GPIO | Physical pin | Used for | Resistor |
|---|---|---|---|
| 4 | 7 | Buzzer | - |
| 7 | 26 | Right motor | - |
| 8 | 24 | Right motor | - |
| 9 | 21 | Left motor | - |
| 10 | 19 | Left motor | - |
| 17 | 11 | Distance sensor (trigger) | - |
| 18 | 12 | Distance sensor (echo) | - |
| 22 | 15 | Red LED (stationary indicator) | 220Ω (red-red-brown-gold) |
| 27 | 13 | Blue LED (moving indicator) | 100Ω (brown-black-brown-gold) |

Free pins remaining in the passed-through range: GPIO 2, 3 (I2C — avoid unless needed), 14, 15 (UART — avoid, serial console), 23, 24, 25, 11.


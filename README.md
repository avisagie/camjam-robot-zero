# CamJam Robot Zero

A little project based on a Raspberry Pi Zero W and the excellent [CamJam Robotics kit](https://camjam.me/?page_id=1035).

## Features
1. An HTML based joystick that controls the robot from a browser on a phone/tablet/desktop.
2. The joystick throttles commands to maintain a short request queue in the browser to the [flask](url) based app. For responsiveness.
3. Beep when it reverses.
4. Distance sensor in front prevents forward motion when it senses a wall closer than 10cm.

## Todo
1. Shutdown to cleanly shutdown the pi zero.
2. Line following mode

## Notes

1. Uses the standard wiring expected by the [CamJam Robot kit](https://gpiozero.readthedocs.io/en/stable/api_boards.html#camjamkitrobot) classes in [gpiozero](https://gpiozero.readthedocs.io/en/stable/index.html)
2. [Wiring diagrams and more for the CamJam kit](https://github.com/CamJam-EduKit/EduKit3/tree/master/CamJam%20Edukit%203%20-%20GPIO%20Zero)


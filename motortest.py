import time
from gpiozero import CamJamKitRobot

def test(robot):
    print('forward')
    robot.forward()
    time.sleep(1.0)
    
    print('stop')
    robot.stop()
    time.sleep(1.0)
    
    print('backward')
    robot.backward()
    time.sleep(1.0)
    
    print('stop')
    robot.stop()
    
    
if __name__ == "__main__":
    robot = CamJamKitRobot()
    try:
        test(robot)
    finally:
        robot.stop()
        

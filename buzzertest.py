from gpiozero import Buzzer
import time


buzzer = Buzzer(4)

while True:
    buzzer.on()
    time.sleep(2.0)
    buzzer.off()
    time.sleep(2.0)

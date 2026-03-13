import serial
import time
from sys import version_info


# Initializing Controller with the correct port for Pi
class Controller:
    def __init__(self, ttyStr='/dev/ttyACM0', device=0x0c):
        self.usb = serial.Serial(ttyStr)
        self.PololuCmd = chr(0xaa) + chr(device)

    
    def head_yes(self):
        # Tilt head down then up then center
        self.setTarget(3, 7000) 
        time.sleep(0.5)
        self.setTarget(3, 5000) 
        time.sleep(0.5)
        self.setTarget(3, 6000)  
        time.sleep(0.5)
    

    def head_no(self):
        self.setTarget(4, 7000)
        time.sleep(0.5)
        self.setTarget(4, 5000)
        time.sleep(0.5)
        self.setTarget(4, 6000)



    def arm_raise(self):
        self.setTarget(5, 8000)
        self.setTarget(7, 3600)
        time.sleep(1.5)
        self.setTarget(5, 5200)
        self.setTarget(7, 6000)
        
    def dance90(self):
        self.setTarget(1, 7500)
        time.sleep(1.0)
        self.setTarget(1, 4500)
        time.sleep(1.0)
        self.setTarget(1, 6000)
        
    


    def drive(self, x, y):
        throttle = y
        steering = x

        # left = max(4000, min(9000, left))
        # right = max(4000, min(9000, right))

        # print(f"DEBUG: Sending to Wheels -> Left (Ch1): {left}, Right (Ch2): {right}")

        self.setTarget(0, int(throttle))
        self.setTarget(1, int(steering))

    def sendCmd(self, cmd):
        cmdStr = self.PololuCmd + cmd
        self.usb.write(bytes(cmdStr, 'latin-1'))

    def setTarget(self, chan, target):
        lsb = target & 0x7f
        msb = (target >> 7) & 0x7f
        cmd = chr(0x04) + chr(chan) + chr(lsb) + chr(msb)
        self.sendCmd(cmd)

    def mainControl(self):
        # nuetral
        waist, hturn, htilt = 6000, 6000, 6000
        wheels, turn, arm, shoulder = 6000, 6000, 5200, 6000

        print("--- Robot Control Manual Mode ---")
        print("1/2: Waist | 3/4: Pan | 5/6: Tilt")
        print("W/S: Drive | A/D: Turn")
        print("0: KILL ALL (Silence) | Q: Quit")

        while True:

            user_input = input("-> ").lower()

            if user_input == 'q':
                break

            elif user_input == '0':
                print("Killing all signals...")
                for i in range(6): self.setTarget(i, 0)
                continue

            # --- Logic ---
            elif user_input == "1":
                wheels += 400
            elif user_input == "2":
                wheels -= 400
            elif user_input == "3":
                htilt += 400
            elif user_input == "4":
                htilt -= 400
            elif user_input == "5":
                hturn += 400
            elif user_input == "6":
                hturn -= 400
            elif user_input == "7":
                arm += 400
            elif user_input == "8":
                arm -= 400
            elif user_input == "w":
                turn += 400
            elif user_input == "s":
                turn -= 400
            elif user_input == "a":
                waist += 400
            elif user_input == "d":
                waist -= 400
            elif user_input =="h":
                shoulder += 400
            elif user_input == "j":
                shoulder -= 400


            # Reset to Neutral
            elif user_input == "r":
                waist, hturn, htilt, wheels, turning, arm, shoulder = 6000, 6000, 6000, 6000, 6000, 5200, 6000

            # Execute
            self.setTarget(0, wheels)
            self.setTarget(1, turn)
            self.setTarget(3, htilt)
            self.setTarget(4, hturn)
            self.setTarget(2, waist)
            self.setTarget(5, arm)
            self.setTarget(7, shoulder)
            print(f"Status: W:{waist} P:{hturn} T:{htilt} Drive:{wheels} Elbow:{arm} Shoulder:{shoulder}")


if __name__ == "__main__":
    # Ensure port is /dev/ttyACM0
    x = Controller(ttyStr='/dev/ttyACM0')
    try:
        x.mainControl()
    finally:
        x.usb.close()

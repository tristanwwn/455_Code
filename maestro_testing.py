#This code is just for testing the servos it is not part of project1 functionality




import serial
import time
from sys import version_info

# Initializing Controller with the correct port for Pi
class Controller:
    def __init__(self, ttyStr='/dev/ttyACM0', device=0x0c):
        self.usb = serial.Serial(ttyStr)
        self.PololuCmd = chr(0xaa) + chr(device)


    
    def drive(self, x, y):
        throttle = y
        steering = x 

        #left = max(4000, min(9000, left))
        #right = max(4000, min(9000, right))

        #print(f"DEBUG: Sending to Wheels -> Left (Ch1): {left}, Right (Ch2): {right}")

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
        # Neutral positions
        waist, hturn, htilt = 6000, 6000, 6000
        wheels, turn = 6000, 6000
        
        print("--- Robot Control Manual Mode ---")
        print("1/2: Waist | 3/4: Pan | 5/6: Tilt")
        print("W/S: Drive | A/D: Turn")
        print("0: KILL ALL (Silence) | Q: Quit")

        while True:
            # Simplified for SSH: Type key then press Enter
            user_input = input("-> ").lower()

            if user_input == 'q':
                break
            
            # --- Kill Command (Stops Buzzing) ---
            elif user_input == '0':
                print("Killing all signals...")
                for i in range(6): self.setTarget(i, 0)
                continue # Skip the rest of the loop

            # --- Logic ---
            elif user_input == "1": wheels += 400
            elif user_input == "2": wheels -= 400
            elif user_input == "3": htilt += 400
            elif user_input == "4": htilt -= 400
            elif user_input == "5": hturn += 400
            elif user_input == "6": hturn -= 400
            elif user_input == "w": turn += 400
            elif user_input == "s": turn -= 400
            elif user_input == "a": waist += 400
            elif user_input == "d": waist -= 400
            
            # Reset to Neutral
            elif user_input == "r":
                waist, hturn, htilt, wheels, turning = 6000, 6000, 6000, 6000, 6000

            # Execute
            self.setTarget(0, wheels)
            self.setTarget(1, turn)
            self.setTarget(3, htilt)
            self.setTarget(4, hturn)
            self.setTarget(2, waist)
            
            print(f"Status: W:{waist} P:{hturn} T:{htilt} Drive:{wheels} Turn:{turning}")

if __name__ == "__main__":
    # Ensure port is /dev/ttyACM0
    x = Controller(ttyStr='/dev/ttyACM0')
    try:
        x.mainControl()
    finally:
        x.usb.close()

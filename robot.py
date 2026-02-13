import serial

class TangoRobot:
    def __init__(self):
        
        # Initialize serial - try ACM0 first, then ACM1
        try:
            self.usb = serial.Serial('/dev/ttyACM0')
        except:
            self.usb = serial.Serial('/dev/ttyACM1')
            
        self.CENTER = 6000

    def send_target(self, channel, target):
        
        #ensure the pulse is always within a safe physical range
        if not (3000 <= target <= 9000):
            print(f"Invalid command {target} rejected!")
            return 
            
        lsb = target & 0x7f
        msb = (target >> 7) & 0x7f
        cmd = chr(0xaa) + chr(0x0c) + chr(0x04) + chr(channel) + chr(lsb) + chr(msb)
        self.usb.write(bytes(cmd, 'latin-1'))

    def drive(self, x_val, y_val):
        # This is where you'll put your joystick-to-wheel logic later!
        self.send_target(1, y_val) # Throttle
        self.send_target(2, x_val) # Steering

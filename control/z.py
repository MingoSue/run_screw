import os
from time import sleep
import can

class Motor:
    # None for direction ,0x23 => 1  0x24 => -1 
    run_data = [0x00,0x20,None,0x00,0x00,0x00,0x00,0x03]
    stop_data = [0x00,0x20,0x25,0x00,0x00,0x00,0x00,0x01]
    # None for speed level   1,2,3,4,5,6 - (32,16,8,4,2,1)  1 is slowest   6 is fastest
    set_speed_data = [0x00,0x20,0x33,None,0x00,0x00,0x00,0x0a]
    speed_level_mapping = [0x20,0x10,0x08,0x04,0x02,0x01]


    def __init__(self, can_channel, motor_id):
        """
        Initialization of can motors
        :param can_channel:name of can device
        :param motor_id:can id of motor
        """
        self.bus = can.interface.Bus(
            channel=can_channel, bustype='socketcan_ctypes')
        self.motor_id = motor_id
        self.speed = 0
        self.now_speed = 0
        self.alive = False

 
    def send(self, aid, data):
        msg = can.Message(arbitration_id=aid, data=data, extended_id=False)
        self.bus.send(msg, timeout=1)
        sleep(0.01)


    def run(self, step, direction):
        # 7-14
        if step > 2147483647:
            raise ValueError("step parameter must be a int integer and between 0~2147483647")
        if direction not in (-1, 1):
            raise ValueError("The dir can only be 0 or 1, clockwis: 0  anticclockwise: 1")
        # deal with direction
        self.run_data[2] = 0x23 if direction == 1 else 0x24
        self.run_data[6] = (0xff000000 & step) >> 24
        self.run_data[5] = (0x00ff0000 & step) >> 16
        self.run_data[4] = (0x0000ff00 & step) >> 8
        self.run_data[3] = 0x000000ff & step
        self.send(self.motor_id, self.run_data)
    
    def stop(self):
        self.send(self.motor_id, self.stop_data)

    def set_speed_level(self,level):
        level -=1
        self.set_speed_data[3] = self.speed_level_mapping[level]
        self.send(self.motor_id, self.set_speed_data)


if __name__ == "__main__":
    m1 = Motor('can0', 0xc1)
    m1.run(10000,-1)


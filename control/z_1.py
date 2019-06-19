import os
from time import sleep
import can
from threading import Thread
import serial
from gpiozero import LED


class Motor:
    # None for direction ,0x23 => 1  0x24 => -1 
    run_data = [0x00, 0x20, None, 0x00, 0x00, 0x00, 0x00, 0x03]
    stop_data = [0x00, 0x20, 0x25, 0x00, 0x00, 0x00, 0x00, 0x01]
    # None for speed level   1,2,3,4,5,6 - (32,16,8,4,2,1)  1 is slowest   6 is fastest
    set_speed_data = [0x00, 0x20, 0x33, None, 0x00, 0x00, 0x00, 0x0a]
    speed_level_mapping = [0x20, 0x10, 0x08, 0x04, 0x02, 0x01]

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
        self.weight = 0
    #     self.ser = serial.Serial('/dev/ttyUSB0')
    #     self.refresh_run_m()
    #
    # def refresh_run_m(self):
    #     t = Thread(target=self.refresh_m, name='refresh_can_m')
    #     t.setDaemon(True)
    #     t.start()
    #     print('thread m ok~')
    #
    # def refresh_m(self):
    #     p = LED(22)
    #     while True:
    #         self.ser.write([0x02, 0x03, 0x00, 0x50, 0x00, 0x02, 0xC4, 0x1A])
    #         sleep(0.05)
    #         weight_data = self.ser.read_all()
    #         try:
    #             weight = round(int('0x' + weight_data.hex()[10:14], 16) * 0.001, 3)
    #             if weight >= 10:
    #                 weight = 0
    #         except Exception as e:
    #             print(e)
    #             weight = 0
    #         print('weight===========', weight)
    #         try:
    #             if weight > 2:
    #                 self.weight = weight
    #                 print('zzzzzzzzz> max m : {}'.format(weight))
    #                 # protect io
    #                 p.on()
    #                 print('zzzzzzzzzzz')
    #                 sleep(0.1)
    #                 p.off()
    #         except Exception as e:
    #             print(e)

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


def main():
    m2 = Motor('can0', 0xc2)
    m2.set_speed_level(2)
    step = 0

    while True:
        print('step==========', step)
        m2.run(1000, 1)
        step += 1000
        if step > 5000:
            break
        sleep(5)


if __name__ == "__main__":
    main()


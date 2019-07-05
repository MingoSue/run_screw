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
    set_speed_data = [0x00, 0x20, 0x26, None, 0x00, 0x00, 0x00, 0x02]
    # speed_level_mapping = [0x20, 0x10, 0x08, 0x04, 0x02, 0x01]

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

    def speed_mode(self, speed):
        # speed > 0 forward, speed < 0 backward, speed = 0 stop
        self.run_data[2] = 0x23 if speed > 0 else 0x24
        if speed > 0:
            # speed -= 1
            self.run_speed_mode(speed)
        if speed < 0:
            # speed = int(-speed - 1)
            self.run_speed_mode(-speed)
        if speed == 0:
            self.send(self.motor_id, self.stop_data)

    def run_speed_mode(self, speed):
        # self.set_speed_data[3] = self.speed_level_mapping[speed]
        self.set_speed_data[6] = (0xff000000 & speed) >> 24
        self.set_speed_data[5] = (0x00ff0000 & speed) >> 16
        self.set_speed_data[4] = (0x0000ff00 & speed) >> 8
        self.set_speed_data[3] = 0x000000ff & speed
        # self.set_speed_data[3] = speed
        self.send(self.motor_id, self.set_speed_data)
        sleep(0.05)
        self.send(self.motor_id, self.run_data)


def main():
    m2 = Motor('can0', 0xc1)
    speed = 500

    while True:
        print('speed============', speed)
        m2.speed_mode(speed)
        print('run...')
        sleep(5)
        m2.speed_mode(0)
        sleep(1)
        # speed < 1000
        if speed < 900:
            speed += 50
        elif speed < 1000:
            speed += 10


if __name__ == "__main__":
    main()


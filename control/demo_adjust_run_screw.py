import os
import json
import csv
import serial
from time import sleep
import can
from threading import Thread
from gpiozero import LED, DigitalInputDevice
import time


class Motor:

    def __init__(self, can_channel, motor_id):
        """
        Initialization of can motors
        :param can_channel:name of can device
        :param motor_id:can id of motor
        """
        self.bus = can.interface.Bus(
            channel=can_channel, bustype='socketcan_ctypes')
        self.motor_id = motor_id
        self.weight = 0
        self.ser = serial.Serial('/dev/ttyUSB0')
        self.refresh_run()

    def refresh_run(self):
        t = Thread(target=self.refresh, name='refresh_can')
        t.setDaemon(True)
        t.start()
        print('thread  ok~')

    def refresh(self):
        p = LED(21)
        p.on()
        while True:
            self.ser.write([0x32, 0x03, 0x00, 0x50, 0x00, 0x02, 0xC4, 0x1A])
            sleep(0.05)
            weight_data = self.ser.read_all()
            try:
                weight = round(int('0x' + weight_data.hex()[10:14], 16) * 0.001, 3)
                if weight >= 10:
                    weight = 0
            except Exception as e:
                print(e)
                weight = 0
            try:
                if weight > 2:
                    self.weight = weight
                    print('> max n : {}'.format(weight))
                    # protect io

                    p.off()
                    print('ppppppppppppp')
                    sleep(0.1)
                    p.on()
            except Exception as e:
                print(e)

    def send(self, aid, data):
        print(time.ctime() + 'can data {}'.format(data))
        msg = can.Message(arbitration_id=aid, data=data, extended_id=False)
        self.bus.send(msg, timeout=1)
        sleep(0.01)

    def speed_mode(self, speed):
        """
        :param speed: integer, -255 to 255, speed of left motor, positive speed will go forward,
                           negative speed will go backward
        :return:
        """
        s_speed = speed & 0xff
        times = speed >> 8 & 0xff
        self.send(self.motor_id, [s_speed, times])


class MotorZ:
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
    #     p = LED(21)
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
        # direction = 1 (left, down)
        # direction = -1 (right, up)
        # 7-14
        if step > 2147483647:
            raise ValueError("step parameter must be a int integer and between 0~2147483647")
        if direction not in (-1, 1):
            raise ValueError("The dir can only be 0 or 1, clockwise: 0  anticlockwise: 1")
        # deal with direction
        self.run_data[2] = 0x23 if direction == 1 else 0x24
        self.run_data[6] = (0xff000000 & step) >> 24
        self.run_data[5] = (0x00ff0000 & step) >> 16
        self.run_data[4] = (0x0000ff00 & step) >> 8
        self.run_data[3] = 0x000000ff & step
        self.send(self.motor_id, self.run_data)

    def stop(self):
        self.send(self.motor_id, self.stop_data)

    def set_speed_level(self, level):
        level -= 1
        self.set_speed_data[3] = self.speed_level_mapping[level]
        self.send(self.motor_id, self.set_speed_data)


# if __name__ == "__main__":
#     m1 = MotorZ('can0', 0xc1)
#     m1.run(10000, -1)


def main():
    m1 = MotorZ('can0', 0xc1)
    m2 = MotorZ('can0', 0xc2)
    m1.set_speed_level(3)
    m2.set_speed_level(1)

    can_motors = Motor('can0', 0x13)
    n = 0
    i = 0
    # cycle times
    m = 0

    # with open('z_log.csv', "a+", newline='') as file:
    #     csv_file = csv.writer(file)
    #     head = ["cycle", "time", "weight", "m-weight"]
    #     csv_file.writerow(head)

    step = 0
    step_right = 0
    total = 0
    total_up = 0
    while True:

        while True:
            m2.run(1000, 1)
            total += 1
            can_motors.speed_mode(int(304*0.8))
            sleep(0.5)
            if can_motors.weight > 2:
                print('=============> max n : {}'.format(can_motors.weight))
                can_motors.weight = 0
                print('total-----------', total)
                sleep(2)
                break
        sleep(2.5)
        while True:
            # reverse
            can_motors.speed_mode(-275)
            sleep(0.5)
            print('gaga')
            # 再用一次循环
            while True:
                if total_up < 5:
                    m2.run(1000, -1)
                    sleep(0.1)
                    print('up>>>>>>>>>>')
                    total_up += 1
                if total_up >= 5:
                    break
            sleep(0.8)
            print('total_up...', total_up)
            total_up = 0
            can_motors.speed_mode(0)
            m2.set_speed_level(2)
            m2.run(5000, -1)
            sleep(2)
            m2.set_speed_level(1)
            break

        sleep(2)
        if step >= 2:
            print('step_right///////////', step_right)
            m1.run(4500, -1)
            sleep(2)
            step_right += 1
            if step_right >= 2:
                print('recycle.............')
                while True:
                    m2.run(1000, 1)
                    total += 1
                    can_motors.speed_mode(int(304 * 0.8))
                    sleep(0.5)
                    if can_motors.weight > 2:
                        print('=============> max n : {}'.format(can_motors.weight))
                        can_motors.weight = 0
                        print('total-----------', total)
                        sleep(2)
                        break
                sleep(2.5)
                while True:
                    # reverse
                    can_motors.speed_mode(-275)
                    sleep(0.5)
                    print('gaga')
                    # 再用一次循环
                    while True:
                        if total_up < 5:
                            m2.run(1000, -1)
                            sleep(0.1)
                            print('up>>>>>>>>>>')
                            total_up += 1
                        if total_up >= 5:
                            break
                    sleep(0.8)
                    print('total_up...', total_up)
                    total_up = 0
                    can_motors.speed_mode(0)
                    m2.set_speed_level(2)
                    m2.run(5000, -1)
                    sleep(2)
                    m2.set_speed_level(1)
                    break
                sleep(2)
                m1.run(4500, 1)
                step = 1
                step_right = 0

        else:
            print('step============', step)
            m1.run(4500, 1)
            step += 1

        sleep(5)


if __name__ == "__main__":
    main()

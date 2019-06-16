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
        p = LED(22)
        while True:
            self.ser.write([0x01, 0x03, 0x00, 0x50, 0x00, 0x02, 0xC4, 0x1A])
            sleep(0.1)
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
                    p.on()
                    print('ppppppppppppp')
                    sleep(0.1)
                    p.off()
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

    can_motors = Motor('can0', 0x13)
    n = 0
    # cycle times
    m = 0

    with open('z_log.csv', "a+", newline='') as file:
        csv_file = csv.writer(file)
        head = ["cycle", "time", "weight"]
        csv_file.writerow(head)

    step = 0
    step_right = 0
    while True:

        while True:
            m2.run(5000, 1)

            while True:
                print('nnnnnnnnnnnnnn', n)
                can_motors.speed_mode(304)
                sleep(0.5)

                try:
                    print('weight==============', can_motors.weight)
                    if can_motors.weight > 2:
                        print('=============> max n : {}'.format(can_motors.weight))
                        sleep(2)

                        # reverse
                        can_motors.speed_mode(-304)
                        print('gaga')
                        sleep(4)
                        can_motors.speed_mode(0)
                        m += 1
                        n = 0
                        print('mmmmmmmmmmmmm', m)
                        with open('z_log.csv', "a+", newline='') as f:
                            csv_f = csv.writer(f)
                            data = [m, time.ctime(), can_motors.weight]
                            csv_f.writerow(data)
                        print('haha')
                        can_motors.weight = 0
                        print('bobo...............', can_motors.weight)

                        break

                       # sleep(2)
                    else:
                        print('again...')
                        n += 1
                        if n >= 15:
                            print('end...')
                            with open('z_log.csv', "a+", newline='') as fi:
                                csv_fi = csv.writer(fi)
                                end = [m, time.ctime(), can_motors.weight, 'end']
                                csv_fi.writerow(end)
                            break
                        sleep(0.5)
                except Exception as e:
                    print(e)
            sleep(10)
            m2.run(5000, -1)

            break

        if step > 50000:
            m1.run(5000, -1)
            step_right += 5000
            if step_right > 50000:
                m1.run(5000, 1)
                step = 5000
                step_right = 0
            # break

        else:
            m1.run(5000, 1)
            step += 5000

        sleep(10)


if __name__ == "__main__":
    main()

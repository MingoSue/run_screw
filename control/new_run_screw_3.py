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


def main():
    can_motors = Motor('can0', 0x13)
    n = 0
    # cycle times
    m = 0

    with open('screw_log.csv', "a+", newline='') as file:
        csv_file = csv.writer(file)
        head = ["cycle", "time", "weight"]
        csv_file.writerow(head)
    while True:
        print('nnnnnnnnnnnnnn', n)
        can_motors.speed_mode(304)
        sleep(0.5)

        try:
            print('weight==============', can_motors.weight)
            if can_motors.weight > 2:
                print('=============> max n : {}'.format(can_motors.weight))
                sleep(7)

                # reverse
                can_motors.speed_mode(-304)
                print('gaga')
                sleep(3)
                can_motors.speed_mode(0)
                m += 1
                n = 0
                print('mmmmmmmmmmmmm', m)
                with open('screw_log.csv', "a+", newline='') as f:
                    csv_f = csv.writer(f)
                    data = [m, time.ctime(), can_motors.weight]
                    csv_f.writerow(data)
                print('haha')

                sleep(3)
            else:
                print('again...')
                n += 1
                if n >= 100:
                    break
                sleep(0.5)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()

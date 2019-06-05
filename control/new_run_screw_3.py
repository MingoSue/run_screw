import os
import json
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
        self.speed = 0
        self.now_speed = 0
        self.position = 0
        self.current = 0
        self.ser = serial.Serial('/dev/ttyUSB0')

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
    p = LED(22)
    n = 0
    while True:
        print('nnnnnnnnnnnnnn', n)
        n += 1
        can_motors.speed_mode(304)
        sleep(0.5)

        can_motors.ser.write([0x01, 0x03, 0x00, 0x50, 0x00, 0x02, 0xC4, 0x1A])
        sleep(0.1)

        weight_data = can_motors.ser.read_all()
        try:
            weight = round(int('0x' + weight_data.hex()[10:14], 16) * 0.001, 3)
            if weight >= 10:
                weight = 0
        except Exception as e:
            print(e)
            weight = 0
        try:
            print('weight==============', weight)
            if weight > 2:
                print('> max n : {}'.format(weight))
                # protect io
                can_motors.speed_mode(0)
                p.on()
                sleep(0.1)
                p.off()
                # stop
                sleep(3)

                # reverse
                can_motors.speed_mode(-304)
                print('gaga')
                sleep(10)
                can_motors.speed_mode(0)
                print('haha')
                sleep(3)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()

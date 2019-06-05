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

    # def serial_refresh(self):
    #     p = LED(22)
    #     while True:
    #         self.ser.write([0x01, 0x03, 0x00, 0x50, 0x00, 0x02, 0xC4, 0x1A])
    #         sleep(0.1)
    #         weight_data = self.ser.read_all()
    #         try:
    #             weight = round(int('0x'+weight_data.hex()[10:14],16)*0.001,3)
    #             if weight >=10:
    #                 weight = 0
    #         except Exception as e:
    #             print(e)
    #             weight = 0
    #         try:
    #             with open('weight.json', 'w') as f:
    #                 json.dump({'weight':weight}, f)
    #
    #             with open('screw_config.json', 'r') as f:
    #                 config = json.load(f)
    #
    #             if weight>config['n']:
    #                 print('> max n : {}'.format(weight))
    #                 config.update({'power':0})
    #                 with open('screw_config.json', 'w') as f:
    #                     json.dump(config,f)
    #                 # protect io
    #                 p.on()
    #                 sleep(0.1)
    #                 p.off()
    #         except Exception as e:
    #             print(e)

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
    pre_speed = None
    init_power = 1
    init_direction = 1
    p = LED(22)
    while True:
        # power 1 :on  0:off
        power = init_power
        # direction 1 , -1
        direction = init_direction
        # 20% 50%  100%
        speed = 1
        actual_speed = int(304 * speed * direction)
        
        if power:
            # run
            if actual_speed != pre_speed:
                if actual_speed < 0:
                    can_motors.speed_mode(actual_speed)
                    sleep(2.5)
                    can_motors.speed_mode(0)
                    sleep(0.5)
                    init_power = 1
                    init_direction = 1
                else:
                    can_motors.speed_mode(actual_speed)
        # else:
        #     if pre_power:
        #         can_motors.speed_mode(0)
        #         pre_speed = 0
        # pre_power = power
        # sleep(0.5)

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
            if weight > 2:
                print('> max n : {}'.format(weight))
                # protect io
                p.on()
                sleep(0.1)
                p.off()
                # stop
                can_motors.speed_mode(0)
                pre_speed = 0
                sleep(0.5)
                # reverse
                init_power = 1
                init_direction = -1
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()

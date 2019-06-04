import os
import json
import serial
from time import sleep
import can
from threading import Thread
from gpiozero import LED

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
        self.refresh_run()

    def send(self, aid, data):
        print(data)
        msg = can.Message(arbitration_id=aid, data=data, extended_id=False)
        self.bus.send(msg, timeout=1)
        sleep(0.01)

    def refresh_run(self):
        t = Thread(target=self.refresh)
        t.setDaemon(True)
        t.start()
        t2 = Thread(target=self.serial_refresh)
        t2.setDaemon(True)
        t2.start()

    def serial_refresh(self):
        p = LED(22)
        while True:
            self.ser.write([0x01, 0x03, 0x00, 0x50, 0x00, 0x02, 0xC4, 0x1A])
            sleep(0.1)
            weight_data = self.ser.read_all()
            try:
                weight = round(int('0x'+weight_data.hex()[10:14],16)*0.001,3)
                if weight >=10:
                    weight = 0
            except Exception as e:
                print(e)
                weight = 0
            with open('weight.json', 'w') as f:
                json.dump({'weight':weight}, f)
            
            with open('screw_config.json', 'r') as f:
                config = json.load(f)
 
            if weight>config['n']:
                print('> max n : {}'.format(weight))
                config.update({'power':0})
                with open('screw_config.json', 'w') as f:
                    json.dump(config,f)
                # protect io
                p.on()
                sleep(0.1)
                p.off()



    def refresh(self):
        while True:
            data = self.bus.recv()
            if data.arbitration_id != 0x1b:
                continue
            data = data.data
            if data[3] > 0xee:
                now_speed = (data[3] - 0xff) * 256 + (data[2] - 0xff)
            else:
                now_speed = data[2] | (data[3] << 8)
            self.now_speed = now_speed
            self.current = data[0] | (data[1] << 8)
            self.position = data[4] | (data[5] << 8) | (data[6] << 16) | (data[7] << 24)
            # print(self.current, self.now_speed, self.position)
            self.direction = 1 if self.now_speed > 0 else -1
            # sleep(0.1)
            screw_data = {'speed': self.now_speed, 'current': self.current if self.current<10000 else 0, 'direction': self.direction}
            with open('screw.json', 'w') as f:
                json.dump(screw_data, f)
            sleep(0.001)

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
    pre_power = None
    while True:
        with open('screw_config.json', 'r') as f:
            config = json.load(f)
        # power 1 :on  0:off
        power = config['power']
        # direction 1 , -1
        direction = config['direction']
        # 20% 50%  100%
        speed = config['speed']
        actual_speed = int(304 * speed * direction)
        
        if power:
            # run
            if actual_speed != pre_speed:
                can_motors.speed_mode(actual_speed)
                pre_speed = actual_speed
        else:
            if pre_power:
                can_motors.speed_mode(0)
                pre_speed = 0
        pre_power = power
        sleep(0.5)


if __name__ == "__main__":
    main()

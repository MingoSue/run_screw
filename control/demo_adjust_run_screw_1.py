import os
import pytz
import sys
import json
import csv
import serial
from time import sleep
import can
from threading import Thread
from gpiozero import LED, DigitalInputDevice
import time

import django
from django.utils import timezone
from django.db.models import Avg

sys.path.append('..')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ScrewDriver.settings")

django.setup()

from control.models import Records, ScrewConfig, Weight


def get_current_time(datetimenow=None, naive_datetime=False, customtimezone=None):
    timezone_datetime = datetimenow
    if datetimenow and not datetimenow.tzinfo:
        # change naive datetime to datetime with timezone
        # use timezone.localize will include day light saving to get more accurate timing
        timezone_datetime = pytz.timezone(os.environ.get('TZ')).localize(datetimenow)
    tz = None
    if customtimezone:
        try:
            tz = pytz.timezone(customtimezone)
        except:
            pass

    # convert to datetime with user local timezone
    converted_datetime = timezone.localtime(timezone_datetime or timezone.now(), tz)
    # return datetime converted
    return converted_datetime.replace(tzinfo=None) if naive_datetime else converted_datetime


class Motor:

    def __init__(self, can_channel, motor_id):
        """
        Initialization of can motors
        :param can_channel:name of can device
        :param motor_id:can id of motor
        """
        self.bus = can.interface.Bus(
            channel=can_channel, bustype='socketcan_ctypes')
        self.speed = 0
        self.now_speed = 0
        self.position = 0
        self.current = 0
        self.motor_id = motor_id
        self.weight = 0
        self.ser = serial.Serial('/dev/ttyUSB1')
        self.refresh_run()

    def refresh_run(self):
        t = Thread(target=self.refresh, name='refresh_can')
        t.setDaemon(True)
        t.start()
        t2 = Thread(target=self.serial_refresh, name='refresh_serial')
        t2.setDaemon(True)
        t2.start()
        t3 = Thread(target=self.button_refresh, name='refresh_button')
        t3.setDaemon(True)
        t3.start()
        print('three thread  ok~')

    def button_refresh(self):
        b_out = DigitalInputDevice(27)
        b_in = DigitalInputDevice(17)
        bin_pre = 0
        bout_pre = 0
        while True:
            bin_now = b_in.value
            bout_now = b_out.value
            sleep(0.01)
            bin_now2 = b_in.value
            bout_now2 = b_out.value

            if bin_now and bin_now2:
                bin_now = 1
            else:
                bin_now = 0

            if bout_now and bout_now2:
                bout_now = 1
            else:
                bout_now = 0
            if bin_now and not bin_pre:
                print('power on ppp')
                poweron_p()
            elif bout_now and not bout_pre:
                print('power on nnn')
                poweron_n()
            elif not any([bin_now, bout_now]) and any([bin_pre, bout_pre]):
                sleep(0.1)
                print('poweroff...')
                # poweroff()
            else:
                pass
            bin_pre = bin_now
            bout_pre = bout_now
            sleep(0.3)

    def serial_refresh(self):
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
                with open('weight.json', 'w') as f:
                    json.dump({'weight': weight}, f)

                with open('screw_config.json', 'r') as f:
                    config = json.load(f)

                if weight > config['n']:
                    self.weight = weight
                    print('> max n : {}'.format(weight))
                    # protect io

                    p.off()
                    print('ppppppppppppp')
                    sleep(0.1)
                    p.on()
            except Exception as e:
                print(e)

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
            direction = 1 if self.now_speed > 0 else -1
            # sleep(0.1)
            screw_data = {'speed': self.now_speed, 'current': self.current if self.current < 10000 else 0,
                          'direction': direction}
            with open('screw.json', 'w') as f:
                json.dump(screw_data, f)
            sleep(0.001)

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


def poweron_p():
    with open('screw_config.json', 'r') as f:
        config = json.load(f)
    config.update({'power': 1, "direction": 1})
    with open('screw_config.json', 'w') as f:
        json.dump(config, f)


def poweron_n():
    with open('screw_config.json', 'r') as f:
        config = json.load(f)
    config.update({'power': 1, "direction": -1})
    with open('screw_config.json', 'w') as f:
        json.dump(config, f)


def poweroff():
    with open('screw_config.json', 'r') as f:
        config = json.load(f)
    config.update({'power': 0})
    with open('screw_config.json', 'w') as f:
        json.dump(config, f)


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


def main():
    m1 = MotorZ('can0', 0xc1)
    m2 = MotorZ('can0', 0xc2)
    m1.set_speed_level(3)
    m2.set_speed_level(3)

    can_motors = Motor('can0', 0x13)
    n = 0
    i = 0
    # cycle times
    m = 0

    step = 0
    step_right = 0
    total = 0
    total_up = 0

    p = 0

    man_position = 0
    man_cycle = 0
    while True:

        try:
            with open('adjust_screw_config.json', 'r') as f:
                config = json.load(f)
        except Exception as e:
            print('config error', e)
            config = {"speed": 0.2, "direction": 1, "n": 2, "power": 1, "auto": 1, "position": 0}
        # power 1 :on  0:off
        power = config['power']
        weight = config['n']
        auto = config['auto']
        # default 0, values=1,2,3
        position = config['position']

        i += 1
        print('iiiiiiiii', i)

        if power == 1:

            if auto == 1:
                while True:
                    p += 1
                    r = 0
                    while True:
                        r += 1
                        can_motors.speed_mode(200)
                        sleep(0.5)

                        record = Records()
                        record.speed = 200
                        record.direction = 1
                        record.current = can_motors.current if can_motors.current < 10000 else 0
                        record.config_weight = weight
                        record.start_time = get_current_time()

                        if r >= 5 and p != 1:
                            break
                        elif r >= 10:
                            break
                    while True:
                        print('total]]]]]]]]]]', total)
                        m2.run(200, 1)
                        total += 1
                        if total > 3 and can_motors.weight > weight:
                            print('mmmmmmmmmmmmm', m)
                            m += 1
                            n = 0

                            record.cycle = m
                            record.weight = can_motors.weight
                            record.d_weight = can_motors.weight - weight
                            record.end_time = get_current_time()
                            record.total_time = (record.end_time - record.start_time).seconds
                            record.save()

                            can_motors.weight = 0
                            total = 0
                            sleep(2)
                            break
                        sleep(0.1)
                    break
                print('here here...')
                sleep(2.5)
                while True:
                    # reverse
                    can_motors.speed_mode(-180)
                    sleep(0.5)

                    record = Records()
                    record.cycle = m
                    record.speed = -180
                    record.direction = -1
                    record.current = can_motors.current if can_motors.current < 10000 else 0
                    record.weight = can_motors.weight
                    record.save()

                    print('gaga')
                    # 再用一次循环
                    while True:
                        if total_up < 15:
                            m2.run(200, -1)
                            sleep(0.1)
                            print('up>>>>>>>>>>', total_up)
                            total_up += 1
                        if total_up >= 15:
                            break
                    sleep(0.8)
                    print('total_up...', total_up)
                    total_up = 0
                    can_motors.speed_mode(0)
                    m2.run(3000, -1)
                    sleep(2)
                    break

                # sleep(2)
                if step >= 2:
                    print('step_right///////////', step_right)
                    m1.run(4800, -1)
                    sleep(2)
                    step_right += 1
                    if step_right >= 2:
                        print('recycle.............')
                        try:
                            with open('screw_config.json', 'r') as f:
                                config = json.load(f)
                        except:
                            continue
                        # power 1 :on  0:off
                        power = config['power']
                        weight = config['n']

                        i += 1
                        print('iiiiiiiii', i)

                        if power == 1:
                            while True:
                                r = 0
                                while True:
                                    r += 1
                                    can_motors.speed_mode(200)
                                    sleep(0.5)

                                    record = Records()
                                    record.speed = 200
                                    record.direction = 1
                                    record.current = can_motors.current if can_motors.current < 10000 else 0
                                    record.config_weight = weight
                                    record.start_time = get_current_time()

                                    if r >= 5:
                                        break
                                while True:
                                    print('total]]]]]]]]]]', total)
                                    m2.run(200, 1)
                                    total += 1
                                    if total > 3 and can_motors.weight > weight:
                                        print('mmmmmmmmmmmmm22222222', m)
                                        m += 1
                                        n = 0

                                        record.cycle = m
                                        record.weight = can_motors.weight
                                        record.d_weight = can_motors.weight - weight
                                        record.end_time = get_current_time()
                                        record.total_time = (record.end_time - record.start_time).seconds
                                        record.save()

                                        can_motors.weight = 0
                                        total = 0
                                        sleep(2)
                                        break
                                    sleep(0.1)
                                break
                            print('here here...')
                            sleep(2.5)
                            while True:
                                # reverse
                                can_motors.speed_mode(-180)
                                sleep(0.5)

                                record = Records()
                                record.cycle = m
                                record.speed = -180
                                record.direction = -1
                                record.current = can_motors.current if can_motors.current < 10000 else 0
                                record.weight = can_motors.weight
                                record.save()

                                print('gaga')
                                # 再用一次循环
                                while True:
                                    if total_up < 15:
                                        m2.run(200, -1)
                                        sleep(0.1)
                                        print('up>>>>>>>>>>', total_up)
                                        total_up += 1
                                    if total_up >= 15:
                                        break
                                sleep(0.8)
                                print('total_up...', total_up)
                                total_up = 0
                                can_motors.speed_mode(0)
                                m2.run(3000, -1)
                                sleep(2)
                                break
                            sleep(2)
                            m1.run(4800, 1)
                            step = 1
                            step_right = 0
                        else:
                            print('stand by...222222')

                else:
                    print('step============', step)
                    m1.run(4800, 1)
                    step += 1

                sleep(0.5)

            # 手动
            else:
                if position == 1 and man_cycle == 0:
                    if man_position == 4800:
                        m1.run(4800, -1)
                        man_position -= 4800
                    elif man_position == 9600:
                        m1.run(9600, -1)
                        man_position -= 9600
                    sleep(1)
                    while True:
                        p += 1
                        r = 0
                        while True:
                            r += 1
                            can_motors.speed_mode(200)
                            sleep(0.5)

                            record = Records()
                            record.speed = 200
                            record.direction = 1
                            record.current = can_motors.current if can_motors.current < 10000 else 0
                            record.config_weight = weight
                            record.start_time = get_current_time()

                            if r >= 5 and p != 1:
                                break
                            elif r >= 10:
                                break
                        while True:
                            print('total]]]]]]]]]]', total)
                            m2.run(200, 1)
                            total += 1
                            if total > 3 and can_motors.weight > weight:
                                print('mmmmmmmmmmmmm', m)
                                m += 1
                                n = 0

                                record.cycle = m
                                record.weight = can_motors.weight
                                record.d_weight = can_motors.weight - weight
                                record.end_time = get_current_time()
                                record.total_time = (record.end_time - record.start_time).seconds
                                record.save()

                                can_motors.weight = 0
                                total = 0
                                sleep(2)
                                break
                            sleep(0.1)
                        break
                    print('here here...')
                    sleep(2.5)
                    while True:
                        # reverse
                        can_motors.speed_mode(-180)
                        sleep(0.5)

                        record = Records()
                        record.cycle = m
                        record.speed = -180
                        record.direction = -1
                        record.current = can_motors.current if can_motors.current < 10000 else 0
                        record.weight = can_motors.weight
                        record.save()

                        print('gaga')
                        # 再用一次循环
                        while True:
                            if total_up < 15:
                                m2.run(200, -1)
                                sleep(0.1)
                                print('up>>>>>>>>>>', total_up)
                                total_up += 1
                            if total_up >= 15:
                                break
                        sleep(0.8)
                        print('total_up...', total_up)
                        total_up = 0
                        can_motors.speed_mode(0)
                        m2.run(3000, -1)
                        sleep(2)
                        break
                    man_cycle = 1
                if position == 2 and man_cycle == 0:
                    if man_position == 0:
                        m1.run(4800, 1)
                        man_position += 4800
                    elif man_position == 9600:
                        m1.run(4800, -1)
                        man_position -= 4800
                    sleep(1)
                    while True:
                        p += 1
                        r = 0
                        while True:
                            r += 1
                            can_motors.speed_mode(200)
                            sleep(0.5)

                            record = Records()
                            record.speed = 200
                            record.direction = 1
                            record.current = can_motors.current if can_motors.current < 10000 else 0
                            record.config_weight = weight
                            record.start_time = get_current_time()

                            if r >= 5 and p != 1:
                                break
                            elif r >= 10:
                                break
                        while True:
                            print('total]]]]]]]]]]', total)
                            m2.run(200, 1)
                            total += 1
                            if total > 3 and can_motors.weight > weight:
                                print('mmmmmmmmmmmmm', m)
                                m += 1
                                n = 0

                                record.cycle = m
                                record.weight = can_motors.weight
                                record.d_weight = can_motors.weight - weight
                                record.end_time = get_current_time()
                                record.total_time = (record.end_time - record.start_time).seconds
                                record.save()

                                can_motors.weight = 0
                                total = 0
                                sleep(2)
                                break
                            sleep(0.1)
                        break
                    print('here here...')
                    sleep(2.5)
                    while True:
                        # reverse
                        can_motors.speed_mode(-180)
                        sleep(0.5)

                        record = Records()
                        record.cycle = m
                        record.speed = -180
                        record.direction = -1
                        record.current = can_motors.current if can_motors.current < 10000 else 0
                        record.weight = can_motors.weight
                        record.save()

                        print('gaga')
                        # 再用一次循环
                        while True:
                            if total_up < 15:
                                m2.run(200, -1)
                                sleep(0.1)
                                print('up>>>>>>>>>>', total_up)
                                total_up += 1
                            if total_up >= 15:
                                break
                        sleep(0.8)
                        print('total_up...', total_up)
                        total_up = 0
                        can_motors.speed_mode(0)
                        m2.run(3000, -1)
                        sleep(2)
                        break
                    man_cycle = 1
                if position == 3 and man_cycle == 0:
                    if man_position == 0:
                        m1.run(9600, 1)
                        man_position += 9600
                    elif man_position == 4800:
                        m1.run(4800, 1)
                        man_position += 4800
                    sleep(1)
                    while True:
                        p += 1
                        r = 0
                        while True:
                            r += 1
                            can_motors.speed_mode(200)
                            sleep(0.5)

                            record = Records()
                            record.speed = 200
                            record.direction = 1
                            record.current = can_motors.current if can_motors.current < 10000 else 0
                            record.config_weight = weight
                            record.start_time = get_current_time()

                            if r >= 5 and p != 1:
                                break
                            elif r >= 10:
                                break
                        while True:
                            print('total]]]]]]]]]]', total)
                            m2.run(200, 1)
                            total += 1
                            if total > 3 and can_motors.weight > weight:
                                print('mmmmmmmmmmmmm', m)
                                m += 1
                                n = 0

                                record.cycle = m
                                record.weight = can_motors.weight
                                record.d_weight = can_motors.weight - weight
                                record.end_time = get_current_time()
                                record.total_time = (record.end_time - record.start_time).seconds
                                record.save()

                                can_motors.weight = 0
                                total = 0
                                sleep(2)
                                break
                            sleep(0.1)
                        break
                    print('here here...')
                    sleep(2.5)
                    while True:
                        # reverse
                        can_motors.speed_mode(-180)
                        sleep(0.5)

                        record = Records()
                        record.cycle = m
                        record.speed = -180
                        record.direction = -1
                        record.current = can_motors.current if can_motors.current < 10000 else 0
                        record.weight = can_motors.weight
                        record.save()

                        print('gaga')
                        # 再用一次循环
                        while True:
                            if total_up < 15:
                                m2.run(200, -1)
                                sleep(0.1)
                                print('up>>>>>>>>>>', total_up)
                                total_up += 1
                            if total_up >= 15:
                                break
                        sleep(0.8)
                        print('total_up...', total_up)
                        total_up = 0
                        can_motors.speed_mode(0)
                        m2.run(3000, -1)
                        sleep(2)
                        break
                    man_cycle = 1

        else:
            print('stand by...')
        sleep(1)


if __name__ == "__main__":
    main()

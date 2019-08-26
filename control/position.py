# 平面定位第一版, 步数模式
import sys
import json
import serial
from time import sleep
import can
from threading import Thread
from gpiozero import LED, DigitalInputDevice
import time


class MotorX:
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


class MotorZ:
    # None for direction ,0x23 => 1  0x24 => -1
    run_data = [0x00, 0x20, None, 0x00, 0x00, 0x00, 0x00, 0x03]
    stop_data = [0x00, 0x20, 0x25, 0x00, 0x00, 0x00, 0x00, 0x01]
    # None for speed level   1,2,3,4,5,6 - (32,16,8,4,2,1)  1 is slowest   6 is fastest
    set_speed_data = [0x00, 0x20, 0x26, None, 0x00, 0x00, 0x00, 0x02]

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

    def speed_mode(self, speed):
        # speed > 0 forward, speed < 0 backward, speed = 0 stop, should < 1000, more bigger more slower
        self.run_data[2] = 0x23 if speed > 0 else 0x24
        if speed > 0:
            self.run_speed_mode(speed)
        if speed < 0:
            self.run_speed_mode(-speed)
        if speed == 0:
            self.send(self.motor_id, self.stop_data)
            print('stopzzzzzzzzzzzzzzzzz')

    def run_speed_mode(self, speed):
        self.set_speed_data[6] = (0xff000000 & speed) >> 24
        self.set_speed_data[5] = (0x00ff0000 & speed) >> 16
        self.set_speed_data[4] = (0x0000ff00 & speed) >> 8
        self.set_speed_data[3] = 0x000000ff & speed
        self.send(self.motor_id, self.set_speed_data)
        sleep(0.05)
        self.send(self.motor_id, self.run_data)


def main():
    x = MotorX('can0', 0xc1)
    y = MotorX('can0', 0xc3)

    # 设置xy轴运行速度等级
    x.set_speed_level(3)
    y.set_speed_level(3)

    # xy轴固定运行步数
    x_step = 4800
    y_step = 48300
    # x轴调整步数
    step_add = 2500

    # x轴左右移动位置参数
    step = 0
    step_right = 0

    # y轴向后运动信号变量
    step_f = 0
    step_b = 0
    # y轴向前运动信号变量
    f_cycle = 0
    b_cycle = 0

    # 手动模式位置参数
    y_position = 0
    has_run = 0

    # 自动模式复位参数，标示关闭自动后螺丝所在位置[1(6),2(5),3(4)]
    a_cycle = 1
    y_cycle = 0

    # try:
    #     with open('adjust_screw_config.json', 'r') as f:
    #         config = json.load(f)
    # except Exception as e:
    #     print('config error', e)
    config_1 = {"speed": 1, "speed2": 350, "direction": 1, "n": 1, "n2": 1, "power": 0, "auto": 0, "position": 0,
                "screw_type": "test001"}

    while True:

        try:
            with open('adjust_screw_config.json', 'r') as f:
                config = json.load(f)
        except Exception as e:
            print('config error', e)
            config = {"speed": 1, "speed2": 350, "direction": 1, "n": 1, "n2": 1, "power": 0, "auto": 0, "position": 0}
        # power 1 :on  0:off
        power = config['power']
        auto = config['auto']
        # default 0, values=1,2,3,4,5,6
        position = config['position']

        weight = config['n']
        d_weight = 1
        weight_z = 1

        if power == 1:

            if auto == 1:
                # pre-start
                r = 0
                p += 1
                while True:
                    r += 1
                    can_motors.speed_mode(0)
                    sleep(0.5)

                    if p != 1:
                        break
                    elif r >= 5:
                        break
                settled_list = Records.objects.filter(screw_type=screw_type, is_settled=True,
                                                      total_time__gt=0).distinct().aggregate(Avg('total_time'))
                if settled_list['total_time__avg']:
                    avg_time = settled_list['total_time__avg']
                    print('%%%%%%%%%%%%%avg_time', avg_time)
                else:
                    record_list = Records.objects.filter(direction=1, d_weight__gt=0, total_time__gt=0,
                                                         screw_type=screw_type).distinct().aggregate(Avg('total_time'))
                    print('record_list==========', record_list)
                    avg_time = record_list['total_time__avg'] if record_list['total_time__avg'] else 0.0
                if avg_time != 0.0:
                    s_time = avg_time - 0.5
                    print('sssssssssss_time', s_time)

                    if s_time > 0:
                        # first stage
                        print('start...')
                        z.speed_mode(speed2)
                        # if auto == 1:
                        # else z.speed_mode(0)
                        if can_motors.weight_z > weight_z:
                            print('can_motors.weight_z===========', can_motors.weight_z)
                            record = Records()
                            record.screw_type = screw_type
                            record.speed = speed1
                            record.direction = 1
                            record.current = can_motors.current if can_motors.current < 10000 else 0
                            record.config_weight = weight
                            record.start_time = get_current_time()
                            
                            can_motors.speed_mode(speed1)
                            sleep(s_time)

                            z.speed_mode(0)
                            # second stage
                            print('actual_speeddddddddddddddd', actual_speed)
                            while True:
                                can_motors.speed_mode(actual_speed)
                                record.actual_speed = actual_speed
                                if can_motors.weight > weight:
                                    break
                            if can_motors.weight > weight:
                                print('can_motors.weight2222222222222', can_motors.weight)
                                m += 1

                                record.cycle = m
                                record.weight = can_motors.weight
                                record.d_weight = can_motors.weight - weight
                                record.end_time = get_current_time()
                                record.total_time = (record.end_time - record.start_time).total_seconds()
                                if record.total_time - avg_time > 0.5:
                                    record.total_time = 0
                                print('record.total_time&&&&&&&&&&&&&&', record.total_time)

                                if record.d_weight > 3:
                                    print('cycle...up...')
                                    while True:
                                        z.speed_mode(-speed2)
                                        if can_motors.up_limit == 1:
                                            z.speed_mode(0)
                                            # 复位
                                            if y_cycle == 1:
                                                y.run(y_step, 1)
                                                # sleep(3)
                                                y_cycle = 0
                                                if a_cycle == 2:
                                                    x.run(x_step + step_add, -1)
                                                    a_cycle = 1
                                                    step = 0
                                                elif a_cycle == 3:
                                                    x.run(x_step * 2 + step_add, -1)
                                                    a_cycle = 1
                                                    step = 0
                                                elif a_cycle == 1:
                                                    x.run(step_add, -1)
                                                    a_cycle = 1
                                                    step = 0
                                            else:
                                                if a_cycle == 2:
                                                    x.run(x_step, -1)
                                                    a_cycle = 1
                                                    step = 0
                                                elif a_cycle == 3:
                                                    x.run(x_step * 2, -1)
                                                    a_cycle = 1
                                                    step = 0

                                            print('cycle...stop...')

                                            with open('adjust_screw_config.json', 'r') as f:
                                                config = json.load(f)
                                            config.update({'power': 0})
                                            with open('adjust_screw_config.json', 'w') as f:
                                                json.dump(config, f)
                                            break
                                    record.save()
                                    can_motors.weight = 0

                                else:

                                    if record.d_weight > d_weight and actual_speed > 5:
                                        actual_speed -= 5
                                    # if record.d_weight < 1:
                                    #     record.is_settled = True
                                    #     print('settled...')
                                    #     actual_speed += 5
                                    else:
                                        record.is_settled = True
                                        print('settled...')
                                    record.save()
                                    can_motors.weight = 0

                                    print('here here...')
                                    sleep(4.5)
                                    # reverse
                                    can_motors.speed_mode(-speed1)
                                    z.speed_mode(-speed2)

                                    record = Records()
                                    record.screw_type = screw_type
                                    record.cycle = m
                                    record.speed = -speed1
                                    record.direction = -1
                                    record.current = can_motors.current if can_motors.current < 10000 else 0
                                    record.weight = can_motors.weight
                                    record.save()

                                    sleep(s_time)
                                    print('gaga')

                                    can_motors.speed_mode(0)
                                    can_motors.weight = 0
                                    z.speed_mode(-200)
                                    sleep(1.5)
                                    z.speed_mode(0)
                                    can_motors.weight_z = 0

                                    config_data = ScrewConfig()
                                    config_data.n = weight
                                    config_data.power = power
                                    config_data.direction = direction
                                    config_data.speed = speed1
                                    config_data.actual_speed = actual_speed
                                    config_data.cycle = m
                                    config_data.save()

                                    print('end...')
                                    sleep(2)

                                    print('again...')
                                    if step >= 2 and step_b == 1:
                                        step_f = 1
                                    if step < 2 and f_cycle == 0:
                                        b_cycle = 0

                            # sleep(2)
                            if step >= 2:
                                print('step_b///////////', step_b)
                                try:
                                    with open('adjust_screw_config.json', 'r') as f:
                                        config = json.load(f)
                                except:
                                    continue
                                # power 1 :on  0:off
                                power = config['power']
                                auto = config['auto']
                                if power == 1 and auto == 1 and step_b == 0:
                                    x.run(step_add, 1)
                                    sleep(1.5)
                                    y.run(y_step, -1)
                                    sleep(3)
                                    step_b = 1
                                    y_cycle = 1

                                print('step_right///////////', step_right)
                                try:
                                    with open('adjust_screw_config.json', 'r') as f:
                                        config = json.load(f)
                                except:
                                    continue
                                # power 1 :on  0:off
                                power = config['power']
                                auto = config['auto']
                                if power == 1 and auto == 1 and step_b == 1 and step_f == 1:
                                    x.run(x_step, -1)
                                    sleep(2)
                                    step_right += 1
                                    if a_cycle == 3:
                                        a_cycle = 2
                                    elif a_cycle == 2:
                                        a_cycle = 1
                                    if step_right >= 2:
                                        # sleep(2)
                                        try:
                                            with open('adjust_screw_config.json', 'r') as f:
                                                config = json.load(f)
                                        except:
                                            continue
                                        # power 1 :on  0:off
                                        power = config['power']
                                        auto = config['auto']
                                        if power == 1 and auto == 1:
                                            step = 0
                                            step_right = 0

                                            step_f = 0
                                            step_b = 0
                                            f_cycle = 1
                                            b_cycle = 1
                                        else:
                                            print('stand by...11111')
                                else:
                                    print('stand by')

                            else:
                                print('step_f///////////', step_f)
                                try:
                                    with open('adjust_screw_config.json', 'r') as f:
                                        config = json.load(f)
                                except:
                                    continue
                                # power 1 :on  0:off
                                power = config['power']
                                auto = config['auto']
                                if power == 1 and auto == 1 and f_cycle == 1:
                                    x.run(step_add, -1)
                                    sleep(1.5)
                                    y.run(y_step, 1)
                                    sleep(3)
                                    f_cycle = 0
                                    y_cycle = 0

                                print('next...left...')
                                try:
                                    with open('adjust_screw_config.json', 'r') as f:
                                        config = json.load(f)
                                except:
                                    continue
                                # power 1 :on  0:off
                                power = config['power']

                                auto = config['auto']
                                if power == 1 and auto == 1 and f_cycle == 0 and b_cycle == 0:
                                    x.run(x_step, 1)
                                    step += 1
                                    if a_cycle == 1:
                                        a_cycle = 2
                                    elif a_cycle == 2:
                                        a_cycle = 3
                                else:
                                    print('stand byyyy')

                            sleep(0.5)
                    else:
                        print('run time too short!!!')
                        with open('adjust_screw_config.json', 'r') as f:
                            config = json.load(f)
                        config.update({'power': 0})
                        with open('adjust_screw_config.json', 'w') as f:
                            json.dump(config, f)

                # 首次运行
                else:
                    print('initial...start...')
                    z.speed_mode(speed2)
                    if can_motors.weight_z > weight_z:
                        record = Records()
                        record.screw_type = screw_type
                        record.speed = speed1
                        record.direction = 1
                        record.current = can_motors.current if can_motors.current < 10000 else 0
                        record.config_weight = weight
                        record.start_time = get_current_time()
                        while True:
                            can_motors.speed_mode(speed1)

                            if can_motors.weight > weight:
                                z.speed_mode(0)
                                print('can_motors.weight>>>>>>>>>>>>', can_motors.weight)
                                m += 1

                                record.cycle = m
                                record.weight = can_motors.weight
                                record.d_weight = can_motors.weight - weight
                                record.end_time = get_current_time()
                                record.total_time = (record.end_time - record.start_time).total_seconds()
                                record.save()
                                print('record.total_time$$$$$$$$$$$$', record.total_time)

                                if record.d_weight > 3:
                                    print('initial...up...')
                                    while True:
                                        z.speed_mode(-speed2)
                                        if can_motors.up_limit == 1:
                                            z.speed_mode(0)
                                            print('initial...stop...')

                                            with open('adjust_screw_config.json', 'r') as f:
                                                config = json.load(f)
                                            config.update({'power': 0})
                                            with open('adjust_screw_config.json', 'w') as f:
                                                json.dump(config, f)
                                            break
                                    can_motors.weight = 0
                                else:
                                    print('initial...here here...')
                                    sleep(4.5)
                                    # reverse
                                    print('initial...haha...')
                                    can_motors.speed_mode(-speed1)
                                    z.speed_mode(-speed2)

                                    record = Records()
                                    record.screw_type = screw_type
                                    record.cycle = m
                                    record.speed = -speed1
                                    record.direction = -1
                                    record.current = can_motors.current if can_motors.current < 10000 else 0
                                    record.weight = can_motors.weight
                                    record.save()

                                    sleep(record.total_time)
                                    print('initial...gaga...')

                                    can_motors.speed_mode(0)
                                    can_motors.weight = 0
                                    z.speed_mode(-200)
                                    sleep(1.5)
                                    z.speed_mode(0)
                                    can_motors.weight_z = 0

                                    config_data = ScrewConfig()
                                    config_data.n = weight
                                    config_data.power = power
                                    config_data.direction = direction
                                    config_data.speed = speed1
                                    config_data.actual_speed = actual_speed
                                    config_data.cycle = m
                                    config_data.save()

                                    print('initial...end...')
                                    sleep(2)

                                    print('initial...again...')
                                break
            # 手动
            else:
                # 位置1
                if position == 1:
                    print('position...1...')
                    # pre-start
                    r = 0
                    q += 1
                    while True:
                        r += 1
                        can_motors.speed_mode(0)
                        sleep(0.5)

                        if q != 1:
                            break
                        elif r >= 5:
                            break
                    settled_list = Records.objects.filter(screw_type=screw_type, is_settled=True,
                                                          total_time__gt=0).distinct().aggregate(Avg('total_time'))
                    if settled_list['total_time__avg']:
                        avg_time = settled_list['total_time__avg']
                        print('%%%%%%%%%%%%%avg_time', avg_time)
                    else:
                        record_list = Records.objects.filter(direction=1, d_weight__gt=0, total_time__gt=0,
                                                             screw_type=screw_type).distinct().aggregate(
                            Avg('total_time'))
                        print('record_list==========', record_list)
                        avg_time = record_list['total_time__avg'] if record_list['total_time__avg'] else 0.0
                    if avg_time != 0.0:
                        s_time = avg_time - 0.5
                        print('sssssssssss_time', s_time)

                        if s_time > 0:
                            # first stage
                            print('start...')
                            z.speed_mode(speed2)
                            if can_motors.weight_z > weight_z:
                                print('can_motors.weight_z===========', can_motors.weight_z)
                                record = Records()
                                record.screw_type = screw_type
                                record.speed = speed1
                                record.direction = 1
                                record.current = can_motors.current if can_motors.current < 10000 else 0
                                record.config_weight = weight
                                record.start_time = get_current_time()

                                can_motors.speed_mode(speed1)
                                sleep(s_time)

                                z.speed_mode(0)
                                # second stage
                                print('actual_speeddddddddddddddd', actual_speed)
                                while True:
                                    can_motors.speed_mode(actual_speed)
                                    record.actual_speed = actual_speed
                                    if can_motors.weight > weight:
                                        break
                                if can_motors.weight > weight:
                                    print('can_motors.weight2222222222222', can_motors.weight)
                                    m += 1

                                    record.cycle = m
                                    record.weight = can_motors.weight
                                    record.d_weight = can_motors.weight - weight
                                    record.end_time = get_current_time()
                                    record.total_time = (record.end_time - record.start_time).total_seconds()
                                    if record.total_time - avg_time > 0.5:
                                        record.total_time = 0
                                    print('record.total_time&&&&&&&&&&&&&&', record.total_time)

                                    if record.d_weight > 3:
                                        print('cycle...up...')
                                        while True:
                                            z.speed_mode(-speed2)
                                            if can_motors.up_limit == 1:
                                                z.speed_mode(0)
                                                print('cycle...stop...')

                                                with open('adjust_screw_config.json', 'r') as f:
                                                    config = json.load(f)
                                                config.update({'power': 0})
                                                with open('adjust_screw_config.json', 'w') as f:
                                                    json.dump(config, f)
                                                break
                                        record.save()
                                        can_motors.weight = 0

                                    else:

                                        if record.d_weight > d_weight and actual_speed > 5:
                                            actual_speed -= 5
                                        # if record.d_weight < 1:
                                        #     record.is_settled = True
                                        #     print('settled...')
                                        #     actual_speed += 5
                                        else:
                                            record.is_settled = True
                                            print('settled...')
                                        record.save()
                                        can_motors.weight = 0

                                        print('here here...')
                                        sleep(4.5)
                                        # reverse
                                        can_motors.speed_mode(-speed1)
                                        z.speed_mode(-speed2)

                                        record = Records()
                                        record.screw_type = screw_type
                                        record.cycle = m
                                        record.speed = -speed1
                                        record.direction = -1
                                        record.current = can_motors.current if can_motors.current < 10000 else 0
                                        record.weight = can_motors.weight
                                        record.save()

                                        sleep(s_time)
                                        print('gaga')

                                        can_motors.speed_mode(0)
                                        can_motors.weight = 0
                                        z.speed_mode(-200)
                                        sleep(1.5)
                                        z.speed_mode(0)
                                        can_motors.weight_z = 0

                                        config_data = ScrewConfig()
                                        config_data.n = weight
                                        config_data.power = power
                                        config_data.direction = direction
                                        config_data.speed = speed1
                                        config_data.actual_speed = actual_speed
                                        config_data.cycle = m
                                        config_data.save()

                                        print('cycle...end...')
                                        with open('adjust_screw_config.json', 'r') as f:
                                            config = json.load(f)
                                        config.update({'position': 0})
                                        with open('adjust_screw_config.json', 'w') as f:
                                            json.dump(config, f)

                                        sleep(2)
                    # 首次运行
                    else:
                        print('initial...start...')
                        z.speed_mode(speed2)
                        if can_motors.weight_z > weight_z:
                            record = Records()
                            record.screw_type = screw_type
                            record.speed = speed1
                            record.direction = 1
                            record.current = can_motors.current if can_motors.current < 10000 else 0
                            record.config_weight = weight
                            record.start_time = get_current_time()
                            while True:
                                can_motors.speed_mode(speed1)

                                if can_motors.weight > weight:
                                    z.speed_mode(0)
                                    print('can_motors.weight>>>>>>>>>>>>', can_motors.weight)
                                    m += 1

                                    record.cycle = m
                                    record.weight = can_motors.weight
                                    record.d_weight = can_motors.weight - weight
                                    record.end_time = get_current_time()
                                    record.total_time = (
                                                record.end_time - record.start_time).total_seconds()
                                    record.save()
                                    print('record.total_time$$$$$$$$$$$$', record.total_time)

                                    if record.d_weight > 3:
                                        print('initial...up...')
                                        while True:
                                            z.speed_mode(-speed2)
                                            if can_motors.up_limit == 1:
                                                z.speed_mode(0)
                                                print('initial...stop...')

                                                with open('adjust_screw_config.json', 'r') as f:
                                                    config = json.load(f)
                                                config.update({'power': 0})
                                                with open('adjust_screw_config.json', 'w') as f:
                                                    json.dump(config, f)
                                                break
                                        can_motors.weight = 0
                                    else:
                                        print('initial...here here...')
                                        sleep(4.5)
                                        # reverse
                                        print('initial...haha...')
                                        can_motors.speed_mode(-speed1)
                                        z.speed_mode(-speed2)

                                        record = Records()
                                        record.screw_type = screw_type
                                        record.cycle = m
                                        record.speed = -speed1
                                        record.direction = -1
                                        record.current = can_motors.current if can_motors.current < 10000 else 0
                                        record.weight = can_motors.weight
                                        record.save()

                                        sleep(record.total_time)
                                        print('initial...gaga...')

                                        can_motors.speed_mode(0)
                                        can_motors.weight = 0
                                        z.speed_mode(-200)
                                        sleep(1.5)
                                        z.speed_mode(0)
                                        can_motors.weight_z = 0

                                        config_data = ScrewConfig()
                                        config_data.n = weight
                                        config_data.power = power
                                        config_data.direction = direction
                                        config_data.speed = speed1
                                        config_data.actual_speed = actual_speed
                                        config_data.cycle = m
                                        config_data.save()

                                        print('initial...end...')
                                        sleep(2)

                                        print('initial...again...')
                                    break
                            with open('adjust_screw_config.json', 'r') as f:
                                config = json.load(f)
                            config.update({'position': 0})
                            with open('adjust_screw_config.json', 'w') as f:
                                json.dump(config, f)

                # 位置2
                if position == 2:
                    print('position...2...')
                    if has_run == 0:
                        x.run(x_step, 1)
                        has_run = 1
                        sleep(1)
                    # pre-start
                    r = 0
                    q += 1
                    while True:
                        r += 1
                        can_motors.speed_mode(0)
                        sleep(0.5)

                        if q != 1:
                            break
                        elif r >= 5:
                            break
                    settled_list = Records.objects.filter(screw_type=screw_type, is_settled=True,
                                                          total_time__gt=0).distinct().aggregate(Avg('total_time'))
                    if settled_list['total_time__avg']:
                        avg_time = settled_list['total_time__avg']
                        print('%%%%%%%%%%%%%avg_time', avg_time)
                    else:
                        record_list = Records.objects.filter(direction=1, d_weight__gt=0, total_time__gt=0,
                                                             screw_type=screw_type).distinct().aggregate(
                            Avg('total_time'))
                        print('record_list==========', record_list)
                        avg_time = record_list['total_time__avg'] if record_list['total_time__avg'] else 0.0
                    if avg_time != 0.0:
                        s_time = avg_time - 0.5
                        print('sssssssssss_time', s_time)

                        if s_time > 0:
                            # first stage
                            print('start...')
                            z.speed_mode(speed2)
                            if can_motors.weight_z > weight_z:
                                print('can_motors.weight_z===========', can_motors.weight_z)
                                record = Records()
                                record.screw_type = screw_type
                                record.speed = speed1
                                record.direction = 1
                                record.current = can_motors.current if can_motors.current < 10000 else 0
                                record.config_weight = weight
                                record.start_time = get_current_time()

                                can_motors.speed_mode(speed1)
                                sleep(s_time)

                                z.speed_mode(0)
                                # second stage
                                print('actual_speeddddddddddddddd', actual_speed)
                                while True:
                                    can_motors.speed_mode(actual_speed)
                                    record.actual_speed = actual_speed
                                    if can_motors.weight > weight:
                                        break
                                if can_motors.weight > weight:
                                    print('can_motors.weight2222222222222', can_motors.weight)
                                    m += 1

                                    record.cycle = m
                                    record.weight = can_motors.weight
                                    record.d_weight = can_motors.weight - weight
                                    record.end_time = get_current_time()
                                    record.total_time = (record.end_time - record.start_time).total_seconds()
                                    if record.total_time - avg_time > 0.5:
                                        record.total_time = 0
                                    print('record.total_time&&&&&&&&&&&&&&', record.total_time)

                                    a_cycle = 2
                                    if record.d_weight > 3:
                                        print('cycle...up...')
                                        while True:
                                            z.speed_mode(-speed2)
                                            if can_motors.up_limit == 1:
                                                z.speed_mode(0)
                                                # 复位
                                                if a_cycle == 2:
                                                    x.run(x_step, -1)
                                                    a_cycle = 1
                                                    step = 0
                                                print('cycle...stop...')

                                                with open('adjust_screw_config.json', 'r') as f:
                                                    config = json.load(f)
                                                config.update({'power': 0})
                                                with open('adjust_screw_config.json', 'w') as f:
                                                    json.dump(config, f)
                                                break
                                        record.save()
                                        can_motors.weight = 0

                                    else:

                                        if record.d_weight > d_weight and actual_speed > 5:
                                            actual_speed -= 5
                                        # if record.d_weight < 1:
                                        #     record.is_settled = True
                                        #     print('settled...')
                                        #     actual_speed += 5
                                        else:
                                            record.is_settled = True
                                            print('settled...')
                                        record.save()
                                        can_motors.weight = 0

                                        print('here here...')
                                        sleep(4.5)
                                        # reverse
                                        can_motors.speed_mode(-speed1)
                                        z.speed_mode(-speed2)

                                        record = Records()
                                        record.screw_type = screw_type
                                        record.cycle = m
                                        record.speed = -speed1
                                        record.direction = -1
                                        record.current = can_motors.current if can_motors.current < 10000 else 0
                                        record.weight = can_motors.weight
                                        record.save()

                                        sleep(s_time)
                                        print('gaga')

                                        can_motors.speed_mode(0)
                                        can_motors.weight = 0
                                        z.speed_mode(-200)
                                        sleep(1.5)
                                        z.speed_mode(0)
                                        can_motors.weight_z = 0

                                        config_data = ScrewConfig()
                                        config_data.n = weight
                                        config_data.power = power
                                        config_data.direction = direction
                                        config_data.speed = speed1
                                        config_data.actual_speed = actual_speed
                                        config_data.cycle = m
                                        config_data.save()

                                        print('cycle...end...')
                                        with open('adjust_screw_config.json', 'r') as f:
                                            config = json.load(f)
                                        config.update({'position': 0})
                                        with open('adjust_screw_config.json', 'w') as f:
                                            json.dump(config, f)

                                        sleep(2)
                                    if has_run == 1:
                                        x.run(x_step, -1)
                                        has_run = 0
                                        sleep(1)
                                        a_cycle = 1

                    # 首次运行
                    else:
                        print('initial...start...')
                        z.speed_mode(speed2)
                        if can_motors.weight_z > weight_z:
                            record = Records()
                            record.screw_type = screw_type
                            record.speed = speed1
                            record.direction = 1
                            record.current = can_motors.current if can_motors.current < 10000 else 0
                            record.config_weight = weight
                            record.start_time = get_current_time()
                            while True:
                                can_motors.speed_mode(speed1)

                                if can_motors.weight > weight:
                                    z.speed_mode(0)
                                    print('can_motors.weight>>>>>>>>>>>>', can_motors.weight)
                                    m += 1

                                    record.cycle = m
                                    record.weight = can_motors.weight
                                    record.d_weight = can_motors.weight - weight
                                    record.end_time = get_current_time()
                                    record.total_time = (
                                            record.end_time - record.start_time).total_seconds()
                                    record.save()
                                    print('record.total_time$$$$$$$$$$$$', record.total_time)

                                    a_cycle = 2
                                    if record.d_weight > 3:
                                        print('initial...up...')
                                        while True:
                                            z.speed_mode(-speed2)
                                            if can_motors.up_limit == 1:
                                                z.speed_mode(0)
                                                # 复位
                                                if a_cycle == 2:
                                                    x.run(x_step, -1)
                                                    a_cycle = 1
                                                    step = 0
                                                print('initial...stop...')

                                                with open('adjust_screw_config.json', 'r') as f:
                                                    config = json.load(f)
                                                config.update({'power': 0})
                                                with open('adjust_screw_config.json', 'w') as f:
                                                    json.dump(config, f)
                                                break
                                        can_motors.weight = 0
                                    else:
                                        print('initial...here here...')
                                        sleep(4.5)
                                        # reverse
                                        print('initial...haha...')
                                        can_motors.speed_mode(-speed1)
                                        z.speed_mode(-speed2)

                                        record = Records()
                                        record.screw_type = screw_type
                                        record.cycle = m
                                        record.speed = -speed1
                                        record.direction = -1
                                        record.current = can_motors.current if can_motors.current < 10000 else 0
                                        record.weight = can_motors.weight
                                        record.save()

                                        sleep(record.total_time)
                                        print('initial...gaga...')

                                        can_motors.speed_mode(0)
                                        can_motors.weight = 0
                                        z.speed_mode(-200)
                                        sleep(1.5)
                                        z.speed_mode(0)
                                        can_motors.weight_z = 0

                                        config_data = ScrewConfig()
                                        config_data.n = weight
                                        config_data.power = power
                                        config_data.direction = direction
                                        config_data.speed = speed1
                                        config_data.actual_speed = actual_speed
                                        config_data.cycle = m
                                        config_data.save()

                                        print('initial...end...')
                                        sleep(2)

                                        print('initial...again...')
                                    break
                            if has_run == 1:
                                x.run(x_step, -1)
                                has_run = 0
                                sleep(1)
                                a_cycle = 1
                            with open('adjust_screw_config.json', 'r') as f:
                                config = json.load(f)
                            config.update({'position': 0})
                            with open('adjust_screw_config.json', 'w') as f:
                                json.dump(config, f)

                # 位置3
                if position == 3:
                    print('position...3...')
                    if has_run == 0:
                        x.run(x_step * 2, 1)
                        has_run = 1
                        sleep(1)
                    # pre-start
                    r = 0
                    q += 1
                    while True:
                        r += 1
                        can_motors.speed_mode(0)
                        sleep(0.5)

                        if q != 1:
                            break
                        elif r >= 5:
                            break
                    settled_list = Records.objects.filter(screw_type=screw_type, is_settled=True,
                                                          total_time__gt=0).distinct().aggregate(Avg('total_time'))
                    if settled_list['total_time__avg']:
                        avg_time = settled_list['total_time__avg']
                        print('%%%%%%%%%%%%%avg_time', avg_time)
                    else:
                        record_list = Records.objects.filter(direction=1, d_weight__gt=0, total_time__gt=0,
                                                             screw_type=screw_type).distinct().aggregate(
                            Avg('total_time'))
                        print('record_list==========', record_list)
                        avg_time = record_list['total_time__avg'] if record_list['total_time__avg'] else 0.0
                    if avg_time != 0.0:
                        s_time = avg_time - 0.5
                        print('sssssssssss_time', s_time)

                        if s_time > 0:
                            # first stage
                            print('start...')
                            z.speed_mode(speed2)
                            if can_motors.weight_z > weight_z:
                                print('can_motors.weight_z===========', can_motors.weight_z)
                                record = Records()
                                record.screw_type = screw_type
                                record.speed = speed1
                                record.direction = 1
                                record.current = can_motors.current if can_motors.current < 10000 else 0
                                record.config_weight = weight
                                record.start_time = get_current_time()

                                can_motors.speed_mode(speed1)
                                sleep(s_time)

                                z.speed_mode(0)
                                # second stage
                                print('actual_speeddddddddddddddd', actual_speed)
                                while True:
                                    can_motors.speed_mode(actual_speed)
                                    record.actual_speed = actual_speed
                                    if can_motors.weight > weight:
                                        break
                                if can_motors.weight > weight:
                                    print('can_motors.weight2222222222222', can_motors.weight)
                                    m += 1

                                    record.cycle = m
                                    record.weight = can_motors.weight
                                    record.d_weight = can_motors.weight - weight
                                    record.end_time = get_current_time()
                                    record.total_time = (record.end_time - record.start_time).total_seconds()
                                    if record.total_time - avg_time > 0.5:
                                        record.total_time = 0
                                    print('record.total_time&&&&&&&&&&&&&&', record.total_time)

                                    a_cycle = 3
                                    if record.d_weight > 3:
                                        print('cycle...up...')
                                        while True:
                                            z.speed_mode(-speed2)
                                            if can_motors.up_limit == 1:
                                                z.speed_mode(0)
                                                # 复位
                                                if a_cycle == 3:
                                                    x.run(x_step * 2, -1)
                                                    a_cycle = 1
                                                    step = 0
                                                print('cycle...stop...')

                                                with open('adjust_screw_config.json', 'r') as f:
                                                    config = json.load(f)
                                                config.update({'power': 0})
                                                with open('adjust_screw_config.json', 'w') as f:
                                                    json.dump(config, f)
                                                break
                                        record.save()
                                        can_motors.weight = 0

                                    else:

                                        if record.d_weight > d_weight and actual_speed > 5:
                                            actual_speed -= 5
                                        # if record.d_weight < 1:
                                        #     record.is_settled = True
                                        #     print('settled...')
                                        #     actual_speed += 5
                                        else:
                                            record.is_settled = True
                                            print('settled...')
                                        record.save()
                                        can_motors.weight = 0

                                        print('here here...')
                                        sleep(4.5)
                                        # reverse
                                        can_motors.speed_mode(-speed1)
                                        z.speed_mode(-speed2)

                                        record = Records()
                                        record.screw_type = screw_type
                                        record.cycle = m
                                        record.speed = -speed1
                                        record.direction = -1
                                        record.current = can_motors.current if can_motors.current < 10000 else 0
                                        record.weight = can_motors.weight
                                        record.save()

                                        sleep(s_time)
                                        print('gaga')

                                        can_motors.speed_mode(0)
                                        can_motors.weight = 0
                                        z.speed_mode(-200)
                                        sleep(1.5)
                                        z.speed_mode(0)
                                        can_motors.weight_z = 0

                                        config_data = ScrewConfig()
                                        config_data.n = weight
                                        config_data.power = power
                                        config_data.direction = direction
                                        config_data.speed = speed1
                                        config_data.actual_speed = actual_speed
                                        config_data.cycle = m
                                        config_data.save()

                                        print('cycle...end...')
                                        with open('adjust_screw_config.json', 'r') as f:
                                            config = json.load(f)
                                        config.update({'position': 0})
                                        with open('adjust_screw_config.json', 'w') as f:
                                            json.dump(config, f)

                                        sleep(2)
                                    if has_run == 1:
                                        x.run(x_step * 2, -1)
                                        has_run = 0
                                        sleep(1)
                                        a_cycle = 1
                    # 首次运行
                    else:
                        print('initial...start...')
                        z.speed_mode(speed2)
                        if can_motors.weight_z > weight_z:
                            record = Records()
                            record.screw_type = screw_type
                            record.speed = speed1
                            record.direction = 1
                            record.current = can_motors.current if can_motors.current < 10000 else 0
                            record.config_weight = weight
                            record.start_time = get_current_time()
                            while True:
                                can_motors.speed_mode(speed1)

                                if can_motors.weight > weight:
                                    z.speed_mode(0)
                                    print('can_motors.weight>>>>>>>>>>>>', can_motors.weight)
                                    m += 1

                                    record.cycle = m
                                    record.weight = can_motors.weight
                                    record.d_weight = can_motors.weight - weight
                                    record.end_time = get_current_time()
                                    record.total_time = (
                                            record.end_time - record.start_time).total_seconds()
                                    record.save()
                                    print('record.total_time$$$$$$$$$$$$', record.total_time)

                                    a_cycle = 3
                                    if record.d_weight > 3:
                                        print('initial...up...')
                                        while True:
                                            z.speed_mode(-speed2)
                                            if can_motors.up_limit == 1:
                                                z.speed_mode(0)
                                                # 复位
                                                if a_cycle == 3:
                                                    x.run(x_step * 2, -1)
                                                    a_cycle = 1
                                                    step = 0
                                                print('initial...stop...')

                                                with open('adjust_screw_config.json', 'r') as f:
                                                    config = json.load(f)
                                                config.update({'power': 0})
                                                with open('adjust_screw_config.json', 'w') as f:
                                                    json.dump(config, f)
                                                break
                                        can_motors.weight = 0
                                    else:
                                        print('initial...here here...')
                                        sleep(4.5)
                                        # reverse
                                        print('initial...haha...')
                                        can_motors.speed_mode(-speed1)
                                        z.speed_mode(-speed2)

                                        record = Records()
                                        record.screw_type = screw_type
                                        record.cycle = m
                                        record.speed = -speed1
                                        record.direction = -1
                                        record.current = can_motors.current if can_motors.current < 10000 else 0
                                        record.weight = can_motors.weight
                                        record.save()

                                        sleep(record.total_time)
                                        print('initial...gaga...')

                                        can_motors.speed_mode(0)
                                        can_motors.weight = 0
                                        z.speed_mode(-200)
                                        sleep(1.5)
                                        z.speed_mode(0)
                                        can_motors.weight_z = 0

                                        config_data = ScrewConfig()
                                        config_data.n = weight
                                        config_data.power = power
                                        config_data.direction = direction
                                        config_data.speed = speed1
                                        config_data.actual_speed = actual_speed
                                        config_data.cycle = m
                                        config_data.save()

                                        print('initial...end...')
                                        sleep(2)

                                        print('initial...again...')
                                    break
                            if has_run == 1:
                                x.run(x_step * 2, -1)
                                has_run = 0
                                sleep(1)
                                a_cycle = 1
                            with open('adjust_screw_config.json', 'r') as f:
                                config = json.load(f)
                            config.update({'position': 0})
                            with open('adjust_screw_config.json', 'w') as f:
                                json.dump(config, f)

                y.run(y_step, -1)
                sleep(3)
                x.run(x_step, 1)
                has_run = 1
                sleep(1)

                # 位置4
                if position == 4:
                    if y_position == 0:
                        y.run(y_step, -1)
                        sleep(3)
                        y_position = 1
                    print('position...4...')
                    if has_run == 0:
                        x.run(x_step * 2 + step_add, 1)
                        has_run = 1
                        sleep(1)
                    # pre-start
                    r = 0
                    q += 1
                    while True:
                        r += 1
                        can_motors.speed_mode(0)
                        sleep(0.5)

                        if q != 1:
                            break
                        elif r >= 5:
                            break
                    settled_list = Records.objects.filter(screw_type=screw_type, is_settled=True,
                                                          total_time__gt=0).distinct().aggregate(Avg('total_time'))
                    if settled_list['total_time__avg']:
                        avg_time = settled_list['total_time__avg']
                        print('%%%%%%%%%%%%%avg_time', avg_time)
                    else:
                        record_list = Records.objects.filter(direction=1, d_weight__gt=0, total_time__gt=0,
                                                             screw_type=screw_type).distinct().aggregate(
                            Avg('total_time'))
                        print('record_list==========', record_list)
                        avg_time = record_list['total_time__avg'] if record_list['total_time__avg'] else 0.0
                    if avg_time != 0.0:
                        s_time = avg_time - 0.5
                        print('sssssssssss_time', s_time)

                        if s_time > 0:
                            # first stage
                            print('start...')
                            z.speed_mode(speed2)
                            if can_motors.weight_z > weight_z:
                                print('can_motors.weight_z===========', can_motors.weight_z)
                                record = Records()
                                record.screw_type = screw_type
                                record.speed = speed1
                                record.direction = 1
                                record.current = can_motors.current if can_motors.current < 10000 else 0
                                record.config_weight = weight
                                record.start_time = get_current_time()

                                can_motors.speed_mode(speed1)
                                sleep(s_time)

                                z.speed_mode(0)
                                # second stage
                                print('actual_speeddddddddddddddd', actual_speed)
                                while True:
                                    can_motors.speed_mode(actual_speed)
                                    record.actual_speed = actual_speed
                                    if can_motors.weight > weight:
                                        break
                                if can_motors.weight > weight:
                                    print('can_motors.weight2222222222222', can_motors.weight)
                                    m += 1

                                    record.cycle = m
                                    record.weight = can_motors.weight
                                    record.d_weight = can_motors.weight - weight
                                    record.end_time = get_current_time()
                                    record.total_time = (
                                                record.end_time - record.start_time).total_seconds()
                                    if record.total_time - avg_time > 0.5:
                                        record.total_time = 0
                                    print('record.total_time&&&&&&&&&&&&&&', record.total_time)

                                    y_cycle = 1
                                    a_cycle = 3
                                    if record.d_weight > 3:
                                        print('cycle...up...')
                                        while True:
                                            z.speed_mode(-speed2)
                                            if can_motors.up_limit == 1:
                                                z.speed_mode(0)
                                                # 复位
                                                if y_cycle == 1:
                                                    y.run(y_step, 1)
                                                    # sleep(3)
                                                    y_cycle = 0
                                                    if a_cycle == 2:
                                                        x.run(x_step + step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 3:
                                                        x.run(x_step * 2 + step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 1:
                                                        x.run(step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                else:
                                                    if a_cycle == 2:
                                                        x.run(x_step, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 3:
                                                        x.run(x_step * 2, -1)
                                                        a_cycle = 1
                                                        step = 0

                                                print('cycle...stop...')

                                                with open('adjust_screw_config.json', 'r') as f:
                                                    config = json.load(f)
                                                config.update({'power': 0})
                                                with open('adjust_screw_config.json', 'w') as f:
                                                    json.dump(config, f)
                                                break
                                        record.save()
                                        can_motors.weight = 0

                                    else:

                                        if record.d_weight > d_weight and actual_speed > 5:
                                            actual_speed -= 5
                                        # if record.d_weight < 1:
                                        #     record.is_settled = True
                                        #     print('settled...')
                                        #     actual_speed += 5
                                        else:
                                            record.is_settled = True
                                            print('settled...')
                                        record.save()
                                        can_motors.weight = 0

                                        print('here here...')
                                        sleep(4.5)
                                        # reverse
                                        can_motors.speed_mode(-speed1)
                                        z.speed_mode(-speed2)

                                        record = Records()
                                        record.screw_type = screw_type
                                        record.cycle = m
                                        record.speed = -speed1
                                        record.direction = -1
                                        record.current = can_motors.current if can_motors.current < 10000 else 0
                                        record.weight = can_motors.weight
                                        record.save()

                                        sleep(s_time)
                                        print('gaga')

                                        can_motors.speed_mode(0)
                                        can_motors.weight = 0
                                        z.speed_mode(-200)
                                        sleep(1.5)
                                        z.speed_mode(0)
                                        can_motors.weight_z = 0

                                        config_data = ScrewConfig()
                                        config_data.n = weight
                                        config_data.power = power
                                        config_data.direction = direction
                                        config_data.speed = speed1
                                        config_data.actual_speed = actual_speed
                                        config_data.cycle = m
                                        config_data.save()

                                        print('cycle...end...')
                                        with open('adjust_screw_config.json', 'r') as f:
                                            config = json.load(f)
                                        config.update({'position': 0})
                                        with open('adjust_screw_config.json', 'w') as f:
                                            json.dump(config, f)

                                        sleep(2)
                                    if has_run == 1:
                                        x.run(x_step * 2 + step_add, -1)
                                        has_run = 0
                                        sleep(1)
                                        a_cycle = 1
                                    if y_position == 1:
                                        y.run(y_step, 1)
                                        sleep(3)
                                        y_position = 0
                                        y_cycle = 0
                    # 首次运行
                    else:
                        print('initial...start...')
                        z.speed_mode(speed2)
                        if can_motors.weight_z > weight_z:
                            record = Records()
                            record.screw_type = screw_type
                            record.speed = speed1
                            record.direction = 1
                            record.current = can_motors.current if can_motors.current < 10000 else 0
                            record.config_weight = weight
                            record.start_time = get_current_time()
                            while True:
                                can_motors.speed_mode(speed1)

                                if can_motors.weight > weight:
                                    z.speed_mode(0)
                                    print('can_motors.weight>>>>>>>>>>>>', can_motors.weight)
                                    m += 1

                                    record.cycle = m
                                    record.weight = can_motors.weight
                                    record.d_weight = can_motors.weight - weight
                                    record.end_time = get_current_time()
                                    record.total_time = (
                                            record.end_time - record.start_time).total_seconds()
                                    record.save()
                                    print('record.total_time$$$$$$$$$$$$', record.total_time)

                                    y_cycle = 1
                                    a_cycle = 3
                                    if record.d_weight > 3:
                                        print('initial...up...')
                                        while True:
                                            z.speed_mode(-speed2)
                                            if can_motors.up_limit == 1:
                                                z.speed_mode(0)
                                                # 复位
                                                if y_cycle == 1:
                                                    y.run(y_step, 1)
                                                    # sleep(3)
                                                    y_cycle = 0
                                                    if a_cycle == 2:
                                                        x.run(x_step + step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 3:
                                                        x.run(x_step * 2 + step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 1:
                                                        x.run(step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                else:
                                                    if a_cycle == 2:
                                                        x.run(x_step, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 3:
                                                        x.run(x_step * 2, -1)
                                                        a_cycle = 1
                                                        step = 0

                                                print('initial...stop...')

                                                with open('adjust_screw_config.json', 'r') as f:
                                                    config = json.load(f)
                                                config.update({'power': 0})
                                                with open('adjust_screw_config.json', 'w') as f:
                                                    json.dump(config, f)
                                                break
                                        can_motors.weight = 0
                                    else:
                                        print('initial...here here...')
                                        sleep(4.5)
                                        # reverse
                                        print('initial...haha...')
                                        can_motors.speed_mode(-speed1)
                                        z.speed_mode(-speed2)

                                        record = Records()
                                        record.screw_type = screw_type
                                        record.cycle = m
                                        record.speed = -speed1
                                        record.direction = -1
                                        record.current = can_motors.current if can_motors.current < 10000 else 0
                                        record.weight = can_motors.weight
                                        record.save()

                                        sleep(record.total_time)
                                        print('initial...gaga...')

                                        can_motors.speed_mode(0)
                                        can_motors.weight = 0
                                        z.speed_mode(-200)
                                        sleep(1.5)
                                        z.speed_mode(0)
                                        can_motors.weight_z = 0

                                        config_data = ScrewConfig()
                                        config_data.n = weight
                                        config_data.power = power
                                        config_data.direction = direction
                                        config_data.speed = speed1
                                        config_data.actual_speed = actual_speed
                                        config_data.cycle = m
                                        config_data.save()

                                        print('initial...end...')
                                        sleep(2)

                                        print('initial...again...')
                                    break
                            if has_run == 1:
                                x.run(x_step * 2 + step_add, -1)
                                has_run = 0
                                sleep(1)
                                a_cycle = 1
                            if y_position == 1:
                                y.run(y_step, 1)
                                sleep(3)
                                y_position = 0
                                y_cycle = 0
                            with open('adjust_screw_config.json', 'r') as f:
                                config = json.load(f)
                            config.update({'position': 0})
                            with open('adjust_screw_config.json', 'w') as f:
                                json.dump(config, f)

                # 位置5
                if position == 5:
                    if y_position == 0:
                        y.run(y_step, -1)
                        sleep(3)
                        y_position = 1
                    print('position...5...')
                    if has_run == 0:
                        x.run(x_step + step_add, 1)
                        has_run = 1
                        sleep(1)
                    # pre-start
                    r = 0
                    q += 1
                    while True:
                        r += 1
                        can_motors.speed_mode(0)
                        sleep(0.5)

                        if q != 1:
                            break
                        elif r >= 5:
                            break
                    settled_list = Records.objects.filter(screw_type=screw_type, is_settled=True,
                                                          total_time__gt=0).distinct().aggregate(Avg('total_time'))
                    if settled_list['total_time__avg']:
                        avg_time = settled_list['total_time__avg']
                        print('%%%%%%%%%%%%%avg_time', avg_time)
                    else:
                        record_list = Records.objects.filter(direction=1, d_weight__gt=0, total_time__gt=0,
                                                             screw_type=screw_type).distinct().aggregate(
                            Avg('total_time'))
                        print('record_list==========', record_list)
                        avg_time = record_list['total_time__avg'] if record_list['total_time__avg'] else 0.0
                    if avg_time != 0.0:
                        s_time = avg_time - 0.5
                        print('sssssssssss_time', s_time)

                        if s_time > 0:
                            # first stage
                            print('start...')
                            z.speed_mode(speed2)
                            if can_motors.weight_z > weight_z:
                                print('can_motors.weight_z===========', can_motors.weight_z)
                                record = Records()
                                record.screw_type = screw_type
                                record.speed = speed1
                                record.direction = 1
                                record.current = can_motors.current if can_motors.current < 10000 else 0
                                record.config_weight = weight
                                record.start_time = get_current_time()

                                can_motors.speed_mode(speed1)
                                sleep(s_time)

                                z.speed_mode(0)
                                # second stage
                                print('actual_speeddddddddddddddd', actual_speed)
                                while True:
                                    can_motors.speed_mode(actual_speed)
                                    record.actual_speed = actual_speed
                                    if can_motors.weight > weight:
                                        break
                                if can_motors.weight > weight:
                                    print('can_motors.weight2222222222222', can_motors.weight)
                                    m += 1

                                    record.cycle = m
                                    record.weight = can_motors.weight
                                    record.d_weight = can_motors.weight - weight
                                    record.end_time = get_current_time()
                                    record.total_time = (
                                                record.end_time - record.start_time).total_seconds()
                                    if record.total_time - avg_time > 0.5:
                                        record.total_time = 0
                                    print('record.total_time&&&&&&&&&&&&&&', record.total_time)

                                    y_cycle = 1
                                    a_cycle = 2
                                    if record.d_weight > 3:
                                        print('cycle...up...')
                                        while True:
                                            z.speed_mode(-speed2)
                                            if can_motors.up_limit == 1:
                                                z.speed_mode(0)
                                                # 复位
                                                if y_cycle == 1:
                                                    y.run(y_step, 1)
                                                    # sleep(3)
                                                    y_cycle = 0
                                                    if a_cycle == 2:
                                                        x.run(x_step + step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 3:
                                                        x.run(x_step * 2 + step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 1:
                                                        x.run(step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                else:
                                                    if a_cycle == 2:
                                                        x.run(x_step, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 3:
                                                        x.run(x_step * 2, -1)
                                                        a_cycle = 1
                                                        step = 0

                                                print('cycle...stop...')

                                                with open('adjust_screw_config.json', 'r') as f:
                                                    config = json.load(f)
                                                config.update({'power': 0})
                                                with open('adjust_screw_config.json', 'w') as f:
                                                    json.dump(config, f)
                                                break
                                        record.save()
                                        can_motors.weight = 0

                                    else:

                                        if record.d_weight > d_weight and actual_speed > 5:
                                            actual_speed -= 5
                                        # if record.d_weight < 1:
                                        #     record.is_settled = True
                                        #     print('settled...')
                                        #     actual_speed += 5
                                        else:
                                            record.is_settled = True
                                            print('settled...')
                                        record.save()
                                        can_motors.weight = 0

                                        print('here here...')
                                        sleep(4.5)
                                        # reverse
                                        can_motors.speed_mode(-speed1)
                                        z.speed_mode(-speed2)

                                        record = Records()
                                        record.screw_type = screw_type
                                        record.cycle = m
                                        record.speed = -speed1
                                        record.direction = -1
                                        record.current = can_motors.current if can_motors.current < 10000 else 0
                                        record.weight = can_motors.weight
                                        record.save()

                                        sleep(s_time)
                                        print('gaga')

                                        can_motors.speed_mode(0)
                                        can_motors.weight = 0
                                        z.speed_mode(-200)
                                        sleep(1.5)
                                        z.speed_mode(0)
                                        can_motors.weight_z = 0

                                        config_data = ScrewConfig()
                                        config_data.n = weight
                                        config_data.power = power
                                        config_data.direction = direction
                                        config_data.speed = speed1
                                        config_data.actual_speed = actual_speed
                                        config_data.cycle = m
                                        config_data.save()

                                        print('cycle...end...')
                                        with open('adjust_screw_config.json', 'r') as f:
                                            config = json.load(f)
                                        config.update({'position': 0})
                                        with open('adjust_screw_config.json', 'w') as f:
                                            json.dump(config, f)

                                        sleep(2)
                                    if has_run == 1:
                                        x.run(x_step + step_add, -1)
                                        has_run = 0
                                        sleep(1)
                                        a_cycle = 1
                                    if y_position == 1:
                                        y.run(y_step, 1)
                                        sleep(3)
                                        y_position = 0
                                        y_cycle = 0
                    # 首次运行
                    else:
                        print('initial...start...')
                        z.speed_mode(speed2)
                        if can_motors.weight_z > weight_z:
                            record = Records()
                            record.screw_type = screw_type
                            record.speed = speed1
                            record.direction = 1
                            record.current = can_motors.current if can_motors.current < 10000 else 0
                            record.config_weight = weight
                            record.start_time = get_current_time()
                            while True:
                                can_motors.speed_mode(speed1)

                                if can_motors.weight > weight:
                                    z.speed_mode(0)
                                    print('can_motors.weight>>>>>>>>>>>>', can_motors.weight)
                                    m += 1

                                    record.cycle = m
                                    record.weight = can_motors.weight
                                    record.d_weight = can_motors.weight - weight
                                    record.end_time = get_current_time()
                                    record.total_time = (
                                            record.end_time - record.start_time).total_seconds()
                                    record.save()
                                    print('record.total_time$$$$$$$$$$$$', record.total_time)

                                    y_cycle = 1
                                    a_cycle = 2
                                    if record.d_weight > 3:
                                        print('initial...up...')
                                        while True:
                                            z.speed_mode(-speed2)
                                            if can_motors.up_limit == 1:
                                                z.speed_mode(0)
                                                # 复位
                                                if y_cycle == 1:
                                                    y.run(y_step, 1)
                                                    # sleep(3)
                                                    y_cycle = 0
                                                    if a_cycle == 2:
                                                        x.run(x_step + step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 3:
                                                        x.run(x_step * 2 + step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 1:
                                                        x.run(step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                else:
                                                    if a_cycle == 2:
                                                        x.run(x_step, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 3:
                                                        x.run(x_step * 2, -1)
                                                        a_cycle = 1
                                                        step = 0

                                                print('initial...stop...')

                                                with open('adjust_screw_config.json', 'r') as f:
                                                    config = json.load(f)
                                                config.update({'power': 0})
                                                with open('adjust_screw_config.json', 'w') as f:
                                                    json.dump(config, f)
                                                break
                                        can_motors.weight = 0
                                    else:
                                        print('initial...here here...')
                                        sleep(4.5)
                                        # reverse
                                        print('initial...haha...')
                                        can_motors.speed_mode(-speed1)
                                        z.speed_mode(-speed2)

                                        record = Records()
                                        record.screw_type = screw_type
                                        record.cycle = m
                                        record.speed = -speed1
                                        record.direction = -1
                                        record.current = can_motors.current if can_motors.current < 10000 else 0
                                        record.weight = can_motors.weight
                                        record.save()

                                        sleep(record.total_time)
                                        print('initial...gaga...')

                                        can_motors.speed_mode(0)
                                        can_motors.weight = 0
                                        z.speed_mode(-200)
                                        sleep(1.5)
                                        z.speed_mode(0)
                                        can_motors.weight_z = 0

                                        config_data = ScrewConfig()
                                        config_data.n = weight
                                        config_data.power = power
                                        config_data.direction = direction
                                        config_data.speed = speed1
                                        config_data.actual_speed = actual_speed
                                        config_data.cycle = m
                                        config_data.save()

                                        print('initial...end...')
                                        sleep(2)

                                        print('initial...again...')
                                    break
                            if has_run == 1:
                                x.run(x_step + step_add, -1)
                                has_run = 0
                                sleep(1)
                                a_cycle = 1
                            if y_position == 1:
                                y.run(y_step, 1)
                                sleep(3)
                                y_position = 0
                                y_cycle = 0
                            with open('adjust_screw_config.json', 'r') as f:
                                config = json.load(f)
                            config.update({'position': 0})
                            with open('adjust_screw_config.json', 'w') as f:
                                json.dump(config, f)

                # 位置6
                if position == 6:
                    if y_position == 0:
                        y.run(y_step, -1)
                        sleep(3)
                        y_position = 1
                    print('position...6...')
                    if has_run == 0:
                        x.run(step_add, 1)
                        has_run = 1
                        sleep(1)
                    # pre-start
                    r = 0
                    q += 1
                    while True:
                        r += 1
                        can_motors.speed_mode(0)
                        sleep(0.5)

                        if q != 1:
                            break
                        elif r >= 5:
                            break
                    settled_list = Records.objects.filter(screw_type=screw_type, is_settled=True,
                                                          total_time__gt=0).distinct().aggregate(Avg('total_time'))
                    if settled_list['total_time__avg']:
                        avg_time = settled_list['total_time__avg']
                        print('%%%%%%%%%%%%%avg_time', avg_time)
                    else:
                        record_list = Records.objects.filter(direction=1, d_weight__gt=0, total_time__gt=0,
                                                             screw_type=screw_type).distinct().aggregate(
                            Avg('total_time'))
                        print('record_list==========', record_list)
                        avg_time = record_list['total_time__avg'] if record_list['total_time__avg'] else 0.0
                    if avg_time != 0.0:
                        s_time = avg_time - 0.5
                        print('sssssssssss_time', s_time)

                        if s_time > 0:
                            # first stage
                            print('start...')
                            z.speed_mode(speed2)
                            if can_motors.weight_z > weight_z:
                                print('can_motors.weight_z===========', can_motors.weight_z)
                                record = Records()
                                record.screw_type = screw_type
                                record.speed = speed1
                                record.direction = 1
                                record.current = can_motors.current if can_motors.current < 10000 else 0
                                record.config_weight = weight
                                record.start_time = get_current_time()

                                can_motors.speed_mode(speed1)
                                sleep(s_time)

                                z.speed_mode(0)
                                # second stage
                                print('actual_speeddddddddddddddd', actual_speed)
                                while True:
                                    can_motors.speed_mode(actual_speed)
                                    record.actual_speed = actual_speed
                                    if can_motors.weight > weight:
                                        break
                                if can_motors.weight > weight:
                                    print('can_motors.weight2222222222222', can_motors.weight)
                                    m += 1

                                    record.cycle = m
                                    record.weight = can_motors.weight
                                    record.d_weight = can_motors.weight - weight
                                    record.end_time = get_current_time()
                                    record.total_time = (
                                                record.end_time - record.start_time).total_seconds()
                                    if record.total_time - avg_time > 0.5:
                                        record.total_time = 0
                                    print('record.total_time&&&&&&&&&&&&&&', record.total_time)

                                    y_cycle = 1
                                    a_cycle = 1
                                    if record.d_weight > 3:
                                        print('cycle...up...')
                                        while True:
                                            z.speed_mode(-speed2)
                                            if can_motors.up_limit == 1:
                                                z.speed_mode(0)
                                                # 复位
                                                if y_cycle == 1:
                                                    y.run(y_step, 1)
                                                    # sleep(3)
                                                    y_cycle = 0
                                                    if a_cycle == 2:
                                                        x.run(x_step + step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 3:
                                                        x.run(x_step * 2 + step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 1:
                                                        x.run(step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                else:
                                                    if a_cycle == 2:
                                                        x.run(x_step, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 3:
                                                        x.run(x_step * 2, -1)
                                                        a_cycle = 1
                                                        step = 0

                                                print('cycle...stop...')

                                                with open('adjust_screw_config.json', 'r') as f:
                                                    config = json.load(f)
                                                config.update({'power': 0})
                                                with open('adjust_screw_config.json', 'w') as f:
                                                    json.dump(config, f)
                                                break
                                        record.save()
                                        can_motors.weight = 0

                                    else:

                                        if record.d_weight > d_weight and actual_speed > 5:
                                            actual_speed -= 5
                                        # if record.d_weight < 1:
                                        #     record.is_settled = True
                                        #     print('settled...')
                                        #     actual_speed += 5
                                        else:
                                            record.is_settled = True
                                            print('settled...')
                                        record.save()
                                        can_motors.weight = 0

                                        print('here here...')
                                        sleep(4.5)
                                        # reverse
                                        can_motors.speed_mode(-speed1)
                                        z.speed_mode(-speed2)

                                        record = Records()
                                        record.screw_type = screw_type
                                        record.cycle = m
                                        record.speed = -speed1
                                        record.direction = -1
                                        record.current = can_motors.current if can_motors.current < 10000 else 0
                                        record.weight = can_motors.weight
                                        record.save()

                                        sleep(s_time)
                                        print('gaga')

                                        can_motors.speed_mode(0)
                                        can_motors.weight = 0
                                        z.speed_mode(-200)
                                        sleep(1.5)
                                        z.speed_mode(0)
                                        can_motors.weight_z = 0

                                        config_data = ScrewConfig()
                                        config_data.n = weight
                                        config_data.power = power
                                        config_data.direction = direction
                                        config_data.speed = speed1
                                        config_data.actual_speed = actual_speed
                                        config_data.cycle = m
                                        config_data.save()

                                        print('cycle...end...')
                                        with open('adjust_screw_config.json', 'r') as f:
                                            config = json.load(f)
                                        config.update({'position': 0})
                                        with open('adjust_screw_config.json', 'w') as f:
                                            json.dump(config, f)

                                        sleep(2)
                                    if has_run == 1:
                                        x.run(step_add, -1)
                                        has_run = 0
                                        sleep(1)
                                        a_cycle = 1
                                    if y_position == 1:
                                        y.run(y_step, 1)
                                        sleep(3)
                                        y_position = 0
                                        y_cycle = 0
                    # 首次运行
                    else:
                        print('initial...start...')
                        z.speed_mode(speed2)
                        if can_motors.weight_z > weight_z:
                            record = Records()
                            record.screw_type = screw_type
                            record.speed = speed1
                            record.direction = 1
                            record.current = can_motors.current if can_motors.current < 10000 else 0
                            record.config_weight = weight
                            record.start_time = get_current_time()
                            while True:
                                can_motors.speed_mode(speed1)

                                if can_motors.weight > weight:
                                    z.speed_mode(0)
                                    print('can_motors.weight>>>>>>>>>>>>', can_motors.weight)
                                    m += 1

                                    record.cycle = m
                                    record.weight = can_motors.weight
                                    record.d_weight = can_motors.weight - weight
                                    record.end_time = get_current_time()
                                    record.total_time = (
                                            record.end_time - record.start_time).total_seconds()
                                    record.save()
                                    print('record.total_time$$$$$$$$$$$$', record.total_time)

                                    y_cycle = 1
                                    a_cycle = 1
                                    if record.d_weight > 3:
                                        print('initial...up...')
                                        while True:
                                            z.speed_mode(-speed2)
                                            if can_motors.up_limit == 1:
                                                z.speed_mode(0)
                                                # 复位
                                                if y_cycle == 1:
                                                    y.run(y_step, 1)
                                                    # sleep(3)
                                                    y_cycle = 0
                                                    if a_cycle == 2:
                                                        x.run(x_step + step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 3:
                                                        x.run(x_step * 2 + step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 1:
                                                        x.run(step_add, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                else:
                                                    if a_cycle == 2:
                                                        x.run(x_step, -1)
                                                        a_cycle = 1
                                                        step = 0
                                                    elif a_cycle == 3:
                                                        x.run(x_step * 2, -1)
                                                        a_cycle = 1
                                                        step = 0

                                                print('initial...stop...')

                                                with open('adjust_screw_config.json', 'r') as f:
                                                    config = json.load(f)
                                                config.update({'power': 0})
                                                with open('adjust_screw_config.json', 'w') as f:
                                                    json.dump(config, f)
                                                break
                                        can_motors.weight = 0
                                    else:
                                        print('initial...here here...')
                                        sleep(4.5)
                                        # reverse
                                        print('initial...haha...')
                                        can_motors.speed_mode(-speed1)
                                        z.speed_mode(-speed2)

                                        record = Records()
                                        record.screw_type = screw_type
                                        record.cycle = m
                                        record.speed = -speed1
                                        record.direction = -1
                                        record.current = can_motors.current if can_motors.current < 10000 else 0
                                        record.weight = can_motors.weight
                                        record.save()

                                        sleep(record.total_time)
                                        print('initial...gaga...')

                                        can_motors.speed_mode(0)
                                        can_motors.weight = 0
                                        z.speed_mode(-200)
                                        sleep(1.5)
                                        z.speed_mode(0)
                                        can_motors.weight_z = 0

                                        config_data = ScrewConfig()
                                        config_data.n = weight
                                        config_data.power = power
                                        config_data.direction = direction
                                        config_data.speed = speed1
                                        config_data.actual_speed = actual_speed
                                        config_data.cycle = m
                                        config_data.save()

                                        print('initial...end...')
                                        sleep(2)

                                        print('initial...again...')
                                    break
                            if has_run == 1:
                                x.run(step_add, -1)
                                has_run = 0
                                sleep(1)
                                a_cycle = 1
                            if y_position == 1:
                                y.run(y_step, 1)
                                sleep(3)
                                y_position = 0
                                y_cycle = 0
                            with open('adjust_screw_config.json', 'r') as f:
                                config = json.load(f)
                            config.update({'position': 0})
                            with open('adjust_screw_config.json', 'w') as f:
                                json.dump(config, f)

        # else:
        #     print('stand by...')


if __name__ == "__main__":
    main()

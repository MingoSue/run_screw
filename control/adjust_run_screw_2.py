import os, pytz
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
        self.motor_id = motor_id
        self.speed = 0
        self.now_speed = 0
        self.position = 0
        self.current = 0
        self.weight = 0
        self.ser = serial.Serial('/dev/ttyUSB0')
        self.refresh_run()

    def send(self, aid, data):
        print(time.ctime() + 'can data {}'.format(data))
        msg = can.Message(arbitration_id=aid, data=data, extended_id=False)
        self.bus.send(msg, timeout=1)
        sleep(0.01)

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

            #if bin_now and bin_now2 and bin_now3 and bin_now4 and bin_now5:
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
                print('poweroff')
                poweroff()
            else:
                pass
            bin_pre = bin_now
            bout_pre = bout_now
            sleep(0.3)

    def serial_refresh(self):
        p = LED(22)
        while True:
            self.ser.write([0x01, 0x03, 0x00, 0x50, 0x00, 0x02, 0xC4, 0x1A])
            sleep(0.1)
            weight_data = self.ser.read_all()
            try:
                weight = round(int('0x'+weight_data.hex()[10:14], 16)*0.001, 3)
                if weight >= 10:
                    weight = 0
            except Exception as e:
                print(e)
                weight = 0
            try:
                with open('adjust_weight.json', 'w') as f:
                    json.dump({'weight': weight}, f)
            
                with open('adjust_screw_config.json', 'r') as f:
                    config = json.load(f)
 
                if weight > config['n']:
                    self.weight = weight
                    print('> max n : {}'.format(weight))

                    # protect io
                    p.on()
                    sleep(0.1)
                    p.off()
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
            self.direction = 1 if self.now_speed > 0 else -1
            # sleep(0.1)
            screw_data = {'speed': self.now_speed, 'current': self.current if self.current < 10000 else 0, 'direction': self.direction}
            with open('adjust_screw.json', 'w') as f:
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


def poweron_p():
    with open('adjust_screw_config.json', 'r') as f:
        config = json.load(f)
    config.update({'power': 1, "direction": 1})
    with open('adjust_screw_config.json', 'w') as f:
        json.dump(config, f)


def poweron_n():
    with open('adjust_screw_config.json', 'r') as f:
        config = json.load(f)
    config.update({'power': 1, "direction": -1})
    with open('adjust_screw_config.json', 'w') as f:
        json.dump(config, f)


def poweroff():
    with open('adjust_screw_config.json', 'r') as f:
        config = json.load(f)
    config.update({'power': 0})
    with open('adjust_screw_config.json', 'w') as f:
        json.dump(config, f)


def main():
    can_motors = Motor('can0', 0x13)

    n = 0
    # cycle times
    m = 0

    with open('adjust_screw_log.csv', "a+", newline='') as file:
        csv_file = csv.writer(file)
        head = ["cycle", "time", "weight"]
        csv_file.writerow(head)

    try:
        with open('adjust_screw_config.json', 'r') as f:
            config = json.load(f)
    except:
        # continue
        pass
    weight = config['n']
    # power 1 :on  0:off
    power = config['power']
    # direction 1 , -1
    direction = config['direction']
    # 20% 50%  100%
    speed = config['speed']
    # actual_speed = int(304 * speed * direction)

    sleep_time = 0.5

    while True:
        # try:
        #     with open('adjust_screw_config.json', 'r') as f:
        #         config = json.load(f)
        # except:
        #     continue

        print('nnnnnnnnnnnnnn', n)

        # weight = config['n']
        # # power 1 :on  0:off
        # power = config['power']
        # # direction 1 , -1
        # direction = config['direction']
        # # 20% 50%  100%
        # speed = config['speed']
        actual_speed = int(304 * speed * direction)
        print('actual_speedddddddddddddddddd', actual_speed)

        try:
            if power:
                # run
                if actual_speed >= 0:
                    record_list = Records.objects.filter(direction=1, d_weight__lte=1, d_weight__gt=0).distinct().aggregate(Avg('total_time'))
                    print('record_list==========', record_list)
                    avg_time = record_list['total_time__avg'] if record_list['total_time__avg'] else 0.0
                    if avg_time != 0.0:
                        s_time = avg_time - sleep_time
                        print('sssssssssss_time', s_time)
                        # first stage
                        can_motors.speed_mode(304)
                        if s_time > 0:
                            sleep(s_time * 0.8)
                        else:
                            sleep(avg_time / 2)

                        record = Records()
                        record.speed = 304
                        record.direction = 1
                        record.current = can_motors.current if can_motors.current < 10000 else 0
                        record.config_weight = weight
                        record.start_time = get_current_time()

                        can_motors.speed_mode(0)

                        # second stage
                        second_speed = int(304 * 0.8)
                        can_motors.speed_mode(second_speed)
                        if s_time > 0:
                            sleep(s_time * 0.2)
                        else:
                            sleep(avg_time / 3)

                        can_motors.speed_mode(0)

                        # third stage
                        third_speed = int(304 * 0.2)
                        can_motors.speed_mode(third_speed)
                        sleep(0.5)

                        print('can_motors.weightaaaaaaaaaaaaaa', can_motors.weight)
                        if can_motors.weight > weight:
                            print('aaaaaaaaaaaaaaaaa> max n : {}'.format(can_motors.weight))
                            sleep(2)
                            m += 1
                            n = 0

                            record.cycle = m
                            record.weight = can_motors.weight
                            record.d_weight = can_motors.weight - weight
                            if record.d_weight > 1 and sleep_time < avg_time:
                                sleep_time += 0.5
                            record.end_time = get_current_time()
                            record.total_time = (record.end_time - record.start_time).seconds
                            record.save()

                            # reverse
                            can_motors.speed_mode(-304)
                            print('gaga')
                            sleep(4)

                            print('aaaaaaaaaaaaaaammmmmmmmmmmmm', m)
                            with open('adjust_screw_log.csv', "a+", newline='') as f:
                                csv_f = csv.writer(f)
                                data = [m, time.ctime(), can_motors.weight]
                                csv_f.writerow(data)
                            record = Records()
                            record.cycle = m
                            record.speed = -304
                            record.direction = -1
                            record.current = can_motors.current if can_motors.current < 10000 else 0
                            record.weight = can_motors.weight
                            record.save()

                            can_motors.speed_mode(0)

                            config_data = ScrewConfig()
                            config_data.n = weight
                            config_data.power = power
                            config_data.direction = direction
                            config_data.speed = speed
                            config_data.cycle = m
                            config_data.save()

                            print('aaaaaaaaaahaha')
                            can_motors.weight = 0
                            print('boboaaaaaaaaaaaa', can_motors.weight)

                        # sleep(2)
                        else:
                            print('aaaaaaaaaaaagain...')
                            n += 1
                            if n >= 15:
                                print('aaaaaaaaaaend...')
                                with open('adjust_screw_log.csv', "a+", newline='') as fi:
                                    csv_fi = csv.writer(fi)
                                    end = [m, time.ctime(), can_motors.weight, 'end']
                                    csv_fi.writerow(end)
                                break
                            sleep(0.5)

                    else:
                        can_motors.speed_mode(actual_speed)
                        sleep(0.5)

                        record = Records()
                        record.speed = actual_speed
                        record.direction = 1
                        record.current = can_motors.current if can_motors.current < 10000 else 0
                        record.config_weight = weight
                        record.start_time = get_current_time()

                        print('can_motors.weight==============', can_motors.weight)
                        if can_motors.weight > weight:
                            print('=============> max n : {}'.format(can_motors.weight))
                            sleep(2)
                            m += 1
                            n = 0

                            record.cycle = m
                            record.weight = can_motors.weight
                            record.d_weight = can_motors.weight - weight
                            if record.d_weight > 1:
                                speed -= 0.05
                            record.end_time = get_current_time()
                            record.total_time = (record.end_time - record.start_time).seconds
                            record.save()

                            # reverse
                            can_motors.speed_mode(-304)
                            print('gaga')
                            sleep(4)

                            print('mmmmmmmmmmmmm', m)
                            with open('adjust_screw_log.csv', "a+", newline='') as f:
                                csv_f = csv.writer(f)
                                data = [m, time.ctime(), can_motors.weight]
                                csv_f.writerow(data)
                            record = Records()
                            record.cycle = m
                            record.speed = -304
                            record.direction = -1
                            record.current = can_motors.current if can_motors.current < 10000 else 0
                            record.weight = can_motors.weight
                            record.save()

                            can_motors.speed_mode(0)

                            config_data = ScrewConfig()
                            config_data.n = weight
                            config_data.power = power
                            config_data.direction = direction
                            config_data.speed = speed
                            config_data.cycle = m
                            config_data.save()

                            print('haha')
                            can_motors.weight = 0
                            print('bobo...............', can_motors.weight)

                        # sleep(2)
                        else:
                            print('again...')
                            n += 1
                            if n >= 15:
                                print('end...')
                                with open('adjust_screw_log.csv', "a+", newline='') as fi:
                                    csv_fi = csv.writer(fi)
                                    end = [m, time.ctime(), can_motors.weight, 'end']
                                    csv_fi.writerow(end)
                                break
                            sleep(0.5)
                else:
                    if n >= 10:
                        break

                    m += 1
                    # reverse
                    can_motors.speed_mode(actual_speed)
                    print('---gaga')
                    sleep(4)

                    record = Records()
                    record.cycle = m
                    record.speed = actual_speed
                    record.direction = -1
                    record.current = can_motors.current if can_motors.current < 10000 else 0
                    record.weight = can_motors.weight
                    record.save()

                    can_motors.speed_mode(0)
                    print('------haha')
                    can_motors.weight = 0
                    print('------bobo...............', can_motors.weight)

                    # normal
                    can_motors.speed_mode(-actual_speed)
                    sleep(0.5)
                    print('-----weight==============', can_motors.weight)
                    if can_motors.weight > weight:
                        print('=============> max n : ------{}'.format(can_motors.weight))
                        sleep(2)
                        # m += 1
                        n = 0
                        print('-----mmmmmmmmmmmmm', m)
                        with open('adjust_screw_log.csv', "a+", newline='') as f:
                            csv_f = csv.writer(f)
                            data = [m, time.ctime(), can_motors.weight]
                            csv_f.writerow(data)

                        record = Records()
                        record.cycle = m
                        record.speed = -actual_speed
                        record.direction = 1
                        record.current = can_motors.current if can_motors.current < 10000 else 0
                        record.weight = can_motors.weight
                        record.save()

                        config_data = ScrewConfig()
                        config_data.n = weight
                        config_data.power = power
                        config_data.direction = direction
                        config_data.speed = speed
                        config_data.cycle = m
                        config_data.save()
                    else:
                        while True:
                            print('-----again...')
                            n += 1
                            can_motors.speed_mode(-actual_speed)
                            sleep(0.5)
                            print('-----weight==============', can_motors.weight)
                            if can_motors.weight > weight:
                                print('=============> max n : ------{}'.format(can_motors.weight))
                                sleep(2)
                                # m += 1
                                n = 0
                                print('-----mmmmmmmmmmmmm', m)
                                with open('adjust_screw_log.csv', "a+", newline='') as f:
                                    csv_f = csv.writer(f)
                                    data = [m, time.ctime(), can_motors.weight]
                                    csv_f.writerow(data)

                                record = Records()
                                record.cycle = m
                                record.speed = -actual_speed
                                record.direction = 1
                                record.current = can_motors.current if can_motors.current < 10000 else 0
                                record.weight = can_motors.weight
                                record.save()

                                config_data = ScrewConfig()
                                config_data.n = weight
                                config_data.power = power
                                config_data.direction = direction
                                config_data.speed = speed
                                config_data.cycle = m
                                config_data.save()

                                break

                            if n >= 15:
                                print('-----end...')
                                with open('adjust_screw_log.csv', "a+", newline='') as fi:
                                    csv_fi = csv.writer(fi)
                                    end = [m, time.ctime(), can_motors.weight, '---end']
                                    csv_fi.writerow(end)
                                break
                            sleep(0.5)
            else:
                can_motors.speed_mode(0)
            # sleep(0.5)

        except Exception as e:
            print('eeeeeeeeeeeeeeeee', e)


if __name__ == "__main__":
    main()

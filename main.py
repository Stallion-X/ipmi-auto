import os
from apscheduler.schedulers.background import BlockingScheduler

tool_dir = '.\\ipmi\\'
ip = ''
username = ''
password = ''
interval_seconds = 30


def disable_auto():
    os.popen(f'{tool_dir}ipmitool.exe -I lanplus -H {ip} -U {username} -P {password} raw 0x30 0x30 0x01 0x00')


def enable_auto():
    os.popen(f'{tool_dir}ipmitool.exe -I lanplus -H {ip} -U {username} -P {password} raw 0x30 0x30 0x01 0x01')


def set_speed(percent):
    disable_auto()
    os.popen(
        f'{tool_dir}ipmitool.exe -I lanplus -H {ip} -U {username} -P {password} raw 0x30 0x30 0x02 0xff {hex(percent)}')


def get_temp():
    result = os.popen(f'{tool_dir}ipmitool.exe -I lanplus -H {ip} -U {username} -P {password} sensor').read()
    result = result.replace("\r\n", "\n")
    sensor_list = result.split('\n')
    temp_list = []
    for sensor in sensor_list:
        if 'Temp' in sensor:
            temp_list.append(float(sensor.split('|')[1].strip()))
    return temp_list


def auto_config():
    temp_list = get_temp()
    temp = max(temp_list)
    print(f'current temp:{temp}')
    if temp >= 79:
        set_speed(40)
    elif 70 <= temp < 79:
        set_speed(30)
    elif 60 <= temp < 70:
        set_speed(20)
    elif 50 <= temp < 60:
        set_speed(15)
    elif temp < 50:
        set_speed(5)


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(auto_config, 'interval', seconds=interval_seconds)
    scheduler.start()

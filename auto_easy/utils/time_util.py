import random


class Timeout:
    def __init__(self, seconds):
        """
        初始化函数，接受一个表示超时时间的参数seconds（单位：秒）
        """
        self.seconds = seconds
        self.start_time = time.time()
        self.check_times = 0

    def not_timeout(self):
        """
        对外函数，用于检查是否超过设定的超时时间，超过则返回False，未超过返回True
        """
        # 如果超时时间设置为0,允许调用一次
        self.check_times += 1
        if self.seconds == 0 and self.check_times == 1:
            return True
        current_time = time.time()
        if current_time - self.start_time > self.seconds:
            return False
        return True

    def is_timeout(self):
        return not self.not_timeout()


def calculate_average_milliseconds(time_array):
    """
    计算给定时间数组中时间对象的平均耗时，单位为毫秒。

    参数:
    time_array (list): 包含datetime.now()获取的时间对象的数组，假设时间对象成对出现表示开始和结束时间。

    返回:
    int: 平均耗时，单位为毫秒。
    """
    if len(time_array) == 0:
        return 0
    durations_in_milliseconds = []
    for i in range(len(time_array) - 1):
        start_time = time_array[i]
        end_time = time_array[i + 1]
        # 取出毫秒信息并计算时间差（单位：毫秒）
        time_diff = end_time - start_time
        duration_milliseconds = int(time_diff.total_seconds() * 1000)
        durations_in_milliseconds.append(duration_milliseconds)

    if durations_in_milliseconds:
        total_milliseconds = sum(durations_in_milliseconds)
        average_duration_milliseconds = total_milliseconds // len(durations_in_milliseconds)
        return average_duration_milliseconds
    return 0


def cost_ms(start) -> int:
    diff = time.time() - start
    return int(diff * 1000)


import functools
import time


def limit_to_one_true_per_x_seconds_decorator(x):
    """
    装饰器函数，使得被装饰的函数在主线程持续调用时，在最近x秒内只返回一次True。

    参数:
    x (float或int): 限定的时间间隔（秒）。
    """
    last_true_time = None

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_true_time
            current_time = time.time()
            if last_true_time is None or current_time - last_true_time > x:
                last_true_time = current_time
                return func(*args, **kwargs)
            return True

        return wrapper

    return decorator


@limit_to_one_true_per_x_seconds_decorator(1)
def one_sec_one_false(x):
    return False


def sleep_with_rand(sec, min_rate=0.8, max_rate=1.2):
    time.sleep(random.uniform(sec * min_rate, sec * max_rate))


def sleep_with_ms(ms, min_rate=1.0, max_rate=1.0):
    sec = ms / 1000
    time.sleep(random.uniform(sec * min_rate, sec * max_rate))


from datetime import datetime


def get_cur_timestr():
    now = datetime.now()
    time_str = now.strftime('%Y%m%d%H%M%S')
    return time_str


if __name__ == '__main__':
    print(get_cur_timestr())
    ############ 测试平均时间计算

    # 模拟存储时间字符串的列表，你可以根据实际情况替换这里的数据来源
    time_strings = [
        '无移动->有移动: 2024-12-11 15:52:05.597354',
        '无移动->有移动: 2024-12-11 15:52:07.195285',
        '无移动->有移动: 2024-12-11 15:52:08.965235',
        '无移动->有移动: 2024-12-11 15:52:10.421640',
        '无移动->有移动: 2024-12-11 15:52:12.023158',
        '无移动->有移动: 2024-12-11 15:52:13.639344',
        '无移动->有移动: 2024-12-11 15:52:15.234323',
        '无移动->有移动: 2024-12-11 15:52:16.844498',
        '无移动->有移动: 2024-12-11 15:52:18.443976',
        '无移动->有移动: 2024-12-11 15:52:20.045133',
        '无移动->有移动: 2024-12-11 15:52:21.660275',
        '无移动->有移动: 2024-12-11 15:52:23.249212',
        '无移动->有移动: 2024-12-11 15:52:24.869407',
        '无移动->有移动: 2024-12-11 15:52:26.463027',
        '无移动->有移动: 2024-12-11 15:52:28.069128',
        '无移动->有移动: 2024-12-11 15:52:29.664688',
        '无移动->有移动: 2024-12-11 15:52:31.270980',
        '无移动->有移动: 2024-12-11 15:52:32.865749',
    ]

    datetime_objects = []
    for time_string in time_strings:
        # 提取出时间部分的字符串
        time_part = time_string.split(": ", 1)[-1]
        # 将时间字符串转换为datetime对象
        dt = datetime.strptime(time_part, "%Y-%m-%d %H:%M:%S.%f")
        datetime_objects.append(dt)

    print(datetime_objects)

    # 模拟一个包含时间记录的数组，这里假设是成对出现，前一个是开始时间，后一个是结束时间，依次类推
    # time_records = [
    #     datetime(2024, 12, 11, 10, 0, 0, 10000),
    #     datetime(2024, 12, 11, 10, 0, 0, 20000),
    #     datetime(2024, 12, 11, 10, 0, 0, 30000),
    #     datetime(2024, 12, 11, 10, 0, 0, 40000),
    # ]

    result = calculate_average_milliseconds(datetime_objects)
    print(f"平均耗时（毫秒）: {result}")

    # ########### 创建一个Timeout实例，设置超时时间为5秒
    # timeout_obj = Timeout(5)
    # # 在一定时间内调用check函数进行检查
    # time.sleep(3)
    # print(timeout_obj.not_timeout())  # 预期输出True，因为还未超过5秒
    # time.sleep(3)
    # print(timeout_obj.not_timeout())  # 预期输出False，因为已经超过5秒了

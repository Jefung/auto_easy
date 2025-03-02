import random
from datetime import datetime

from pypinyin import lazy_pinyin

from auto_easy.utils.time_util import Timeout


def gen_lambda_func(func, *args, **kwargs):
    def inner_func():
        return func(*args, **kwargs)

    return inner_func


count = 0


def ten_times_one_true(x=0):
    global count
    count += 1
    if count % 10 == 0:
        result = True
        count = 0
    else:
        result = False
    return result


def array_to_camelcase(arr, first=False):
    result = ""
    for s in arr:
        for index, element in enumerate(s):
            if first:
                if index == 0:
                    result += element.capitalize()
            else:
                if index == 0:
                    result += element.capitalize()
                else:
                    result += element.lower()
    return result


def cvt_chinese(s):
    py_list = lazy_pinyin(s)
    return ''.join(py_list)


import time


def loop_with_sleep(times, sleep_sec, func, logger=None):
    """
    循环调用指定函数并在每次调用后暂停指定秒数。

    参数:
    x (int): 循环的次数。
    sec (float): 每次调用函数后暂停的秒数。
    func (function): 要循环调用的函数，该函数不接受任何参数。
    """
    for i in range(int(times)):
        if logger is not None:
            logger.info("####### 开始第{}次调用 ####################".format(i + 1))
        ans = func()
        if logger is not None:
            logger.info("调用结果：{}".format(ans))
            logger.info("####### 结束第{}次调用，sleep {} ##########".format(i + 1, sleep_sec))
        time.sleep(sleep_sec)


def loop_until_true(f, to_ms=1000, sleep_ms=50, ) -> (bool, int):
    if to_ms <= 0:
        return f(), 1
    to = Timeout(to_ms / 1000)
    cnt = 0
    while to.not_timeout():
        cnt += 1
        ok = f()
        if ok:
            return True, cnt
        time.sleep(sleep_ms / 1000)
    return False, cnt


import tempfile
import os

temp_dir = tempfile.gettempdir()


def get_tmp_file(ext='jpg'):
    now = datetime.now()
    # 格式化时间字符串
    time_str = now.strftime('%Y%M%d_%H%M%S_%f')[:-3]
    return os.path.join(temp_dir, f"{time_str}.{ext}")


def set_env(k, v):
    os.environ[k] = v


def get_env(k, default=None):
    if k in os.environ:
        return os.environ[k]
    return default


def rand_int_in_time_range(min_val, max_val, time_window_seconds):
    """
    在给定的最小值和最大值之间生成随机数，并且保证在特定时间窗口内生成的随机数相同。

    参数:
    min_val (int或float): 随机数范围的最小值。
    max_val (int或float): 随机数范围的最大值。
    time_window_seconds (int): 时间窗口的秒数，在这个时间窗口内生成的随机数保持一致。

    返回:
    int或float: 生成的随机数
    """
    current_time = int(time.time())
    # 计算当前时间所在的时间窗口起始时间戳
    window_start_time = current_time - (current_time % time_window_seconds)
    random.seed(window_start_time)
    return int(random.uniform(min_val, max_val))

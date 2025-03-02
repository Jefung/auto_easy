import multiprocessing
import threading
import time
from concurrent.futures import ThreadPoolExecutor

cpu_count = multiprocessing.cpu_count()


def concurrent_exec_functions(func_list, max_workers=None):
    if len(func_list) == 0:
        return []

    if len(func_list) == 1:
        try:
            return [func_list[0]()]
        except Exception as e:
            raise e

    if max_workers is not None:
        # work在[len(func_list), cup_count-1]中选择最小一个
        max_workers = min(cpu_count - 1, len(func_list))

    results = []
    with ThreadPoolExecutor(max_workers) as executor:
        futures = [executor.submit(func) for func in func_list]
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append(None)  # 如果函数执行出现异常，对应位置存None
                raise e
    return results


def concurrent_exec_one_func(func, args_list, max_workers=None):
    func_list = []
    for arg in args_list:
        def inner_func(arg1=arg):
            return func(arg1)

        func_list.append(inner_func)
    return concurrent_exec_functions(func_list, max_workers=max_workers)


def concurrent_exec_multi_func_one_arg(func_list, args, max_workers=None):
    fs = []
    for func in func_list:
        def inner_func(_f=func):
            return _f(args)

        fs.append(inner_func)
    return concurrent_exec_functions(fs, max_workers=max_workers)


def timing_thread(user_func, sec):
    def _f():
        while True:
            user_func()
            time.sleep(sec)

    th = threading.Thread(target=_f)
    th.daemon = True
    th.start()


def async_thread(user_func):
    th = threading.Thread(target=user_func)
    th.daemon = True
    th.start()


class SharedVal:
    def __init__(self, val=None):
        self.val = val
        self.lock = threading.RLock()

    def get(self, dft_val=None):
        with self.lock:
            if self.val is None:
                return dft_val
            return self.val

    def set(self, val):
        with self.lock:
            self.val = val


if __name__ == '__main__':
    def print_ii(i):
        print(i * i)
        # print(j + j)


    def print_ii2(i):
        print(i + i)


    args = [(1), (2)]
    concurrent_exec_multi_func_one_arg([print_ii, print_ii2], 1)

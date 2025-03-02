# from datetime import time

import time

from auto_easy.global_log import logger


def timeit_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        # 获取函数名称
        func_name = func.__name__
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"函数 {func_name} 执行完毕，耗时: {elapsed_time:.3f} 秒")
        return result

    return wrapper

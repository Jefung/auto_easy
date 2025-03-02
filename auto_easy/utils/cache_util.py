import sys
import threading

import cachetools


def func_cache_ignore_args(ttl=sys.maxsize):
    cache = cachetools.TTLCache(maxsize=99999, ttl=ttl)
    lock = threading.Lock()

    def actual_decorator(func):
        def wrapper(*args, **kwargs):
            key = func.__name__
            if key in cache:
                try:
                    return cache[key]
                except KeyError:
                    pass
            with lock:
                try:
                    return cache[key]
                except KeyError:
                    pass
                result = func(*args, **kwargs)
                cache[key] = result
            return result

        return wrapper

    return actual_decorator


# 定义支持自定义ttl的缓存装饰器
def cache_with_custom_time(ttl=sys.maxsize):
    cache = cachetools.TTLCache(maxsize=99999, ttl=ttl)
    lock = threading.Lock()

    def actual_decorator(func):
        def wrapper(*args, **kwargs):
            key = args + tuple(kwargs.items())
            if key in cache:
                try:
                    return cache[key]
                except KeyError:
                    pass
            with lock:
                try:
                    return cache[key]
                except KeyError:
                    pass
                result = func(*args, **kwargs)
                cache[key] = result
            return result

        return wrapper

    return actual_decorator

import logging
import os
import re

from logging.handlers import TimedRotatingFileHandler

logger_name = 'auto_easy'


def get_logger():
    return logging.getLogger(logger_name)


def get_log_formatter():
    # 定义日志格式
    datefmt = '%Y/%m/%d-%H:%M:%S'
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s', )
    formatter.default_time_format = datefmt
    formatter.default_msec_format = '%s.%03d'
    return formatter


def set_log_2_console(log_level=logging.INFO):
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(get_log_formatter())
    get_logger().setLevel(log_level)
    get_logger().addHandler(console_handler)


def set_log_2_file(log_dir,file_prefix='', log_level=logging.INFO):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 处理文件名中的特殊字符
    pattern = r'[<>:"/\\|?*]'
    # 使用 re.sub 函数将匹配到的特殊字符替换为空字符串
    file_prefix = re.sub(pattern, '', file_prefix)
    # 去除首尾的空白字符，并将连续的空格替换为单个下划线
    file_prefix = re.sub(r'\s+', '_', file_prefix.strip())


    get_logger().setLevel(log_level)
    log_file = os.path.join(log_dir, f"auto_easy_{file_prefix}.log")


    logger = get_logger()
    file_handler = TimedRotatingFileHandler(log_file, when="D", interval=1, backupCount=3, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(get_log_formatter())
    logger.addHandler(file_handler)


logger = get_logger()

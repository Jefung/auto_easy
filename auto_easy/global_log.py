import logging
import os

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


def set_log_2_console(log_level=logging.DEBUG):
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(get_log_formatter())
    get_logger().setLevel(log_level)
    get_logger().addHandler(console_handler)


def set_log_2_file(log_dir, log_level=logging.INFO):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    get_logger().setLevel(log_level)
    log_file = os.path.join(log_dir, f"auto_easy.log")
    logger = get_logger()
    file_handler = TimedRotatingFileHandler(log_file, when="D", interval=1, backupCount=3, encoding="utf-8")
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)


logger = get_logger()

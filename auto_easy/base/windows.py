import ctypes
import logging
import random
from functools import lru_cache

import PIL
import win32api
import win32con
import win32gui
import win32ui
from PIL import Image

from auto_easy.models import Direction
from auto_easy.models import Box, Point
from auto_easy.utils import logger, sleep_with_ms
from auto_easy.utils.cache_util import func_cache_ignore_args
import ctypes
import win32gui
import win32con

def get_window_dpi(hwnd):
    # 方法1：Windows 10+ 专用 API
    try:
        dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
        return dpi
    except WindowsError:
        pass

    # 方法2：通过设备上下文计算（兼容旧系统）
    hdc = win32gui.GetDC(hwnd)
    dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, win32con.LOGPIXELSX)
    win32gui.ReleaseDC(hwnd, hdc)
    return dpi_x

# 使用lru_cache装饰器，设置最大缓存数量（可选参数，这里设为None表示无限制）
@lru_cache(maxsize=None)
def find_windows_with_prefix(prefix='Phone'):
    # 通过win32gui.EnumWindows函数可以枚举系统中的所有顶级窗口。对于每个窗口，使用win32gui.GetWindowText函数获取窗口标题，然后检查窗口标题是否以指定的前缀开始，从而实现前缀模糊匹配。
    window_handles = []

    def callback(hwnd, extra):
        window_title = win32gui.GetWindowText(hwnd)
        if window_title.startswith(prefix):
            window_handles.append(
                {'hwnd': hwnd, 'title': window_title}
            )
        return True

    win32gui.EnumWindows(callback, None)
    sorted_ans = sorted(window_handles, key=lambda w: w['title'])
    if len(sorted_ans) == 0:
        raise Exception('No windows found, title prefix: {}'.format(prefix))
    return sorted_ans[0]['hwnd']


import time


class ClickStatus:
    def __init__(self, down=False, x=-1, y=-1):
        self.down = down
        self.x = x
        self.y = y

    def __str__(self):
        return f'{self.down}({self.x},{self.y})'


class Window:
    def __init__(self, window_id='', logger=logging.getLogger()):
        import ctypes
        # 声明程序为 DPI 感知（需在代码开头执行）
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        self.hwnd = None
        if window_id:
            self.hwnd = find_windows_with_prefix(window_id)
            logger.debug('init win_mgr, hwnd {}'.format(self.hwnd))
        self.logger = logger
        self.logger.setLevel(logging.INFO)

        dpi_x = get_window_dpi(self.hwnd)
        msg = "[窗口管理器] 标题: {}, 句柄：{}, DPI: {}, 大小: <{}>宽高{}".format(self.get_text(), self.hwnd,dpi_x,
                                                                        self.get_client_rect(),
                                                                        self.get_client_size())
        # print(msg)
        self.logger.info(msg=msg)
        self.prev_click_status = ClickStatus()
        self.latest_pil_img = None
        self.latest_pil_time = 0
        self.send_msg_count = 0
        self.last_pump_time = time.time()
        self.pump_interval = 0.2

    def get_info(self):
        return "[窗口管理器] 标题: {}, 句柄：{}, 大小: <{}>宽高{}".format(self.get_text(), self.hwnd,
                                                                         self.get_client_rect(),
                                                                         self.get_client_size())

    @property
    def height(self):
        width, height = self.get_client_size()
        return height

    @property
    def width(self):
        width, height = self.get_client_size()
        return width

    @property
    def screen_box(self) -> Box:
        return Box(0, 0, self.width, self.height)

    def get_text(self):
        return win32gui.GetWindowText(self.hwnd)

    def get_client_size(self):
        left, top, right, down = win32gui.GetClientRect(self.hwnd)
        return right - left, down - top

    def get_client_rect(self):
        left, top, right, down = win32gui.GetClientRect(self.hwnd)
        return left, top, right, down

    def get_client_lt_in_screen(self):
        rect = win32gui.GetClientRect(self.hwnd)
        client_left, client_top = win32gui.ClientToScreen(self.hwnd, (rect[0], rect[1]))
        return client_left, client_top

    def get_window_lt_in_screen(self):

        window_rect = win32gui.GetWindowRect(self.hwnd)
        return window_rect[0], window_rect[1]

    def client_xy_to_window(self, x, y):
        abs_client_x, abs_client_y = self.get_client_lt_in_screen()
        abs_window_x, abs_window_y = self.get_window_lt_in_screen()
        return abs_client_x - abs_window_x + x, abs_client_y - abs_window_y + y

    def client_xy_to_screen(self, x, y):
        win_x, win_y = self.client_xy_to_window(x, y)
        abs_win_x, abs_win_y = self.get_window_lt_in_screen()
        return abs_win_x + win_x, abs_win_y + win_y

    def move_window(self, x1, y1, x2, y2):
        # print('move_window: x1: {}, y1: {}, x2: {}, y2: {}'.format(x1, y1, x2, y2))
        win32gui.MoveWindow(self.hwnd, x1, y1, x2 - x1, y2 - y1, True)
        win32gui.UpdateWindow(self.hwnd)
        time.sleep(1)

    def check_coor(self, x, y):
        # pass
        left, top, right, down = self.get_client_rect()
        if not (left <= x <= right and top <= y <= down):
            raise Exception(f'xy(<{x},{y}>) is invalid')

    def left_click(self, x, y, press_sec=0.05, af_sleep=0, bf_sleep=0):
        x = int(x)
        y = int(y)
        time.sleep(bf_sleep)

        self.check_coor(x, y)
        self.left_down(x, y)
        time.sleep(press_sec)
        self.left_up(x, y)

        time.sleep(af_sleep)

    def left_click_in_box(self, box: Box, af_sleep=0, bf_sleep=0, scale=0.75):
        # 为了避免点击到边缘,这里先将区域缩小到scale比例
        scaled_box = box.copy_by_scale(scale)
        point = scaled_box.get_rand_point()

        self.left_click(point.x, point.y, af_sleep=af_sleep, bf_sleep=bf_sleep)

    def left_down(self, x, y):
        self.check_coor(x, y)
        self._mouse_click(True, x, y)

    def left_up(self, x=-1, y=-1):
        if x >= 0 and y >= 0:
            self.check_coor(x, y)
        self._mouse_click(False, x, y)

    def reset_left_click(self):
        if self.prev_click_status.down:
            self._mouse_click(False)

    def _mouse_click(self, down, x=-1, y=-1):
        # logger.debug('_mouse_click: down={}, x={}, y={}, prev_click_status: {}'.format(down, x, y, self.prev_click_status))
        lParam = None
        if x >= 0 and y >= 0:
            lParam = win32api.MAKELONG(x, y)
        # 抬起
        if not down:
            res = self._send_message(self.hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, lParam)
        else:
            # 之前是按压状态, 直接移动鼠标，不需要在按压
            # TODO: 可能需要增加超时失效机制
            if self.prev_click_status.down and self.prev_click_status.x > 0:
                res = self._send_message(self.hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, lParam)
            else:
                res = self._send_message(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)

        self.prev_click_status = ClickStatus(down, x, y)

    def simple_mouse_move(self,x,y,distance,direction:Direction):
        target_x = x
        target_y = y
        if direction == Direction.LEFT:
            target_x = x - distance
        elif direction == Direction.RIGHT:
            target_x = x + distance
        elif direction == Direction.UP:
            target_y = y - distance
        elif direction == Direction.DOWN:
            target_y = y + distance
        logger.debug(f'simple_mouse_move {direction} {distance} from <{x},{y}> to <{target_x},{target_y}>')

        self.mouse_move(x,y,target_x,target_y)


    def mouse_move(self, x1, y1, x2, y2, steps=5, base_delay=0.001):
        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps
        self._mouse_click(False)

        # 速度曲线调整，例如使用二次函数模拟速度变化
        speed_curve = [i * (steps - i) + 1 for i in range(steps + 1)]
        total_speed = sum(speed_curve)

        for i in range(steps + 1):
            # 计算当前位置
            x = int(x1 + i * dx)
            y = int(y1 + i * dy)

            # 引入随机抖动
            jitter_x = random.randint(-2, 2)
            jitter_y = random.randint(-2, 2)
            x += jitter_x
            y += jitter_y

            # 根据速度曲线调整延迟
            current_speed = speed_curve[i] / total_speed
            current_delay = base_delay / current_speed

            # 引入随机延迟
            random_delay = random.uniform(0.8, 1.2) * current_delay

            self._mouse_click(True, x, y)
            time.sleep(random_delay)
            # win32gui.PumpWaitingMessages()

        self._mouse_click(False)
        # win32gui.PumpWaitingMessages()
        time.sleep(0.1)

    def debug_left_click(self, x, y):
        lParam = win32api.MAKELONG(x, y)
        self._send_message(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)

    def mouse_wheel(self, x, y, down=True, times=100, loop_sleep=0.003):
        abs_x, abs_y = self.get_client_lt_in_screen()
        lParam = win32api.MAKELONG(abs_x + x, abs_y + y)
        wParam = win32api.MAKELONG(0, win32con.WM_MOUSEWHEEL)
        if down:
            wParam = win32api.MAKELONG(0, win32con.WM_MOUSEWHEEL * -1)

        # 发送鼠标滚轮向下滑动的消息
        i = 0
        while i < times:
            self._send_message(self.hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)
            time.sleep(loop_sleep)
            i += 1

    def wheel_move(self, down: bool, dis=100, point: Point = None, sleep_ms=10):
        if point is None:
            point = self.screen_box.get_mid_point(offset_rate=0.05)

        # logger.info('[大漠] 滑轮向{}移动{}'.format('下' if down else '上', dis))
        # 本机测试，调用80次，每次sleep 0.1，移动210的距离，平均每次调用移动2.6
        times = dis / 1.0
        self.mouse_wheel(point.x, point.y, down, times)

        sleep_with_ms(sleep_ms)

    def _send_message(self, *args, **kwargs):
        logger.debug(f'_send_message {args} {kwargs}')
        # 在 PostMessage 版本中，消息被快速添加到队列中，更接近真实的鼠标移动
        if args[1] in [win32con.WM_MOUSEMOVE,win32con.WM_MOUSEWHEEL]:
            ok = win32gui.PostMessage(*args, **kwargs)
        else:
            ok = win32gui.SendMessage(*args, **kwargs)

        if time.time() - self.last_pump_time >= self.pump_interval:
            win32gui.PumpWaitingMessages()
            self.last_pump_time = time.time()
        return ok

    def capture(self, box: Box = None, latest_lag=0):
        # 允许获取最近x秒内的图片,即图片复用
        if latest_lag > 0 and (time.time() - self.latest_pil_time) <= latest_lag:
            win_img = self.latest_pil_img
        else:
            win_img = self._capture_window()

        # 图片裁剪
        if box is not None and not box.is_empty():
            cropped_image = win_img.crop(box.tuple())
            return cropped_image
        return win_img

    # todo: 待废弃
    def capture_window(self, x1=-1, y1=-1, x2=-1, y2=-1) -> PIL.Image:
        win_img = self._capture_window()
        if x1 >= 0 and x2 >= 0 and y1 >= 0 and y2 >= 0:
            cropped_image = win_img.crop((x1, y1, x2, y2))
            return cropped_image
        return win_img

    # todo: 待废弃
    def capture_box(self, x1, y1, x2, y2) -> PIL.Image:
        win_img = self._capture_window()
        cropped_image = win_img.crop((x1, y1, x2, y2))
        return cropped_image

    @func_cache_ignore_args(0.1)
    def _capture_window(self) -> PIL.Image:
        hwnd = self.hwnd
        x1, y1 = 0, 0
        x2, y2 = self.get_client_size()
        width = x2 - x1
        height = y2 - y1

        def _gen_img():
            # 获取窗口的设备上下文
            hdc = win32gui.GetWindowDC(hwnd)

            # 创建一个与窗口设备上下文兼容的设备上下文
            src_dc = win32ui.CreateDCFromHandle(hdc)

            # 创建一个位图对象，并将其选入内存设备上下文
            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(src_dc, width, height)

            # 创建一个内存设备上下文，用于存储位图
            mem_dc = src_dc.CreateCompatibleDC()
            mem_dc.SelectObject(bmp)
            # 将窗口内容复制到内存设备上下文中的位图, 参数为（目标位置的x和y坐标），（目标位图的宽度和高度），（源设备上下文），（源位置的x和y坐标），（光栅操作码）
            # 这里（源位置的x和y坐标）传入的时相对于整个窗口左上角位置， 需要计算
            target_x, target_y = self.client_xy_to_window(x1, y1)
            mem_dc.BitBlt((0, 0), (width, height), src_dc,
                          (target_x, target_y), win32con.SRCCOPY)
            # 获取位图的位数据
            bmp_info = bmp.GetInfo()
            bmp_bits = bmp.GetBitmapBits(True)
            # 使用PIL库将位图数据转换为图像对象
            img = Image.frombuffer('RGB',
                                   (bmp_info['bmWidth'], bmp_info['bmHeight']),
                                   bmp_bits, 'raw', 'BGRX', 0, 1)
            src_dc.DeleteDC()
            mem_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hdc)
            win32gui.DeleteObject(bmp.GetHandle())
            return img

        screenshot = None
        for i in range(10):
            try:
                screenshot = _gen_img()
                break
            except Exception as e:
                logger.error('failed to generate screenshot, e:{}'.format(e))
                time.sleep(0.1)

        if screenshot is None:
            raise Exception('failed to generate screenshot')

        self.latest_pil_img = screenshot
        self.latest_pil_time = time.time()
        return screenshot

    def set_client_width_then_height(self, width, height):
        logger.debug('预期窗口 width: {}, height: {}'.format(width, height))
        # 设置当前进程为 DPI（每英寸点数，Dots Per Inch）感知状态
        ctypes.windll.user32.SetProcessDPIAware()

        client_width, client_height = self.get_client_size()
        logger.debug('当前窗口 width: {}, height: {}'.format(client_width, client_height))
        abs_win_x, abs_win_y = self.get_window_lt_in_screen()
        abs_client_rd_x, abs_client_rd_y = self.client_xy_to_screen(width, height)
        i = 0
        while i < 3:
            client_width, client_height = self.get_client_size()
            if abs(client_width - width) <= width * 0.05 and abs(client_height - height) <= height * 0.05:
                break
            i += 1
            self.move_window(abs_win_x, abs_win_y, abs_client_rd_x, abs_client_rd_y)
        logger.debug('最新窗口({}) width: {}, height: {}'.format(self.get_text(), client_width, client_height))


if __name__ == '__main__':
    pass

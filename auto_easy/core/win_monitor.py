import threading
import time

from auto_easy.base.windows import Window
from auto_easy.utils import logger


class TimerProcessor:
    def __init__(self, interval, f):
        self.interval = interval
        self.f = f

    def _timer_call(self):
        interval_ms = self.interval * 1000
        while True:
            now_ms = time.time() * 1000
            next_call = now_ms + (interval_ms - (now_ms % interval_ms))
            delay_ms = next_call - now_ms
            time.sleep(delay_ms / 1000)
            self.f()

    def async_run(self):
        th = threading.Thread(target=self._timer_call)
        th.daemon = True
        th.start()


class WinTimer(Window):
    def __init__(self, window_id=None):
        Window.__init__(self, window_id=window_id)

    def add_timer_minitor(self, interval, f):
        def _f():
            f(self)

        logger.debug('add_timer_minitor, interval=%f, f=%s', interval, f)
        TimerProcessor(interval, _f).async_run()


if __name__ == '__main__':
    win = WinTimer('Phone-VB')

    win.add_timer_minitor(1.5, lambda x: print(time.time()))

    time.sleep(10)

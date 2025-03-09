import datetime
import os

from auto_easy.base.image.draw import draw_rectangles
from auto_easy.base.windows import Window
from auto_easy.models import Box
from auto_easy.utils import logger


class WinShow(Window):
    def __init__(self, window_id=None, pic_save_dir=None):
        Window.__init__(self, window_id=window_id)
        self.pic_save_dir = pic_save_dir

    def show(self, boxes: list[Box] = None, title=''):
        img = self.capture_window()
        draw_img = draw_rectangles(img, boxes, use_name=True,title=title)
        draw_img.show()

    def save(self, prefix, img=None, time_suffix=True, ext='bmp', debug_print=True):
        if self.pic_save_dir is None:
            raise Exception('save_dir must be set')
        prefix = prefix.replace("\\", "").replace("/", "")
        target_dir = os.path.join(self.pic_save_dir, self.get_text())
        if not os.path.exists(target_dir):
            os.mkdir(target_dir)
        now = datetime.datetime.now()
        if time_suffix:
            file_time_str = now.strftime('%Y%m%d_%H%M%S_%f')[:-3]
            file_name = f'{prefix}_{file_time_str}.{ext}'
        else:
            file_name = f'{prefix}.{ext}'
        path = os.path.join(target_dir, file_name)
        if img is None:
            img = self.capture(latest_lag=3)
        img.save(path)
        if debug_print:
            logger.debug('save screenshot to: {}'.format(path))


if __name__ == '__main__':
    win = WinShow('Phone-VB')
    win.show([Box(10, 10, 100, 100)])
    win.pic_save_dir = '.'
    win.save('test', debug_print=True)

    # win.pic_dir = TestPicDir
    # start = time.time()
    # mdet = win.loop_find_pics('core/test_1', to=10, sleep=1)
    # mdet = win.find_pics('core/test_1')
    # print(mdet)
    # print(time.time() - start)

    # exists = win.exists_pics('core/test_1')
    # print(exists)

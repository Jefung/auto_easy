import os
import time

from auto_easy.base.find_pic import PicFactory
from auto_easy.base.find_pic.find_pic import find_pics_v2
from auto_easy.base.find_pic.model import MPicDetV2, PicDetConf, PicV2
from auto_easy.base.windows import Window
from auto_easy.constant import TestPicDir
from auto_easy.utils import Timeout


class PicLoopDetConf:
    def __init__(self):
        self.to = 1
        self.sleep = 0.1
        self.break_func = None
        self.loop_obj_func = None


class WinFindPic(Window, PicFactory):
    def __init__(self, window_id=None, pic_dir=None):
        Window.__init__(self, window_id=window_id)
        PicFactory.__init__(self, pic_dir=pic_dir)

    def _cvt_pic(self, pic):
        # 字符串,可能是具体文件路径或者图片名(指定目录下的)
        if isinstance(pic, str) and not os.path.isfile(pic):
            return self.get_pic(pic)  # 从图片工厂获取图片
        return PicV2.new_auto(pic)

    def _cvt_pics(self, pics) -> list[PicV2]:
        if not isinstance(pics, list):
            pics = [pics]
        ans = []
        for pic in pics:
            if isinstance(pic, str) and not os.path.isfile(pic):
                ans.extend(self.get_pics(pic))  # 实现一个图片名对应多张图片的逻辑
            else:
                ans.append(PicV2.new_auto(pic))
        return ans

    def debug_find_pics(self, src, pics, pic_det_conf: PicDetConf = None) -> MPicDetV2:
        screen_img = self.capture_window()
        source = self._cvt_pic(screen_img)
        searches = self._cvt_pics(pics)
        mdet = find_pics_v2(source, searches, pic_det_conf)
        mdet.merge_same_name(dedup=True)  # 相同图片名称的检测结果合并
        return mdet

    # @timeit_decorator
    def raw_find_pics(self, pics, pic_det_conf: PicDetConf) -> MPicDetV2:
        # 支持同个图片名对应多张图片
        screen_img = self.capture_window()
        source = self._cvt_pic(screen_img)
        searches = self._cvt_pics(pics)
        mdet = find_pics_v2(source, searches, pic_det_conf)
        mdet.merge_same_name(dedup=True)  # 相同图片名称的检测结果合并
        return mdet

    def find_pics(self, pics, pic_det_conf: PicDetConf = None) -> MPicDetV2:
        return self.raw_find_pics(pics, pic_det_conf)

    def find_pics_simple(self, pics, box=None, sim=None, rgb=None, scale=None, multi_match=None):
        conf = PicDetConf()
        if box is not None:
            conf.box = box
        if sim is not None:
            conf.sim = sim
        if rgb is not None:
            conf.rgb = rgb
        if scale is not None:
            conf.cur_scale = scale
        if multi_match is not None:
            conf.multi_match = multi_match
        return self.raw_find_pics(pics, conf)

    def exists_pics(self, pics) -> bool:
        pics = self._cvt_pics(pics)
        mdet = self.raw_find_pics(pics, pic_det_conf=None, pics_det_conf=None)
        return mdet.check(includes=pics)

    def loop_find_pics(self, pics, to=1, sleep=None, min_det_num=-1, det_conf: PicDetConf = None) -> MPicDetV2:
        if to <= 0:
            sleep = 0
        if sleep is None:
            sleep = to / 3  # 暂定按检测三次来算, sleep在[0.1,1]之间
            sleep = min(sleep, 2)  # 最长sleep时间1秒
            sleep = max(sleep, 0.2)  # 最短sleep时间
            # logger.debug('sleep %.2f', sleep)

        searches = self._cvt_pics(pics)
        to = Timeout(to)
        to_searches = searches
        while to.not_timeout():
            mdet = self.raw_find_pics(to_searches, det_conf)

            exists_name = mdet.get_output_exists_names()
            to_searches = [search for search in searches if search.name not in exists_name]
            if len(to_searches) == 0:
                break

            if min_det_num > 0 and len(exists_name) >= min_det_num:
                break
            time.sleep(sleep)
        return mdet

    def loop_find_pics_not_exists(self, pics, to=1, sleep=None, det_conf: PicDetConf = None) -> MPicDetV2:
        if to > 0 and sleep is None:
            sleep = to / 3  # 暂定按检测三次来算, sleep在[0.2,1]之间
            sleep = min(sleep, 1)  # 最长sleep时间1秒
            sleep = max(sleep, 0.2)  # 最短sleep时间

        searches = self._cvt_pics(pics)
        to = Timeout(to)
        mdet = MPicDetV2()
        to_searches = searches
        while to.not_timeout():
            print(to_searches)
            mdet = self.raw_find_pics(to_searches, det_conf)
            exists_name = mdet.get_output_exists_names()
            to_searches = [search for search in to_searches if search.name in exists_name]
            if len(to_searches) == 0:
                return mdet
            time.sleep(sleep)
        return mdet


if __name__ == '__main__':
    win = WinFindPic('Phone-VB')
    win.pic_dir = TestPicDir
    start = time.time()
    mdet = win.loop_find_pics('core/test_1', to=10, sleep=1)
    # mdet = win.find_pics('core/test_1')
    print(mdet)
    print(time.time() - start)

    # exists = win.exists_pics('core/test_1')
    # print(exists)

import copy
import hashlib
import os
import re

import PIL
import cv2
import numpy as np
from PIL import Image

from auto_easy.base.find_pic.conf_base import ConfBase
from auto_easy.base.image.draw import draw_rectangles
from auto_easy.constant import get_test_pic
from auto_easy.models import Box, sort_boxes_by_group, group_box

PicDetConf_box = None
PicDetConf_expand_scale = 3  # 匹配区域box缩放比例, 1表示不缩放, 2表示放大两倍
PicDetConf_multi_match = False  # 是否允许一张图片匹配多个
PicDetConf_multi_dedup = True  # 匹配多个的时候进行去重, 保留sim最高
PicDetConf_find_one = False  # 只返回一个
PicDetConf_color = ""  # 该参数如果设置了非空，会覆盖图片名称中的偏色
PicDetConf_contain_color = ""  # 该参数如果设置了非空，会覆盖图片名称中的偏色
PicDetConf_sim = 0.8
PicDetConf_range_scale = (0.95, 1.05, 0.01)  # 自动大小匹配, 左闭右闭区间, 格式 (start, end, step) , 例如(0.95, 1.1, 0.1)
PicDetConf_cur_scale = None
PicDetConf_rgb = True  # 是否在RPB模式下匹配
PicDetConf_bg_remove = False
PicDetConf_method = cv2.TM_CCOEFF_NORMED
PicDetConf_debug = False


class PicDetConf(ConfBase):
    def __init__(self):
        super().__init__()
        self._box: Box = PicDetConf_box  # 匹配区域, None/Box(0,0,0,0) 默认全屏
        self._expand_scale = PicDetConf_expand_scale  # 匹配区域box缩放比例, 1表示不缩放, 2表示放大两倍
        self._multi_match = PicDetConf_multi_match  # 是否允许一张图片匹配多个
        self._multi_dedup = PicDetConf_multi_dedup  # 匹配多个的时候进行去重, 保留sim最高
        self._find_one = PicDetConf_find_one  # 只返回一个
        self._color = PicDetConf_color  # 该参数如果设置了非空，会覆盖图片名称中的偏色
        self._contain_color = PicDetConf_contain_color  # 必须包含的颜色
        self._sim = PicDetConf_sim
        self._range_scale = PicDetConf_range_scale  # 自动大小匹配, 左闭右闭区间, 格式 (start, end, step) , 例如(0.95, 1.1, 0.1)
        self._cur_scale = PicDetConf_cur_scale
        self._rgb = PicDetConf_rgb  # 是否在RPB模式下匹配
        self._bg_remove = PicDetConf_bg_remove
        self._method = PicDetConf_method
        self._debug = PicDetConf_debug
        self._params = {}

    @property
    def cur_scale(self):
        return self._cur_scale

    @cur_scale.setter
    def cur_scale(self, value):
        self._cur_scale = float(value)

    @property
    def box(self):
        return self._box

    @property
    def scaled_box(self):
        if self.box is None:
            return None
        origin_box = self.box
        if self.expand_scale is not None and self.expand_scale != 1:
            scaled_box = self._box.copy_by_scale(self.expand_scale)
            return scaled_box
        return origin_box

    @box.setter
    def box(self, v):
        if v is None:
            self._box = None
            return
        if isinstance(v, Box):
            self._box = v
            return
        if isinstance(v, str):
            s = v
            if len(s) == 0:
                self._box = None
                return
            ls = s.split(',')
            if len(ls) >= 4:
                self._box = Box(ls[0], ls[1], ls[2], ls[3])
                return
        raise Exception('invalid box, {}'.format(v))

    @property
    def expand_scale(self):
        return self._expand_scale

    @expand_scale.setter
    def expand_scale(self, v):
        self._expand_scale = int(v)

    @property
    def multi_match(self):
        return self._multi_match

    @multi_match.setter
    def multi_match(self, v):
        self._multi_match = self._cvt_bool(v)

    @property
    def find_one(self):
        return self._find_one

    @find_one.setter
    def find_one(self, v):
        self._find_one = self._cvt_bool(v)
        if self._find_one is None:
            raise Exception('invalid find one, {}'.format(v))

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, v):
        self._color = str(v)

    @property
    def contain_color(self):
        return self._contain_color

    @contain_color.setter
    def contain_color(self, v):
        self._contain_color = str(v)

    @property
    def sim(self):
        return self._sim

    @sim.setter
    def sim(self, v):
        self._sim = float(v)
        if not (0 <= self._sim <= 1):
            raise Exception('invalid sim, {}'.format(v))

    @property
    def range_scale(self):
        return self._range_scale

    @range_scale.setter
    def range_scale(self, v):
        self._range_scale = None
        if v is None:
            return
        if isinstance(v, tuple) and len(v) == 3:
            self._range_scale = (float(v[0]), float(v[1]), float(v[2]))

        if isinstance(v, str):
            if len(v) == 0:
                self._range_scale = (1, 1, 0)
            ls = v.split(',')
            if len(ls) == 3:
                self._range_scale = (float(ls[0]), float(ls[1]), float(ls[2]))

        if self._range_scale is None:
            raise Exception('invalid range_scale, {}'.format(v))

        if self._range_scale[0] > self._range_scale[1] or self._range_scale[1] - self._range_scale[0] < \
                self._range_scale[2]:
            raise Exception('invalid range_scale, {}'.format(v))
        # print(self._range_scale)

    @property
    def rgb(self):
        return self._rgb

    @rgb.setter
    def rgb(self, v):
        self._rgb = self._cvt_bool(v)
        if self._rgb is None:
            raise Exception('invalid rgb, {}'.format(v))

    @property
    def bg_remove(self):
        return self._bg_remove

    @bg_remove.setter
    def bg_remove(self, v):
        self._bg_remove = self._cvt_bool(v)

    @property
    def method(self):
        return self._method

    @method.setter
    def method(self, v):
        _method = int(v)
        template_matching_methods = [
            cv2.TM_SQDIFF,
            cv2.TM_SQDIFF_NORMED,
            cv2.TM_CCORR,
            cv2.TM_CCORR_NORMED,
            cv2.TM_CCOEFF,
            cv2.TM_CCOEFF_NORMED
        ]
        if _method not in template_matching_methods:
            raise Exception('invalid method, {}'.format(v))
        self._method = _method

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, v):
        self._debug = bool(v)

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, v):
        self._params = v

    def _cvt_bool(self, v):
        if isinstance(v, bool):
            return v
        if v in ['True', 'true', '1']:
            return True
        if v in ['False', 'false', '0']:
            return False
        raise Exception('invalid cvt_bool, {}'.format(v))

    def update_with_kv_str(self, kv_str: str):
        # kv_str例子: box=0,0,1,1&sim=0.8
        items = kv_str.split('&')
        params = {}
        for item in items:
            key, value = item.split('=')
            params[key] = value
            if not hasattr(PicDetConf, key):
                continue
            if isinstance(getattr(PicDetConf, key), property):
                setattr(self, key, value)
        setattr(self, 'params', params)

    def deepcopy(self):
        obj = copy.deepcopy(self)
        return obj


class PicV2:
    def __init__(self, name='', path='', pil_img=None, cv2_img=None, det_conf: PicDetConf = None):

        self.pil_img_rgb = None
        self.cv2_img_bgr = None
        # 产出图片数据
        if path != '':
            self._is_image(path)
            self.pil_img_rgb = Image.open(path)
            # cv2 imread不支持中文路径, 通过pil转化
            self.cv2_img_bgr = cv2.cvtColor(np.array(self.pil_img_rgb), cv2.COLOR_RGB2BGR)
        elif pil_img is not None:
            self.pil_img_rgb = pil_img
            self.cv2_img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        elif cv2_img is not None:
            self.cv2_img_bgr = cv2_img
            self.pil_img_rgb = Image.fromarray(cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB))
        else:
            raise Exception('path or pil_img or cv2_img are required')

        self.path = path
        self.name = ''  # 优先级: name > path > image.sha256
        if name != '':
            self.name = name
        elif path != '':
            self.name = path
        else:
            hasher = hashlib.sha256()
            hasher.update(self.cv2_img_bgr)
            self.name = hasher.hexdigest()

        base_conf = PicDetConf()  # 默认配置
        file_conf = PicDetConf()  # 文件名中的配置
        user_conf = det_conf  # 用户传入的配置
        if path != '':
            file_name_without_extension = os.path.splitext(os.path.basename(path))[0]
            ls = file_name_without_extension.split('$$$')
            if len(ls) < 1:
                raise Exception('invalid path, {}'.format(path))
            if len(ls) > 1:
                file_conf.update_with_kv_str(ls[1])
        self.det_conf = ConfBase.new_conf_by_pry([base_conf, file_conf, user_conf])  # 按低优到高优进行配置覆盖

    def _is_image(self, path) -> bool:
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        try:
            img = Image.open(path)  # 尝试打开图像文件
            img.verify()  # 验证文件是否损坏
            return True
        except (IOError, SyntaxError):  # PIL无法识别的文件类型会抛出IOError
            raise Exception('path exists, but file is not image, {}'.format(path))

    def deepcopy(self):
        obj = copy.deepcopy(self)
        return obj

    @staticmethod
    def new_auto(v, name=''):
        if isinstance(v, PicV2):
            return v

        # 传入文件路径
        if isinstance(v, str):
            return PicV2(name=name, path=v)

        # 传入PIL.Image
        if isinstance(v, PIL.Image.Image):
            return PicV2(name=name, pil_img=v)

        # 传入cv2的ndarray
        if isinstance(v, np.ndarray):
            return PicV2(name=name, cv2_img=v)
        raise Exception(
            'Piv new_auto only support str/PIL.Image.Image/np.ndarray, input: {}, type: {}'.format(v, type(v)))

    def __str__(self):
        return self.path

    def show(self, boxes=None):
        draw_img = self.pil_img_rgb
        if boxes:
            draw_img = draw_rectangles(self.pil_img_rgb, boxes=boxes)
        draw_img.show()


class DetBox(Box):
    def __init__(self, sim, x1, y1, x2, y2, name=''):
        super().__init__(x1, y1, x2, y2, name)
        self.sim = float(sim)
        self.parent_name = ''

    @staticmethod
    def new_det_boxes_by_str(s):
        # 使用正则表达式提取<x1,y1,x2,y2>
        pattern = r'(\d+\.\d+)<(\d+),(\d+),(\d+),(\d+)>'
        matches = re.findall(pattern, s)
        # 打印提取的坐标
        boxes = []
        for match in matches:
            score, x1, y1, x2, y2 = match
            boxes.append(DetBox(score, x1, y1, x2, y2, str(score)))
        return boxes

    def __str__(self):
        return f'{self.sim}<{self.x1},{self.y1},{self.x2},{self.y2}>'


class PicDetV2:
    def __init__(self, pic: PicV2, det_boxes: list[DetBox] = None, scale=1):
        self.pic = pic
        self.scale = scale
        self.boxes: list[DetBox] = []
        self.add_boxes(det_boxes)
        # self.boxes = det_boxes if det_boxes is not None else []

    def replace_boxes(self, det_boxes: list[DetBox]):
        self.boxes = []
        self.add_boxes(det_boxes)

    def add_box(self, det_box: DetBox):
        det_box.parent_name = self.pic.name
        self.boxes.append(det_box)


    def add_boxes(self, det_boxes: list[DetBox]):
        for box in det_boxes:
            self.add_box(box)
        self.boxes = sorted(self.boxes, key=lambda box: box.sim, reverse=True)

    @property
    def is_detected(self):
        return len(self.boxes) > 0

    @property
    def box(self):
        if self.boxes:
            return self.boxes[0]
        return None

    def get_boxes(self, sort_mode=0, dis_err=10):
        # 默认按置信度排序
        if sort_mode == 0:
            return self.boxes
        if sort_mode == 1:
            return sort_boxes_by_group(self.boxes, dis_err=dis_err)
        raise Exception('sort_mode must be 0 or 1')

    def get_boxes_group(self, dis_err):
        boxes = self.boxes
        return sort_boxes_by_group(boxes, dis_err=dis_err)

    def group_boxes(self, dis_err) -> list[list[Box]]:
        boxes = self.boxes
        return group_box(boxes, dis_err=dis_err)

    def __str__(self):
        str_list = []
        for box in self.boxes:
            str_list.append(f'{box}')

        s = '|'.join(str_list)
        if len(self.pic.name) > 0:
            s = f'{self.pic.name}:{s}'
        return s

    def merge_other(self, other, dedup=False):
        if len(other.boxes) == 0:
            return
        self.add_boxes(other.boxes)
        if dedup:
            self.boxes = nms_boxes(self.boxes)

    def merge_others(self, others, dedup=False):
        for other in others:
            self.merge_other(other, dedup)


def nms_boxes(det_boxes):
    # 准备进行非极大值抑制
    boxes = np.array([(box.x1, box.y1, box.width, box.height) for box in det_boxes])
    scores = np.array([box.sim for box in det_boxes])

    # 执行非极大值抑制
    indices = cv2.dnn.NMSBoxes(boxes.tolist(), scores.tolist(), score_threshold=0.5, nms_threshold=0.1)

    # 存储经过 NMS 处理后的匹配结果
    filter_boxes = [det_boxes[i] for i in indices]
    return filter_boxes


class MPicDetV2:
    def __init__(self, pic_det_list: list[PicDetV2] = None):
        self.pic_det_list = pic_det_list if pic_det_list is not None else []

    @property
    def first_det(self) -> PicDetV2:
        res = None
        for det in self.pic_det_list:
            if det.is_detected:
                if res is None:
                    res = det
                else:
                    if det.box.sim > res.box.sim:
                        res = det
        return res

    def filter_not_top1_det(self):
        top1_det = self.first_det
        if top1_det is None:
            self.pic_det_list = []
        else:
            self.pic_det_list = [top1_det]

    @property
    def is_detected(self) -> bool:
        for pic_det in self.pic_det_list:
            if pic_det.is_detected:
                return True
        return False

    @property
    def all_detected(self):
        for det in self.pic_det_list:
            if not det.is_detected:
                return False
        return True

    @property
    def boxes(self) -> list[DetBox]:
        _boxes = []
        for pic_det in self.pic_det_list:
            _boxes += pic_det.boxes
        return _boxes

    def get_boxes(self, pic=None, sort_mode=0, dis_err=10) -> list[DetBox]:
        boxes = self.boxes
        # todo: 支持指定具体的图片

        # 默认按置信度排序
        if sort_mode == 0:
            return sorted(self.boxes, key=lambda box: box.sim, reverse=True)

        if sort_mode == 1:
            return sort_boxes_by_group(boxes, dis_err=dis_err)

    @property
    def box(self) -> DetBox:
        _boxes = self.boxes
        if len(_boxes) == 0:
            return None
        return _boxes[0]

    def get_output_exists_names(self):
        return [det.pic.name for det in self.pic_det_list if det.is_detected]

    def merge_other(self, other, dedup=False):
        for det in other.pic_det_list:
            if dedup and self.get(det.pic.name):
                self.get(det.pic.name).merge_other(det, dedup)
            else:
                self.pic_det_list.append(det)

    def merge_others(self, others):
        for other in others:
            self.merge_other(other.pic_det_list)

    def get(self, name):
        for det in self.pic_det_list:
            if det.pic.name == name:
                return det
        return None

    def check(self, includes=None, excludes=None):
        includes = includes if includes is not None else []
        excludes = excludes if excludes is not None else []
        if not isinstance(includes, list):
            includes = [includes]

        for name in includes:
            det = self.get(name)
            if det is None or not det.is_detected:
                return False

        for name in excludes:
            det = self.get(name)
            if det is not None and det.is_detected:
                return False

        return True

    def merge_same_name(self, dedup=True):
        new_det_dict = {}
        for det in self.pic_det_list:
            if det.pic.name in new_det_dict.keys():
                new_det_dict[det.pic.name].merge_other(det, dedup)
            else:
                new_det_dict[det.pic.name] = det
        self.pic_det_list = list(new_det_dict.values())

    def filter_overlap(self):
        boxes = self.boxes
        boxes = nms_boxes(boxes)
        boxes_id = [id(box) for box in boxes]
        for det in self.pic_det_list:
            det_boxes = det.boxes
            filter_boxes = [box for box in det_boxes if id(box) in boxes_id]
            det.replace_boxes(filter_boxes)

    def print_exists_results(self):
        str_list = []
        for det in self.pic_det_list:
            if det.is_detected:
                str_list.append(det.__str__())
        return ';'.join(str_list)

    def __str__(self):
        str_list = []
        for det in self.pic_det_list:
            str_list.append(det.__str__())
        return ';'.join(str_list)


if __name__ == '__main__':
    # 从图片文件初始化
    path1 = get_test_pic('find_pic/search_pic_1$$$box=778,381,812,416.bmp')
    pic = PicV2.new_auto(path1, name='case1')
    print(pic.det_conf.__dict__)
    print(pic.name)

    # path2 = get_test_pic('find_pic/search_pic_2.bmp')
    # pic2 = PicV2.new_auto(path2, name='case2')
    # print(pic2.name)
    #
    # # 从cv2对象和PIL对象初始化
    # path3 = get_test_pic('find_pic/search_pic_1$$$box=778,381,812,416.bmp')
    # pil_img = Image.open(path3)
    # cv2_img = cv2.imread(path3)
    #
    # pic_from_cv2 = PicV2.new_auto(cv2_img)
    # pic_from_pil = PicV2.new_auto(pil_img)
    # print(pic_from_cv2.name)
    # print(pic_from_pil.name)
    # # pic3.show()
    # # pic4.show()
    #
    # if ImageChops.difference(pic_from_cv2.pil_img_rgb, pic_from_pil.pil_img_rgb).getbbox():
    #     print('pic3.pil_img_rgb != pic4.pil_img_rgb')
    #
    # if not np.array_equal(pic_from_cv2.cv2_img_bgr, pic_from_pil.cv2_img_bgr):
    #     print('pic3.pil_img_rgb != pic4.pil_img_rgb')

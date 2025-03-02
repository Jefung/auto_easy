import time
from typing import List

from auto_easy.models import Box, sort_and_group_points


class Pic:
    def __init__(self, path):
        self.path = path  # 完整文件路径
        self.name = ""  # 文件名
        self.name_final = ""  # 文件名中最后的名称
        self.cut_box = None  # 游戏截图区域
        self.click_area_rate = None  # 点击区域,百分比,如(0.5,0.5,1,1)
        self.delta_color = ''
        self.width = 0  # 宽
        self.height = 0  #
        self.params = {}
        self.pil_img = None
        self.ndarray_obj = None
        self.sim = -1

    def is_same(self, name) -> bool:
        return self.name == name

    def gen_click_box(self, match_box: Box):
        if not self.click_area_rate:
            return match_box
        new_box = match_box.crop_by_rate(self.click_area_rate[0], self.click_area_rate[1],
                                         self.click_area_rate[2], self.click_area_rate[3])
        return new_box

    def __str__(self):
        return '{}{}'.format(self.name, self.cut_box)


class PicDet:
    def __init__(self, pic: Pic, boxes: List[Box]):
        self.pic = pic
        self.is_detected = False
        self.match_boxes = []
        self.ts = time.time()
        self.add_boxes(boxes)

    @property
    def match_box_first(self) -> Box:
        return self.match_boxes[0]

    def replace_boxes(self, boxes: List[Box]):
        self.match_boxes = boxes
        self.is_detected = len(self.match_boxes) > 0

    # TODO： 待廢棄
    def add_boxes(self, boxes: List[Box]):
        self.match_boxes += boxes
        self.is_detected = len(self.match_boxes) > 0

    def get_boxes(self, dir=1, dis_err=20):
        # TODO: 支持按不同顺序排序, 现在默认是从左往右，从上往下
        points = [box.tl_point for box in self.match_boxes]
        sorted_points = sort_and_group_points(points, dis_err=dis_err)
        # points的顺序映射到box的顺序
        boxes = []
        for point in sorted_points:
            for box in self.match_boxes:
                if id(box.tl_point) == id(point):
                    boxes.append(box)

        return boxes

    def get_click_box(self):
        if not self.is_detected:
            return None
        box = self.match_box_first
        box = self.pic.gen_click_box(box)  # 图片有参数可以指定点击区域
        return box

    def __str__(self):
        return '{}：{}'.format(self.pic.name, '|'.join([str(box) for box in self.match_boxes]))


class MPicDet:
    def __init__(self, pics_det: List[PicDet] = []):
        self.results = pics_det
        # self.is_detected = len(pics_det) > 0
        self.create_ts = time.time()

    @property
    def is_detected(self):
        for det in self.results:
            if det.is_detected:
                return True
        return False

    def get_output_exists_names(self) -> list[str]:
        ans = []
        for det in self.results:
            if det.is_detected:
                ans.append(det.pic.name)
        return ans

    def get_output_first(self) -> PicDet:
        for det in self.results:
            if det.is_detected:
                return det

    def exists_inputs(self, names: list[str]) -> bool:
        names = names if isinstance(names, list) else [names]
        for name in names:
            det = self.get(name)
            if det is None:
                return False
        return True

    def get(self, name) -> PicDet:
        for v in self.results:
            if v.pic.is_same(name):
                return v
        return None

    def get_box(self, name) -> Box:
        return self.get(name).match_box_first

    def exists_output(self, names: list[str]) -> bool:
        if not self.is_detected:
            return False
        names = names if isinstance(names, list) else [names]
        for name in names:
            det = self.get(name)
            if det is None or det.is_detected == False:
                return False
        return True

    def not_exists_output(self, names: list) -> bool:
        if not self.is_detected:
            return True
        names = names if isinstance(names, list) else [names]
        for name in names:
            det = self.get(name)
            if det is not None and det.is_detected:
                return False
        return True

    def merge_other(self, other):
        assert isinstance(other, MPicDet)
        for other_det in other.results:
            old_det = self.get(other_det.pic.name)

            if old_det is None:
                self.results.append(other_det)
            else:
                old_det.replace_boxes(other_det.match_boxes)

    def merge_others(self, others):
        assert isinstance(others, list)
        for other in others:
            self.merge_other(other)

    def add_pics_det(self, pics_det: List[PicDet]):
        if isinstance(pics_det, MPicDet):
            pics_det = pics_det.results

        for new_det in pics_det:
            old_det = self.get(new_det.pic.name)
            if old_det is None:
                self.results.append(new_det)
            else:
                old_det.add_boxes(new_det.match_boxes)

    def print_results(self):
        tmp = [str(pic) for pic in self.results]
        return '|'.join(tmp)

    def print_exists_results(self):
        tmp = []
        for det in self.results:
            if det.is_detected:
                tmp.append(str(det))
        return '|'.join(tmp)

    def get_all_boxes(self):
        boxes = []
        for v in self.results:
            boxes = boxes + v.match_boxes
        return boxes

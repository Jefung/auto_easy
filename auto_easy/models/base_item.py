import datetime
import time
from typing import Type

from auto_easy.models.geometry import *


class ItemT(Enum):
    Default = "默认"
    Role = "角色"
    GuidePost = "路标"
    Monster = "怪物"
    Goods = "物品"


class YoloItem:
    def __init__(self, name, score, match_box, src_box):
        self.params_list = [name, score, match_box, src_box]
        self.name = name
        self.score = score
        self.box: Box = match_box
        self.src_box = src_box
        self.mock = False
        self.mock_mid_point = Point(0, 0)

    # 默认返回识别区域中心点，派生类可以覆盖
    @property
    def middle_point(self) -> Point:
        if self.mock:
            return self.mock_mid_point
        return self.box.get_mid_point()

    @property
    def itype(self):
        return ItemT.Default

    def __str__(self):
        return "name({})-type({})-class({})-mid_point({})".format(self.name, self.itype.value,
                                                                  self.__class__.__name__,
                                                                  str(self.middle_point))

    def cal_farthest(self, items):
        target = items[0]
        max_dis = self.middle_point.get_distance(items[0].middle_point)
        for item in items:
            dis = self.middle_point.get_distance(item.middle_point)
            if max_dis < dis:
                target = item
                max_dis = dis
        return target

    def cal_closest(self, items):
        target = items[0]
        min_dis = self.middle_point.get_distance(items[0].middle_point)
        for item in items:
            dis = self.middle_point.get_distance(item.middle_point)
            if min_dis > dis:
                target = item
                min_dis = dis
        return target

    def cal_left(self, items):
        res = []
        for item in items:
            if item.middle_point.x <= self.middle_point.x:
                res.append(item)
        return res

    def cal_right(self, items):
        res = []
        for item in items:
            if item.middle_point.x > self.middle_point.x:
                res.append(item)
        return res

    def move(self, x, y):
        self.box.move(x, y)

    def is_class(self, cls: type):
        if not isinstance(cls, type):
            raise Exception('AIItemBase.isinstance cls must class type')
        mro_list = self.__class__.__mro__
        mro_name_list = [c.__name__ for c in mro_list]
        return cls.__name__ in mro_name_list

    def in_classes(self, cls_list: List[type]):
        for cls in cls_list:
            if self.is_class(cls):
                return True
        return False

    @staticmethod
    def can_new_obj(input: str) -> bool:
        return True


class MYoloItem:
    def __init__(self, items: list[YoloItem], model_name=''):
        self.model_name = model_name
        self.items = items
        self.create_ts = time.time()

    @property
    def is_detected(self):
        return len(self.items) > 0

    def cal_item_cnt(self, name):
        return len(self.get_items_by_name(name))

    def contain_item(self, name):
        return len(self.get_items_by_name(name)) > 0

    def exists_type(self, itype: ItemT) -> bool:
        return len(self.get_items_by_type(itype)) > 0

    def exists_types(self, itypes: list[ItemT]) -> bool:
        flag = True
        for t in itypes:
            if len(self.get_items_by_type(t)) == 0:
                flag = False
        return flag

    def check(self, include=[], exclude=[]):
        cls_include = []
        type_include = []
        for v in include:
            if isinstance(v, ItemT):
                type_include.append(v)
            elif isinstance(v, type):
                cls_include.append(v)
            else:
                raise Exception(f'only check cls/type, include: {include}')
        if len(type_include) > 0 and not self.exists_types(type_include):
            return False
        if len(cls_include) > 0 and not self.exists_cls_list(cls_include):
            return False

        cls_exclude = []
        type_exclude = []
        for v in exclude:
            if isinstance(v, ItemT):
                type_exclude.append(v)
            elif isinstance(v, type):
                cls_exclude.append(v)
            else:
                raise Exception(f'only check cls/type, include: {exclude}')
        if len(cls_exclude) > 0 and self.exists_cls_list(cls_exclude, min_num=1):
            return False

        if len(type_exclude) > 0 and len(self.get_items_by_types(type_exclude)) > 0:
            return False
        return True

    def exists_cls(self, cls: type) -> bool:
        return self.get_item_by_cls(cls) is not None

    def exists_cls_list(self, cls_list: list[type], min_num=-1) -> bool:
        cnt = 0
        for cls in cls_list:
            if not self.exists_cls(cls):
                return False
            cnt += 1
            if min_num > 0 and cnt >= min_num:
                return True
        return True

    def get_item_by_cls(self, cls: type) -> YoloItem:
        ls = self.get_items_by_cls(cls)
        return ls[0] if len(ls) > 0 else None

    def get_item_by_cls_list(self, order_cls_list: list[type]) -> YoloItem:
        for cls in order_cls_list:
            item = self.get_item_by_cls(cls)
            if item is not None:
                return item
        return None

    def get_items_by_cls(self, cls: type) -> list[YoloItem]:
        ls = []
        for item in self.items:
            if item.is_class(cls):
                ls.append(item)
        return ls

    def get_items_by_types(self, itype_list: list[ItemT]) -> list[YoloItem]:
        ls = []
        for item in self.items:
            if item.itype in itype_list:
                ls.append(item)
        return ls

    def get_items_by_type(self, itype: ItemT) -> list[YoloItem]:
        ls = []
        for item in self.items:
            if item.itype == itype:
                ls.append(item)
        return ls

    def get_items_by_name(self, name) -> list[YoloItem]:
        if name == '':
            return self.items
        ls = []
        for item in self.items:
            if item.name == name:
                ls.append(item)
        return ls

    def get_item_by_type(self, itype: ItemT, cls_order_list: list[Type] = None) -> YoloItem:
        items = self.get_items_by_type(itype)
        if len(items) == 0:
            return None

        if cls_order_list is not None:
            for cls in cls_order_list:
                for item in items:
                    if isinstance(item, cls):
                        return item
        return items[0]

    def get_item_by_name(self, name) -> YoloItem:
        items = self.get_items_by_name(name)
        if len(items) == 0:
            return None
        return items[0]

    def get_item_types(self) -> list[ItemT]:
        ts = {}
        for item in self.items:
            ts[item.itype] = 0
        return ts.keys()

    def get_items_name(self) -> list[str]:
        set_val = set()
        for item in self.items:
            set_val.add(str(item.itype.value))
        return list(sorted(set_val))

    def __str__(self):
        ls = []
        for item in self.items:
            ls.append(str(item))
        ts_format = datetime.datetime.fromtimestamp(self.create_ts)
        return 'model[{}], time[{}]: '.format(self.model_name, ts_format) + ';'.join(ls)

    def print_simple_info(self):
        ls = []
        for item in self.items:
            ls.append('{}{}'.format(item.name, item.middle_point))
        return '|'.join(sorted(ls))

    def print_info(self):
        ls = []
        for item in self.items:
            ls.append('{}&{}&{}'.format(item.name, item.middle_point, item.box))
        return ';'.join(sorted(ls))


def cvt_items2points(items: list[YoloItem]) -> list[Point]:
    points = []
    for item in items:
        points.append(item.middle_point)
    return points


def cnt_point(points, f) -> int:
    cnt = 0
    for point in points:
        if f(point):
            cnt += 1
    return cnt


if __name__ == '__main__':
    pass
    # # cnt_point(points, lambda point: point.x > role.middle_point.x)
    # s = "哥布林,0.869,819,120,54,86|人物,0.741,521,293,15,20|哥布林,0.636,59,128,53,96"
    # s = "路标-移动,0.923,882,216,44,26|路标-三角,0.854,579,303,24,18|路标-三角,0.835,491,305,24,15|人物-叶子,0.822,180,158,20,21|人物-黑钻,0.801,156,161,18,17|建筑-小桥,0.785,254,266,425,74|路标-三角,0.771,764,305,21,14|路标-三角,0.751,308,305,21,15|路标-三角,0.750,398,305,24,15|路标-三角,0.684,947,305,14,14|物品-白色物品,0.631,791,222,54,18|路标-三角,0.607,672,306,20,12|人物-工会图标,0.606,54,162,15,12"
    # items = new_ai_base_item(s)
    #
    # res = AIResult(items, s)
    # print(res)
    #
    # print(check_distance([
    #     Point(494, 292),
    #     Point(494, 290),
    #     Point(385, 365),
    # ], user_max_x=20, user_max_y=20))

    # items = res.get_items_by_name('')
    # target = AIItemBase('t', 0.9, 820, 120, 55, 86)
    # closest = find_closest_point(items,target)
    # print( closest.name, closest.score)
    #
    # p1 = Point(400,600,'')
    # p2 = Point(800,1200,'')
    # print(gen_move_target_point(p1, p2).x)

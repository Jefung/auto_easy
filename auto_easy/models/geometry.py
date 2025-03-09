import math
import random
import re
import sys
from enum import Enum
from typing import List


class Direction(Enum):
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class Point:
    def __init__(self, x, y, name=None):
        self.name = name if name is not None else ''
        self._x = 0
        self._y = 0
        self.x = x
        self.y = y

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = int(value)

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = int(value)

    def __str__(self):
        return "{}<{},{}>".format(self.name, self.x, self.y)

    def is_nearby(self, p, x_radius=30, y_radius=30):
        return abs(self.x - p.x) <= x_radius and abs(self.y - p.y) <= y_radius

    def is_nearby_with_points(self, points, x_radius=30, y_radius=30):
        for p in points:
            if self.is_nearby(p, x_radius, y_radius):
                return True
        return False


    def get_distance(self, p):
        dx = self.x - p.x
        dy = self.y - p.y
        return int(math.sqrt(dx ** 2 + dy ** 2))

    def calculate_angle(self, p):
        dx = p.x - self.x
        dy = p.y - self.y
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        if angle_deg < 0:
            return angle_deg + 360
        else:
            return angle_deg

    def on_other_left(self, p):
        return self.x < p.x

    def on_other_right(self, p):
        return not self.on_other_left(p)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def gen_point(self, x, y, max_x=-1, max_y=-1):
        p = Point(max(self.x + x, 0), max(self.y + y, 0))
        if max_x > 0:
            p.x = min(p.x, max_x)
        if max_y > 0:
            p.y = min(p.y, max_y)
        return p

    def move_x(self, dis, min_x=0, max_x=-1):
        self.x += dis
        if min_x >= 0:
            self.x = max(self.x, min_x)
        if max_x > 0:
            self.x = min(self.x, max_x)

    def tuple(self):
        return (self.x, self.y)


def check_distance(points: List[Point], user_max_x: float, user_max_y: float):
    """
    判断给定数组内所有元素的最大x轴距离和最大y轴距离是否分别小于max_x和max_y

    :param points: 包含Point对象的列表，代表坐标点集合
    :param max_x: x轴距离的最大值限制
    :param max_y: y轴距离的最大值限制
    :return: 如果满足条件返回True，否则返回False
    """
    if not points:
        return True
    min_x = max_x = points[0].x
    min_y = max_y = points[0].y
    for point in points[1:]:
        min_x = min(min_x, point.x)
        max_x = max(max_x, point.x)
        min_y = min(min_y, point.y)
        max_y = max(max_y, point.y)
    return (max_x - min_x) < user_max_x and (max_y - min_y) < user_max_y


def points_2_str(points) -> str:
    ls = [point.__str__() for point in points]

    return '|'.join(ls)


def group_points(points, dis_err) -> str:
    # 按照横坐标x进行升序排序（从左往右），如果x相同则按照纵坐标y升序排序（从上往下）
    sorted_points = sorted(points, key=lambda p: (p.y, p.x))

    # 用于存储分组后的结果（同一行或同一列的点为一组）
    groups = []
    current_group = []

    for i in range(len(sorted_points)):
        current_group.append(sorted_points[i])
        if i < len(sorted_points) - 1:
            next_point = sorted_points[i + 1]
            # 判断是否在同一列（横坐标距离在dis_err以内）
            if abs(next_point.y - current_group[0].y) <= dis_err:
                continue
            else:
                # 如果既不在同一行也不在同一列，当前组结束，添加到分组结果中并开启新组
                current_group = sorted(current_group, key=lambda p: p.x)
                groups.append(current_group)
                current_group = []
    # 添加最后一组（循环结束后最后一组还未添加）
    if current_group:
        current_group = sorted(current_group, key=lambda p: p.x)
        groups.append(current_group)
    return groups


def sort_and_group_points(points: List[Point], dis_err):
    groups = group_points(points, dis_err)
    merged_list = [element for sublist in groups for element in sublist]
    return merged_list


class Box:
    def __init__(self, tl_x, tl_y, rd_x, rd_y, name=""):
        tl_x, tl_y, rd_x, rd_y = int(tl_x), int(tl_y), int(rd_x), int(rd_y)
        if tl_x > rd_x or tl_y > rd_y:
            raise Exception(
                f"配置有问题，边框左上角和右下角信息错误, {tl_x}, {tl_y}, {rd_x}, {rd_y}, {name}; {tl_x > rd_x},{tl_y > rd_y}")
        self.name = name
        self.tl_point = Point(tl_x, tl_y, 'left_top')
        self.rd_point = Point(rd_x, rd_y, 'right_low')

    # 生成点，已左上角为起点，通过宽度和高度的比例
    def get_inner_point(self, width_rate=0.5, height_rate=0.5) -> Point:
        x = self.tl_point.x + (self.rd_point.x - self.tl_point.x) * width_rate
        y = self.tl_point.y + (self.rd_point.y - self.tl_point.y) * height_rate
        return Point(x, y)

    def get_mid_point(self, offset_rate=0) -> Point:
        w_rand = random.uniform(-offset_rate, offset_rate)
        h_rand = random.uniform(-offset_rate, offset_rate)
        return self.get_inner_point(0.5 + w_rand, 0.5 + h_rand)

    def get_rand_point(self):
        return self.get_inner_point(
            width_rate=random.uniform(0, 1),
            height_rate=random.uniform(0, 1),
        )

    def get_dis_to_center(self) -> int:
        mid_point = self.get_mid_point()
        return self.tl_point.get_distance(mid_point)

    def is_overlap(self, other) -> bool:
        """
        判断当前 Box 是否与另一 Box 重叠。
        :param other: 另一个 Box 对象
        :return: 如果重叠返回 True，否则返回 False
        """
        # 不重叠条件
        # A的右边在B的左边的左侧。
        # A的左边在B的右边的右侧。
        # A的底边在B的顶部的上方。
        # A的顶部在B的底边的下方
        # 检查是否不重叠
        if (self.x1 >= other.x2 or self.x2 <= other.x1 or
                self.y1 >= other.y2 or self.y2 <= other.y1):
            return False  # 不重叠

        return True  # 重叠

    def move(self, x, y):
        self.tl_point.x += x
        self.tl_point.y += y
        self.rd_point.x += x
        self.rd_point.y += y
        self.fix_overflow()

    def copy(self, x=0, y=0):
        new_box = Box(
            self.tl_point.x + x,
            self.tl_point.y + y,
            self.rd_point.x + x,
            self.rd_point.y + y,
            '')
        new_box.fix_overflow()
        return new_box

    def crop_by_rate(self, x1_r, y1_r, x2_r, y2_r):
        new_box = self.copy()
        new_box.tl_point.x += self.width * x1_r
        new_box.tl_point.y += self.height * y1_r
        new_box.rd_point.x -= self.width * (1 - x2_r)
        new_box.rd_point.y -= self.height * (1 - y2_r)
        new_box.fix_overflow()
        return new_box

    def copy_by_scale(self, scale):
        new_box = self.copy()
        new_box.tl_point.x += self.width * (1 - scale)
        new_box.tl_point.y += self.height * (1 - scale)
        new_box.rd_point.x -= self.width * (1 - scale)
        new_box.rd_point.y -= self.height * (1 - scale)
        new_box.fix_overflow()
        return new_box

    def fix_overflow(self, max_y=sys.maxsize, max_x=sys.maxsize):
        def _fix(cur_val, max_val):
            if cur_val < 0:
                return 0
            if cur_val > max_val:
                return max_val
            return cur_val

        self.tl_point.x = _fix(self.tl_point.x, max_x)
        self.tl_point.y = _fix(self.tl_point.y, max_y)
        self.rd_point.x = _fix(self.rd_point.x, max_x)
        self.rd_point.y = _fix(self.rd_point.y, max_y)

    def get_mid_dis(self, other):
        p1 = self.get_mid_point()
        p2 = other.get_mid_point()
        return p1.get_distance(p2)

    @property
    def x1(self):
        return self.tl_point.x

    @property
    def y1(self):
        return self.tl_point.y

    @property
    def x2(self):
        return self.rd_point.x

    @property
    def y2(self):
        return self.rd_point.y

    @property
    def area(self):
        return self.width * self.height

    @property
    def width(self):
        return self.x2 - self.x1

    @property
    def height(self):
        return self.y2 - self.y1

    def tuple(self):
        return (self.x1, self.y1, self.x2, self.y2)

    def is_empty(self):
        return self.width == 0 and self.height == 0

    @staticmethod
    def new_boxes_by_str(s):
        # 使用正则表达式提取<x1,y1,x2,y2>
        pattern = r'<(\d+),(\d+),(\d+),(\d+)>'
        matches = re.findall(pattern, s)
        # 打印提取的坐标
        boxes = []
        for match in matches:
            x1, y1, x2, y2 = match
            boxes.append(Box(x1, y1, x2, y2))
        return boxes

    def __str__(self):
        return "<{},{},{},{}>".format(self.tl_point.x, self.tl_point.y, self.rd_point.x, self.rd_point.y)

    def __eq__(self, other):
        if isinstance(other, Box):
            # 都为None的情况
            if self is None and other is None:
                return True
            # 均不为None的情况，比较坐标是否一致
            elif self is not None and other is not None:
                return self.x1 == other.x1 and self.y1 == other.y1 and self.x2 == other.x2 and self.y2 == other.y2
            else:
                return False
        return False


def sort_boxes_by_group(boxes: list[Box], dis_err=20):
    # 从左到右, 从上往下排序
    points = [box.tl_point for box in boxes]
    sorted_points = sort_and_group_points(points, dis_err=dis_err)
    # points的顺序映射到box的顺序
    sort_boxes = []
    for point in sorted_points:
        for box in boxes:
            if id(box.tl_point) == id(point):
                sort_boxes.append(box)
                break
    return sort_boxes


def group_box(boxes: list[Box], dis_err=20):
    points = [box.tl_point for box in boxes]
    groups = group_points(points, dis_err=dis_err)
    box_matrix = []
    for row in groups:
        box_row = []
        for point in row:
            for box in boxes:
                if id(box.tl_point) == id(point):
                    box_row.append(box)
                    break
        box_matrix.append(box_row)
    return box_matrix


class Circle:
    def __init__(self, name, point: Point, radius: int):
        self.name = name
        self.point = point
        self.radius = radius

    def get_rand_point_by_dis(self) -> Point:
        # 越靠近中心的概率越高；利用了圆的极坐标方程
        r = self.radius * math.sqrt(random.random())
        theta = 2 * math.pi * random.random()
        dx = r * math.cos(theta)
        dy = r * math.sin(theta)
        return Point(self.point.x + dx, self.point.y + dy, '{}内随机点'.format(self.name))

    def contain_point(self, point: Point) -> bool:
        dis = self.point.get_distance(point)
        return dis < self.radius

    def in_hr_line(self, p1, p2) -> bool:
        if p1.x < self.point.x < p2.x:
            return True
        if p2.x < self.point.x < p1.x:
            return True
        return False

    def touch_line(self, p1, p2):
        # 计算圆心到直线的距离
        numerator = abs((p2.x - p1.x) * (p1.y - self.point.y) - (p1.x - self.point.x) * (p2.y - p1.y))
        denominator = math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)
        if denominator == 0:
            distance = math.sqrt((p1.x - self.point.x) ** 2 + (p1.y - self.point.y) ** 2)
        else:
            distance = numerator / denominator
        # 判断距离和半径的关系
        if distance <= self.radius:
            return True
        return False


if __name__ == '__main__':
    box = Box(84, 261, 372, 418)
    # print(box.get_dis_to_center())
    cc = Circle('', Point(753, 298), 90)
    print(cc.touch_line(Point(466, 306), Point(914, 357)))
    # 人物(<466,306>), 终点(<914,357>), 门柱(<753,298>)

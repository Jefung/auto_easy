import cv2
import numpy as np

from auto_easy.base.image.cvt import img_2_ndarray_rgb
from auto_easy.constant import get_test_pic


def parse_color_range(color_range):
    """
    根据用户提供的偏差参数解析上下限颜色
    :param color_range: 偏差格式字符串，例如 "F7E97D-08123D"
    :return: lower_bound, upper_bound 两个数组
    """
    # 分成基准颜色和偏差范围
    base_color, delta_color = color_range.split('-')

    # 将颜色值从 16 进制转为 RGB 三个独立数值
    base = np.array([int(base_color[i:i + 2], 16) for i in (0, 2, 4)])
    delta = np.array([int(delta_color[i:i + 2], 16) for i in (0, 2, 4)])

    # 计算颜色的上下限
    lower_bound = np.clip(base - delta, 0, 255)  # 防止低于 0
    upper_bound = np.clip(base + delta, 0, 255)  # 防止超过 255

    return lower_bound, upper_bound


# RGB 格式
def find_color(image, color_range):
    """
    在图片中寻找符合条件的颜色范围，并计算面积占比
    :param image: 输入图片路径
    :param color_range: 偏差参数，格式如 "F7E97D-08123D"
    :return: (是否存在, 占比百分比)
    """
    # 解析颜色区间
    lower_bound, upper_bound = parse_color_range(color_range)
    image = img_2_ndarray_rgb(image)

    # 根据颜色范围生成掩码
    mask = cv2.inRange(image, lower_bound, upper_bound)

    # 计算符合条件的像素数量
    matching_pixels = np.count_nonzero(mask)

    # 计算图片总像素数量
    total_pixels = image.shape[0] * image.shape[1]

    # 是否存在符合条件的颜色
    exists = matching_pixels > 0

    # 计算面积占比（百分比输出）
    area_percentage = (matching_pixels / total_pixels) * 100

    return exists, round(area_percentage, 2)


def find_best_color(image, colors_range: list[str], area_rate=0.00) -> str:
    target_color = ''
    max_rate = 0
    for color_range in colors_range:
        exists, area_percentage = find_color(image, color_range)
        if area_percentage < area_rate:
            continue
        if area_percentage >= max_rate:
            max_rate = area_percentage
            target_color = color_range
    return target_color


# 示例调用
if __name__ == "__main__":
    # skill_color_buff = '2A98B0-2A504F'
    # # skill_color_yellow = 'A38C5D-5C705E'
    # skill_beidong = '3B814E-2C3327'
    # skill_color_yellow = 'DCC151-0D174D'
    skill_color_buff = '2A98B0-2A504F'
    skill_beidong = '3B814E-2C3327'
    skill_color_yellow = 'DCC151-0D174D'
    skill_color_red = 'CE9338-263832'
    # 图片路径
    image_path = get_test_pic('debug/wujinbodong.bmp')  # 请替换为本地图片路径
    image = cv2.imread(image_path)
    # 转换图片为 RGB 格式 (OpenCV 默认是 BGR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    print(find_color(image, skill_color_yellow))

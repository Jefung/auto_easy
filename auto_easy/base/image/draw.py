import PIL
import cv2
import numpy as np
from PIL import ImageDraw, ImageFont

from auto_easy.base.image.cvt import img_2_pil, img_2_ndarray_rgb
from auto_easy.constant import get_test_pic
from auto_easy.models import Box
from auto_easy.utils import must_get_file, cache_with_custom_time


@cache_with_custom_time()
def _get_cn_font(font_size):
    font_path = must_get_file('NotoSansSC-VariableFont_wght.ttf',
                              download_url='https://github.com/Jefung/auto_easy/raw/refs/heads/main/statics/NotoSansSC-VariableFont_wght.ttf')
    return ImageFont.truetype(font_path, font_size)


def draw_rectangles(img, boxes: list[Box] = None, title='', use_name=True, show=False, front_size=9):
    """
    在图片上绘制矩形框。

    参数:
        input_image: 可以是图像文件路径，PIL Image对象或NumPy ndarray。
        boxes: 矩形框列表，每个矩形由四个整数定义 (x1, y1, x2, y2)。
    """
    image = img_2_pil(img)

    # 创建一个画布(ImageDraw对象)
    draw = ImageDraw.Draw(image)

    font = _get_cn_font(front_size)  # 可能需要调整字体大小
    print(font)

    # 绘制每一个矩形
    boxes = boxes if boxes is not None else []
    for box in boxes:
        draw.rectangle([box.x1, box.y1, box.x2, box.y2], outline="red", width=1)
        text_position = (box.x1, box.y2 + 5)
        # 绘制文本
        if use_name and box.name:
            draw.text(text_position, box.name, fill="red", font=font)
    if show:
        image.show(title=title)
    return image  # 返回包含矩形的图像对象，用于进一步处理或保存


def show_image(img, name='img'):
    if isinstance(img, PIL.Image.Image):
        img.show(title=name)
        return
    if isinstance(img, np.ndarray):
        cv2.imshow(name, img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return
    raise Exception('show_image only support np.ndarray or Image.Image')


def show_image_table(images, column_titles):
    num_rows = len(images)  # 行数dd
    num_cols = len(images[0])  # 列数
    # 计算最大宽度和高度
    max_height = 0
    max_width = 0

    for row in images:
        for img in row:
            if img.shape[0] > max_height:
                max_height = img.shape[0]
            if img.shape[1] > max_width:
                max_width = img.shape[1]

    # 创建填充后的图像列表
    padded_images = []

    for row in images:
        padded_row = []
        for img in row:
            h, w = img.shape[:2]
            top = (max_height - h) // 2
            bottom = max_height - h - top
            left = (max_width - w) // 2
            right = max_width - w - left

            # 填充图像（使用黑色填充）
            padded_img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])
            padded_row.append(padded_img)
        padded_images.append(padded_row)

    if len(padded_images) == 0:
        return
    # 将填充后的图像拼接
    combined_rows = []

    for row in padded_images:
        combined_row = cv2.hconcat(row)
        combined_rows.append(combined_row)

    # 最后将每行组合在一起
    final_combined_image = cv2.vconcat(combined_rows)

    # 在图像顶部添加标题行
    title_height = 40  # 标题行的高度
    title_image = np.zeros((title_height, final_combined_image.shape[1], 3), dtype=np.uint8)  # 创建黑色背景

    # 添加列标题
    for idx, title in enumerate(column_titles):
        # 计算每个列标题的X坐标
        text_x = int((final_combined_image.shape[1] / num_cols) * idx) + 10  # +10为文本间距
        cv2.putText(title_image, title, (text_x, int(title_height / 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255),
                    1, cv2.LINE_AA)

    # 拼接标题行和最终图像
    # 确保 title_image 和 final_combined_image 的列数一致
    final_with_titles = cv2.vconcat([final_combined_image])

    # 显示最终图像
    cv2.imshow('Combined Image with Titles', final_with_titles)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def show_multi_image(images):
    images = [img_2_ndarray_rgb(img) for img in images]
    # 找到最大宽度和高度
    max_height = max(img.shape[0] for img in images)
    max_width = max(img.shape[1] for img in images)

    # 创建填充后的图像列表
    padded_images = []

    for img in images:
        # 计算填充的边距
        height, width = img.shape[:2]
        top = (max_height - height) // 2
        bottom = max_height - height - top
        left = (max_width - width) // 2
        right = max_width - width - left

        # 填充图像（使用黑色填充，也可以选择其他颜色）
        padded_img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        padded_images.append(padded_img)

    # 拼接所有填充后的图片（水平拼接）
    combined_image = cv2.hconcat(padded_images)

    # 显示拼接后的图像
    cv2.imshow('Combined Image', combined_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    # 拼接所有图片（水平拼接）
    # combined_image = cv2.hconcat(images)
    #
    # # 显示拼接后的图像
    # cv2.imshow('Combined Image', combined_image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


if __name__ == '__main__':
    draw_rectangles(get_test_pic('core/win_model_case_1.jpg'), [Box(100, 100, 150, 150, name='test 中文')], show=True)

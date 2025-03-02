from abc import ABC, abstractmethod

import cv2
import numpy as np

from auto_easy.base.image.process import image_color_keep
from auto_easy.models import Box


class PicProcess(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def process(self, img_source_rgb: np.ndarray, img_search_rgb: np.ndarray) -> (np.ndarray, np.ndarray):
        pass


class PicResize(PicProcess):
    def __init__(self, scale=1):
        super().__init__(name='图片缩放')
        self.scale = scale

    def process(self, img_source_rgb: np.ndarray, img_search_rgb: np.ndarray) -> (np.ndarray, np.ndarray):
        img_search_rgb = cv2.resize(
            img_search_rgb,
            None,
            fx=self.scale,
            fy=self.scale,
            interpolation=cv2.INTER_CUBIC
        )
        return img_source_rgb, img_search_rgb


class PicColorKeep(PicProcess):
    def __init__(self, color=None):
        super().__init__(name='颜色保留')
        self.color = color

    def process(self, img_source_rgb: np.ndarray, img_search_rgb: np.ndarray) -> (np.ndarray, np.ndarray):
        img_source_rgb = image_color_keep(img_source_rgb, self.color)
        img_search_rgb = image_color_keep(img_search_rgb, self.color)
        return img_source_rgb, img_search_rgb


class PicColorGray(PicProcess):
    def __init__(self, ):
        super().__init__('转灰度图片')

    def process(self, img_source_rgb: np.ndarray, img_search_rgb: np.ndarray) -> (np.ndarray, np.ndarray):
        img_source_gray = cv2.cvtColor(img_source_rgb, cv2.COLOR_BGR2GRAY)
        img_search_rgb = cv2.cvtColor(img_search_rgb, cv2.COLOR_BGR2GRAY)
        return img_source_gray, img_search_rgb


class PicColorCanny(PicProcess):
    def __init__(self, threshold1=100, threshold2=200):
        super().__init__('背景去除')
        self.threshold1 = threshold1  # 用于边缘连接。如果边缘强度大于这个值，Canny 算法将其分类为边缘
        self.threshold2 = threshold2  # 当边缘强度小于此值时，如果边缘与强边缘相连，则该边缘也将被接受

    def process(self, img_source_rgb: np.ndarray, img_search_rgb: np.ndarray) -> (np.ndarray, np.ndarray):
        img_source_rgb = cv2.Canny(img_source_rgb, self.threshold1, self.threshold2)
        img_search_rgb = cv2.Canny(img_search_rgb, self.threshold1, self.threshold2)
        return img_source_rgb, img_search_rgb


class PicCrop(PicProcess):
    def __init__(self, src_crop_box: Box):
        super().__init__('图片裁剪')
        self.src_crop_box = src_crop_box

    def process(self, img_source_rgb: np.ndarray, img_search_rgb: np.ndarray) -> (np.ndarray, np.ndarray):
        height, width = img_source_rgb.shape[:2]
        x1, y1, x2, y2 = self.src_crop_box.tuple()
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(width, x2)
        y2 = min(height, y2)

        img_source_crop = img_source_rgb[y1:y2, x1:x2]
        return img_source_crop, img_search_rgb

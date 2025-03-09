import json
import time
import warnings
from typing import List

import numpy as np
import torch

from auto_easy.base.ai.model_mgr_v2 import AIModelBase
from auto_easy.base.image.cvt import img_2_ndarray_rgb, img_2_list, list_2_ndarray
from auto_easy.models import MYoloItem, YoloItem, Box
from auto_easy.utils import logger, cls_to_dict, set_obj_by_dict

warnings.filterwarnings("ignore", category=FutureWarning)


class ModelConf:
    def __init__(self, name, pt_path, prob=0.5, iou=0.45):
        self.name = name
        self.pt_path = pt_path
        self.prob = prob
        self.iou = iou
        self.agnostic = False
        self.multi_label = True


class YoloObj:
    def __init__(self):
        self.id = -1
        self.name = ''
        self.score = 0
        self.x1 = 0
        self.y1 = 0
        self.x2 = 0
        self.y2 = 0

    def __str__(self):
        return f'{self.id}({self.name}):<{self.x1}, {self.y1}, {self.x2}, {self.y2}> {self.score}'


class YoloObjs:
    def __init__(self, conf: ModelConf, dets: List[YoloObj]):
        self.objs = dets
        self.conf = conf
        self.screen_box = None

        self.result_str = ''  # TODO: 待删除
        self.create_ts = time.time()

    def to_dict(self):
        return {}

    def __str__(self):
        return '|'.join([str(det) for det in self.objs])

    @staticmethod
    def new_obj_by_str(s):
        segments = s.split('|')
        dets = []
        for segment in segments:
            name, coordinates = segment.split('<')
            x, y = coordinates.rstrip('>').split(',')
            obj = YoloObj()
            obj.name = name
            obj.x1 = int(x)
            obj.y1 = int(y)
            obj.x2 = int(x)
            obj.y2 = int(y)
            dets.append(obj)
        return YoloObjs(ModelConf('', ''), dets)


class AIYolo(AIModelBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AIYoloV5(AIYolo):
    def __init__(self, conf: ModelConf):
        self.conf = conf
        self.model = None
        super().__init__(self.conf.name)

    def init_model(self):
        conf = self.conf
        # # 禁用所有级别的日志记录
        # logger.disabled = True
        model = torch.hub.load('ultralytics/yolov5', 'custom', verbose=True, path=conf.pt_path)

        # 将模型设置为eval模式，关闭一些训练相关的模块（如Dropout等），提升性能
        model.eval()
        # 设置模型相关参数（可选操作）
        model.det_conf = conf.prob  # 设置置信度阈值，只有置信度高于此值的检测结果才会被保留
        model.iou = conf.iou  # 设置非极大值抑制（NMS）的交并比（IoU）阈值
        model.agnostic = conf.agnostic  # 设置是否进行类别无关的NMS，False表示按照类别进行NMS筛选
        model.multi_label = conf.multi_label  # 设置是否允许每个检测框有多个标签，False表示每个检测框只对应一个类别
        self.model = model
        logger.debug(f'模型({conf.name})完成加载')

    def predict(self, img) -> MYoloItem:
        if self.use_rpc():
            return self.rpc_call(img)
        self.wait_model_init()
        img = img_2_ndarray_rgb(img)
        height, width = img.shape[:2]
        with torch.no_grad():
            # 使用模型进行预测，在这个上下文环境中，不会进行梯度计算，节省计算资源，提升性能
            results = self.model(img)
            # 处理预测结果，整理成要求的格式
            detections = results.pandas().xyxy[0].to_dict(orient='records')
            items = []
            for idx, detection in enumerate(detections, start=1):
                name = detection['name']
                score = round(detection['confidence'], 2)
                x1 = int(detection['xmin'])
                y1 = int(detection['ymin'])
                x2 = int(detection['xmax'])
                y2 = int(detection['ymax'])
                item = YoloItem(name, score, Box(x1, y1, x2, y2), src_box=Box(0, 0, height, width))
                items.append(item)
        return MYoloItem(items, self.conf.name)

    def rpc_req_encode(self, *args, **kwargs):
        if len(args) != 1:
            raise Exception('args length error')
        args_list = list(args)
        args_list[0] = img_2_list(args_list[0])
        args = tuple(args_list)
        return args, kwargs

    def rpc_req_decode(self, *args, **kwargs):
        args_list = list(args)
        img = list_2_ndarray(args_list[0])
        if img.dtype != np.uint8:
            img = img.astype(np.uint8)
        args_list[0] = img
        args = tuple(args_list)
        return args, kwargs

    def rpc_resp_encode(self, origin_resp: MYoloItem):
        return json.dumps(cls_to_dict(origin_resp))

    def rpc_resp_decode(self, str_resp):
        d = json.loads(str_resp)
        items = []
        for v in d['items']:
            obj = YoloItem(
                v['name'],
                v['score'],
                match_box=Box(
                    v['box']['tl_point']['_x'], v['box']['tl_point']['_y'],
                    v['box']['rd_point']['_x'], v['box']['rd_point']['_y'],
                ),
                src_box=Box(
                    v['src_box']['tl_point']['_x'], v['src_box']['tl_point']['_y'],
                    v['src_box']['rd_point']['_x'], v['src_box']['rd_point']['_y'],
                ),
            )
            items.append(obj)

        res = MYoloItem([], d.get('model_name', ''))
        set_obj_by_dict(res, d)
        res.items = items
        return res


if __name__ == '__main__':
    pass

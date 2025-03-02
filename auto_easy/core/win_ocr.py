import numpy as np

from auto_easy.base.ai import AIModelBase, ModelMgrV2
from auto_easy.base.ai import OCR
from auto_easy.base.ai.ai_yolo import YoloObjs
from auto_easy.base.ai.superres.ai_supper_res import SuperRes
from auto_easy.base.windows import Window
from auto_easy.models import Box


class WinSupperRes(Window, ModelMgrV2):
    def __init__(self, window_id, models: list[AIModelBase], rpc_server_port=8765):
        Window.__init__(self, window_id=window_id)
        ModelMgrV2.__init__(self, models=models, rpc_server_port=rpc_server_port)

    def supper_res(self, img, scale_factor=3) -> np.array:
        models = self.get_models_by_cls(SuperRes)
        if len(models) == 0:
            raise Exception('No SuperRes model found')
        model: SuperRes = models[0]

        # img = self.capture(box)
        return model.predict(img, scale_factor)


class WinOCR(WinSupperRes):
    def __init__(self, window_id, models: list[AIModelBase], rpc_server_port=8765):
        WinSupperRes.__init__(self, window_id=window_id, models=models, rpc_server_port=rpc_server_port)

    def ocr(self, box: Box, scale_factor=1) -> YoloObjs:
        models = self.get_models_by_cls(OCR)
        if len(models) == 0:
            raise Exception('No yolo OCR found')
        model: OCR = models[0]

        img = self.capture(box)
        if scale_factor != 1:
            img = self.supper_res(img, scale_factor=scale_factor)

        return model.predict(img)


if __name__ == '__main__':
    supper_res = SuperRes()
    ocr = OCR()
    win = WinOCR('Phone-9a', models=[ocr, supper_res])
    ans = win.ocr(Box(264, 53, 398, 81), scale_factor=2)

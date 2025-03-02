import cv2
import numpy as np

from auto_easy.base.ai.model_mgr_v2 import AIModelBase
from auto_easy.base.ai.superres.ai_supper_res import SuperRes
from auto_easy.base.image.cvt import img_2_ndarray_rgb, img_2_list, list_2_ndarray
from auto_easy.constant import get_test_pic


class OCR(AIModelBase):
    def __init__(self, *args, **kwargs):
        self.arg = args
        self.kwargs = kwargs
        super().__init__(name='OCR')
        self.rpc_support = False  # TODO: test

    def init_model(self):
        import easyocr
        if len(self.arg) > 0 or len(self.kwargs.keys()) > 0:
            self.reader = easyocr.Reader(*self.arg, **self.kwargs)
        else:
            self.reader = easyocr.Reader(['en', 'ch_sim'], quantize=False)

    def predict(self, img, auto_proc=False):
        if self.use_rpc():
            return self.rpc_call(img)
        self.wait_model_init()
        img = img_2_ndarray_rgb(img)
        # cv2.imwrite(gen_test_pic('ocr_input.bmp'), img)
        if auto_proc:
            # 灰度化
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # cv2.imwrite(gen_test_pic('ocr_gray.bmp'), img)

            # 二值化
            _, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
            # cv2.imwrite(gen_test_pic('ocr_binary.bmp'), img)

            # 去噪
            img = cv2.GaussianBlur(img, (5, 5), 0)
            # cv2.imwrite(gen_test_pic('ocr_blur.bmp'), img)

            # 增强对比度
            img = cv2.equalizeHist(img)
            # cv2.imwrite(gen_test_pic('ocr_equal.bmp'), img)

        result = self.reader.readtext(img)
        ans = []
        for detection in result:
            text = detection[1]
            ans.append(text)
        return ans

    def rpc_req_encode(self, *args, **kwargs):
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


if __name__ == '__main__':
    pass
    supper_res = SuperRes()
    scaled = supper_res.mock_rpc_call(get_test_pic('level.bmp'), scale_factor=3)
    ocr = OCR()
    ans = ocr.predict(scaled, debug=True)
    print(ans)
    ans = ocr.predict(scaled, debug=False)
    print(ans)
    # ans = ocr.predict(get_test_pic('attack.bmp'))
    # print(ans)

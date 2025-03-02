import os

import PIL
import cv2
import numpy as np
from PIL import Image


def img_2_pil(img):
    if isinstance(img, str):
        if not os.path.exists(img):
            raise FileNotFoundError(img)
        return Image.open(img)
    if isinstance(img, np.ndarray):
        return Image.fromarray(img)
    if isinstance(img, PIL.Image.Image):
        return img
    raise TypeError("img must be str or PIL.Image.Image")


def img_2_ndarray_rgb(img):
    if isinstance(img, str):
        if not os.path.exists(img):
            raise FileNotFoundError(img)
        image_bgr = cv2.imread(img)
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        return image_rgb

    if isinstance(img, PIL.Image.Image):
        return np.array(img)

    if isinstance(img, np.ndarray):
        return img
    raise TypeError('img must be PIL.Image.Image or np.ndarray, type: {}'.format(type(img)))


def img_2_ndarray_gbr(img):
    if isinstance(img, str):
        return cv2.imread(img)
    if isinstance(img, PIL.Image.Image):
        rgb_array = np.array(img)
        bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
        return bgr_array
    if isinstance(img, np.ndarray):
        return img
    raise TypeError('img must be PIL.Image.Image or np.ndarray, type: {}'.format(type(img)))


def img_2_list(img):
    ndarray = img_2_ndarray_rgb(img)
    return ndarray.tolist()


def list_2_ndarray(list_img):
    return np.array(list_img)
    # ndarray = img_2_ndarray(list_img)

    # def rpc_api_predict(self,model_name,image_bytes) -> {} :
    #     self.set_cur_model(model_name)
    #     image = Image.open(io.BytesIO(image_bytes.data))
    #     print('[client_rpc_call] rpc api predict, image_size = {}'.format(image.size))
    #     results = self.cur_model.predict(image)
    #     json.dumps(cls_to_dict(results))
    #     return json.dumps(cls_to_dict(results))
    #
    # def rpc_call_predict(self, model_name, image) -> YoloObjs:
    #     if isinstance(image, str):
    #         image = Image.open(image)
    #     image_bytes = io.BytesIO()
    #     image.save(image_bytes, format='PNG')
    #     image_bytes = image_bytes.getvalue()
    #     bs = self.rpc_client.ocr_rpc_api_predict(model_name, image_bytes)
    #     d = json.loads(bs)

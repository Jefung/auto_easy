import importlib.util
import os
from typing import List

from auto_easy.base.ai import ModelMgrV2, AIModelBase
from auto_easy.base.ai.ai_yolo import AIYolo
from auto_easy.base.windows import Window
from auto_easy.models import MYoloItem, YoloItem
from auto_easy.utils.cache_util import cache_with_custom_time


class WinYolo(Window, ModelMgrV2):
    def __init__(self, window_id, models: list[AIModelBase], rpc_server_port=8765, item_model_dir=''):
        Window.__init__(self, window_id=window_id)
        ModelMgrV2.__init__(self, models=models, rpc_server_port=rpc_server_port)
        self._cur_yolo_name = ''
        if item_model_dir != '' and not os.path.isdir(item_model_dir):
            raise Exception('item_model_dir must be a valid path: {}'.format(item_model_dir))
        self._item_model_dir = item_model_dir

    @property
    def cur_yolo_name(self):
        return self._cur_yolo_name

    @cur_yolo_name.setter
    def cur_yolo_name(self, name):
        yolo_models = self.get_models_by_cls(AIYolo)
        models_name = [model.name for model in yolo_models]
        if name not in models_name:
            raise Exception(f'invalid yolo model({name}), registed names: {models_name}')
        self._cur_yolo_name = name

    def yolo_predict(self, name=None) -> MYoloItem:
        yolo_models = self.get_models_by_cls(AIYolo)
        if len(yolo_models) == 0:
            raise Exception('No yolo models found')
        # 优先使用用户指定的模型,其次使用cur_yolo_name, 最后默认选择第一个
        model_name = self.cur_yolo_name if self.cur_yolo_name != '' else yolo_models[0].name
        if name is not None:
            model_name = name

        model: AIYolo = None
        for m in yolo_models:
            if m.name == model_name:
                model = m
                break
        if model is None:
            raise Exception(f'no yolo model named "{model_name}" found')

        img = self.capture()
        mdet: MYoloItem = model.predict(img)
        for i, item in enumerate(mdet.items):
            mdet.items[i] = self._auto_cvt_item(item)  # 类型转化
        return mdet

    def _auto_cvt_item(self, item: YoloItem) -> YoloItem:
        # 自动读取_item_model_dir目录下的AIItemBase类，然后调用其静态方法can_new_obj判断是否生成对象
        # 注：这里优先遍历派生类
        if self._item_model_dir == '':
            return item
        item_cls_list = find_classes_inheriting(self._item_model_dir, YoloItem)
        for cls in item_cls_list:
            if cls.can_new_obj(item.name):
                return cls(*item.params_list)
        return item


@cache_with_custom_time()
def find_classes_inheriting(dir: str, cls) -> List[type]:
    """
    在指定目录下查找继承自AIItemBase的所有类。
    :param dir: 要查找的目录路径
    :return: 继承自AIItemBase的类的列表
    """
    if not os.path.exists(dir):
        raise Exception("不存在的路径: {}".format(dir))
    if isinstance(cls, type):
        cls = cls.__name__
    if not isinstance(cls, str):
        raise Exception("find_classes_inheriting must use class or class_name")
    result_classes = []
    processed_modules = set()
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                pass
                file_path = os.path.join(root, file)
                module_name = os.path.splitext(file)[0]
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                processed_modules.add(module_name)
                for name, obj in vars(module).items():
                    if isinstance(obj, type):
                        try:
                            if cls in [cls.__name__ for cls in obj.mro()]:
                                result_classes.append(obj)
                        except AttributeError:
                            continue
    # 因为同个文件夹下，不同文件导入的class可能是路径不同，被认为不同的类，这里通过类名统一去重
    unique_class_list = [cls for i, cls in enumerate(result_classes) if
                         cls.__name__ not in [c.__name__ for c in result_classes[:i]]]

    # 排序，将派生类排在前面
    def sort_classes(cls1, cls2):
        return len(cls1.mro()) > len(cls2.mro())

    sorted_class_list = sorted(unique_class_list, key=lambda x: tuple(sort_classes(x, y) for y in unique_class_list),
                               reverse=True)

    return sorted_class_list


if __name__ == '__main__':
    pass

import time

from auto_easy.base.ai import AIModelBase
from auto_easy.base.ai import OCR
from auto_easy.base.ai.superres.ai_supper_res import SuperRes
from auto_easy.base.windows import Window
from auto_easy.constant import TestPicDir
from auto_easy.core.win_ai import WinYolo
from auto_easy.core.win_find_color import WinFindColor
from auto_easy.core.win_find_pic import WinFindPic
from auto_easy.core.win_monitor import WinTimer
from auto_easy.core.win_ocr import WinOCR
from auto_easy.core.win_show import WinShow
from auto_easy.models import Box


class CoreConf:
    def __init__(self, *args, **kwargs):
        self.pic_dir = ''
        self.window_id = ''  # 窗口名/窗口名前缀/窗口句柄
        self.pic_save_dir = None
        self.models: list[AIModelBase] = []
        self.rpc_server_port = 8765
        self.item_model_dir = ''  # 存储各种业务定制的Yolo Item类, 会自动进行转化


class AutoCore(
    WinYolo,
    WinOCR,
    WinFindPic,
    WinFindColor,
    WinShow,
    WinTimer):
    def __init__(self, conf: CoreConf):
        Window.__init__(self, window_id=conf.window_id)
        WinYolo.__init__(self, window_id=conf.window_id, models=conf.models, rpc_server_port=conf.rpc_server_port,
                         item_model_dir=conf.item_model_dir)
        WinOCR.__init__(self, window_id=conf.window_id, models=conf.models, rpc_server_port=conf.rpc_server_port)
        WinFindColor.__init__(self, window_id=conf.window_id)
        WinFindPic.__init__(self, window_id=conf.window_id, pic_dir=conf.pic_dir)
        WinShow.__init__(self, window_id=conf.window_id, pic_save_dir=conf.pic_save_dir)
        WinTimer.__init__(self, window_id=conf.window_id)


def interval_save(auto_core: AutoCore):
    auto_core.save('interval_save', debug_print=True)


_global_auto_core = None


def get_auto_core() -> AutoCore:
    global _global_auto_core
    if _global_auto_core is None:
        raise Exception('global_auto_core is not set')
    return _global_auto_core


def set_auto_core(auto_core: AutoCore):
    global _global_auto_core
    _global_auto_core = auto_core


if __name__ == '__main__':
    conf = CoreConf()
    conf.window_id = 'Phone-9a'
    conf.pic_dir = TestPicDir
    conf.pic_save_dir = TestPicDir + '/debug'

    supper_res = SuperRes()
    ocr = OCR()
    conf.models = [ocr, supper_res]
    # win = WinOCR('Phone-9a', models=[ocr, supper_res])
    # ans = win.ocr(Box(264, 53, 398, 81), scale_factor=2)

    auto_core = AutoCore(conf)
    print(auto_core.ocr(Box(264, 53, 398, 81), scale_factor=2))
    # auto_easy.add_timer_minitor(2, interval_save)

    time.sleep(10)
    # ans = auto_easy.find_pics('core/test_1')
    # print(ans)
    # auto_easy.window_id()
    # auto_easy.ocr()
    # auto_easy.find_pic()
    # auto_easy.a = 2
    # auto_easy.print_a1()
    # auto_easy.print_a2()

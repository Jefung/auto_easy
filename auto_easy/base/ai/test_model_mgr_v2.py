import time
from unittest import TestCase

from auto_easy.base.ai.model_mgr_v2 import AIModelBase, ModelMgrV2
from auto_easy.utils import async_thread


class ModelTest1(AIModelBase):
    def __init__(self):
        super().__init__(name='test1')

    def init_model(self):
        print('init model1')
        time.sleep(2)

    def predict(self, arg1):
        print('ModelTest1 input', arg1)
        return ['ModelTest1', arg1]


class TestModelMgr(TestCase):
    def test_predict(self):
        model1 = ModelTest1()
        mgr = ModelMgrV2([model1])
        async_thread(mgr.start_rpc_server)
        time.sleep(3)
        print('开始调用')
        model1_new = ModelTest1()
        mgr2 = ModelMgrV2([model1_new])
        time.sleep(1)
        ans = mgr2.predict('test1', 'input_test')
        print('resp ', ans)

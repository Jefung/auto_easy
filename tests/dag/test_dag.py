import logging
from unittest import TestCase

from auto_easy import DAG, ExecutorDebug, Ctx, DAGLayerSimple
from auto_easy.global_log import set_log_2_console, logger


class TestDag(DAG):
    def __init__(self):
        super().__init__('测试重试功能')

    def init(self):
        self.add_layer(ExecutorDebug('layer1'))
        self.add_layer(ExecutorDebug('layer2', exec_wait=1))
        self.add_layer(ExecutorDebug('layer3', hit_ret=True))


class TestDAG(TestCase):
    def test_dag(self):
        dag = TestDag()
        ok = dag.run(ctx=Ctx())
        self.assertTrue(ok)
        # logger.debug(ok)

    def test_subdag(self):
        set_log_2_console(logging.INFO)
        logger.debug('test_subdag')
        class TestSubDag(DAG):
            def __init__(self):
                super().__init__('测试Sub功能')

            def init(self):
                self.add_layer(TestDag())
                self.add_layer(DAGLayerSimple(ExecutorDebug('after_sub_dag',hit_ret=True)))

        dag2 = TestSubDag()
        ok = dag2.run(ctx=Ctx())
        self.assertTrue(ok)

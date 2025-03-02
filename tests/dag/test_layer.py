from unittest import TestCase

from auto_easy import DAGLayerSwitchOne, ExecutorDebug, Ctx


class TestDAGLayerSwitchOne(TestCase):
    def test_exec(self):
        layer = DAGLayerSwitchOne(loop_to=1.1)
        layer.add_branch(ExecutorDebug('1', hit_ret=False, hit_wait=0.2))
        layer.add_branch(ExecutorDebug('2', hit_ret=False, hit_wait=0.2))
        layer.add_branch(ExecutorDebug('3', hit_ret=True, hit_wait=0.1, exec_ret=True))
        ok = layer.run(Ctx())
        self.assertTrue(ok)

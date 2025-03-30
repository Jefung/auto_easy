from abc import abstractmethod
from typing import List

from auto_easy.dag.executor import Executor, ExecutorDebug
from auto_easy.dag.layer import DAGLayerDef, LayerConf, DAGLayerSimple
from auto_easy.models import Ctx
from auto_easy.utils import is_actual_subclass, logger


class DAG(Executor):
    def __init__(self, name, retry_mode=True):
        self.layers: List[DAGLayerDef] = []
        self.retry_mode = retry_mode  # None-不重试, 1-回退重试
        super().__init__(name)

    def _init_optional(self, ctx: Ctx) -> bool:
        return self._init_layer(ctx)

    @abstractmethod
    def _init_layer(self, ctx: Ctx):
        pass

    def _hit_optional(self, ctx: Ctx) -> bool:
        if len(self.layers) == 0:
            raise Exception("Dag empty, no layers added, name: {}".format(self.name))
        hit = self.layers[0].hit(ctx=ctx)
        if hit:
            return True
        if self.layers[0].conf.break_err:
            return True
        return hit
        # return self.layers[0].hit(ctx=ctx)

    def _exec_optional(self, ctx: Ctx) -> bool:
        if len(self.layers) == 0:
            raise Exception("Dag empty, no layers added, name: {}".format(self.name))

        logger.info(f'开始执行DAG: {self.name}')
        idx = 0
        retry = 0
        while idx < len(self.layers):

            layer = self.layers[idx]
            succ = False
            if layer.hit(ctx=ctx):
                if layer.run(ctx=ctx):
                    succ = True
            # logger.debug(f'layer [{idx}]-{layer.name} result: {succ}')
            if not succ:
                if layer.conf.break_err:
                    logger.info(f'Layer({layer.name}) 未命中, 结束DAG执行')
                    break

            if succ or layer.conf.skip_err:
                idx += 1
                continue

            if self.retry_mode and self.retry_mode == 1 and retry < 1:
                if idx > 0:
                    logger.warning("Retrying layer, failed layer: {}, goback: {}".format(self.layers[idx].name,
                                                                                         self.layers[idx - 1].name))
                    idx = idx - 1
                    retry += 1
                    continue

            logger.error(f'DAG({self.name}) 执行失败, layer: {layer.name}')
            return False


        logger.debug(f'结束执行DAG: {self.name}')
        return True

    def add_layer(self, layer, conf: LayerConf = None):
        if not is_actual_subclass(layer, DAGLayerDef):
            if is_actual_subclass(layer, Executor):
                layer = DAGLayerSimple(executor=layer, conf=conf)

        if not is_actual_subclass(layer, DAGLayerDef):
            raise Exception("Dag add layer failed")
        self.layers.append(layer)

    def add_layers(self, layers):
        for layer in layers:
            self.add_layer(layer)

    @staticmethod
    def simple_new(name, executors: List[Executor]):
        dag = DAG(name)
        dag.add_layers(executors)
        return dag

class SimpleDAG(DAG):
    def __init__(self, name, executors: List[Executor],retry_mode=True):
        super().__init__(name,retry_mode)
        for executor in executors:
            self.add_layer(executor)

    def _init_layer(self, ctx: Ctx):
        pass

class EmptyDAG(DAG):
    def __init__(self,name, retry_mode=True):
        super().__init__(name, retry_mode=retry_mode)

    def _init_layer(self,ctx: Ctx):
        pass

# todo: 待废弃
class SubDAG2Executor(Executor):
    def __init__(self, dag: DAG):
        super().__init__(dag.name)
        self.dag = dag

    def _hit_optional(self, ctx: Ctx) -> bool:
        return self.dag.hit(ctx=ctx)

    def _exec_optional(self, ctx: Ctx) -> bool:
        return self.dag.run(ctx=ctx)

    @staticmethod
    def cvt(dag: DAG):
        return SubDAG2Executor(dag=dag)

class TestDag(DAG):
    def __init__(self):
        super().__init__('测试重试功能')

    def _init_layer(self, ctx: Ctx):
        self.add_layer(ExecutorDebug('layer1'))
        self.add_layer(ExecutorDebug('layer2', exec_wait=1))
        self.add_layer(ExecutorDebug('layer3', hit_ret=True))


if __name__ == "__main__":
    ans = TestDag().run(Ctx())
    print(ans)
    pass

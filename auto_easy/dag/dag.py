from typing import List

from auto_easy.dag.executor import Executor
from auto_easy.dag.layer import DAGLayerDef, LayerConf, DAGLayerSimple
from auto_easy.models import Ctx
from auto_easy.utils import is_actual_subclass, logger


class DAG(Executor):
    def __init__(self, name, retry_mode=None):
        self.layers: List[DAGLayerDef] = []
        self.retry_mode = retry_mode  # None-不重试, 1-回退重试
        super().__init__(name)

    # @abstractmethod
    def init(self):
        pass

    def hit(self, ctx: Ctx) -> bool:
        if len(self.layers) == 0:
            raise Exception("Dag empty, no layers added, name: {}".format(self.name))
        return self.layers[0].hit(ctx=ctx)

    def exec(self, ctx: Ctx) -> bool:
        if len(self.layers) == 0:
            raise Exception("Dag empty, no layers added, name: {}".format(self.name))

        logger.debug(f'开始执行DAG: {self.name}')
        idx = 0
        retry = 0
        while idx < len(self.layers):
            layer = self.layers[idx]
            logger.debug(layer.name)
            succ = False
            if layer.hit(ctx=ctx):
                if layer.run(ctx=ctx):
                    succ = True
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

            logger.debug(f'DAG({self.name}) 执行失败, layer: {layer.name}')
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


class SubDAG2Executor(Executor):
    def __init__(self, dag: DAG):
        super().__init__(dag.name)
        self.dag = dag

    def hit(self, ctx: Ctx) -> bool:
        return self.dag.hit(ctx=ctx)

    def exec(self, ctx: Ctx) -> bool:
        return self.dag.run(ctx=ctx)

    @staticmethod
    def cvt(dag: DAG):
        return SubDAG2Executor(dag=dag)


if __name__ == "__main__":
    pass

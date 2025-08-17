import time
from abc import ABC, abstractmethod
from random import uniform

from numba.np.arraymath import return_false

from auto_easy import Timeout, PicDetConf, Direction
from auto_easy.core.core import get_auto_core
from auto_easy.models import Ctx
from auto_easy.utils import loop_until_true, logger, cost_ms, sleep_with_rand


class Executor(ABC):
    def __init__(self, name):
        self.name = name
        self.hit_loop_toms = 0
        self._inited = False

    # @abstractmethod
    def _init_optional(self, ctx: Ctx) -> bool:
        return True

    # @abstractmethod
    def _hit_optional(self, ctx: Ctx) -> bool:
        return True

    @abstractmethod
    def _exec_optional(self, ctx: Ctx) -> bool:
        return True

    def _inner_init(self,ctx: Ctx):
        if self._inited:
            return
        self._inited = True
        self._init_optional(ctx)

    def reset(self, ctx: Ctx):
        return True

    def hit(self, ctx: Ctx) -> bool:
        self._inner_init(ctx)
        return self._hit_optional(ctx)

    def run(self, ctx: Ctx):
        start = time.time()
        self._inner_init(ctx)
        
        if not self._hit_optional(ctx):
            logger.debug("[执行] 前置校验失败: {}".format(self.name))
            return False

        if not self._exec_optional(ctx):
            logger.error("[执行] 中途执行失败: {}".format(self.name))
            return False

        logger.debug("[执行] {} 执行成功, 耗时： {}ms".format(self.name, cost_ms(start)))
        return True


    @classmethod
    def __subclasshook__(cls, subclass):
        """
        This makes the abstract method optional for the subclass to override,
        ensuring that BaseClass can still be instantiated if necessary.
        """
        if cls is Executor:
            return True
        return NotImplemented


class ExecutorDebug(Executor):
    def __init__(self, name, hit_ret=True, exec_ret=True, hit_wait=0, exec_wait=0):
        super().__init__("Debug执行器{}".format(name))
        self.hit_ret = hit_ret
        self.exec_ret = exec_ret
        self.exec_wait = exec_wait
        self.hit_wait = hit_wait

    def _hit_optional(self, ctx: Ctx) -> bool:
        time.sleep(self.hit_wait)
        return self.hit_ret

    def _exec_optional(self, ctx: Ctx) -> bool:
        time.sleep(self.exec_wait)
        return self.exec_ret


class ExecutorPicClick(Executor):
    def __init__(self, pic_name: object, det_to: object = 2, bf_sleep: object = 0.2, af_sleep: object = 0.2, x_offset: object = 0, y_offset: object = 0,
                 hit_err_print: object = True,
                 click_area_rate: object = (0, 0, 1, 1), click_hit_det=False, click_times=1) -> None:
        self.pic_name = pic_name
        self.det_to = det_to
        self.bf_sleep = bf_sleep
        self.af_sleep = af_sleep
        self.x_offset = x_offset  # 点击偏移量
        self.y_offset = y_offset  # 点击偏移量
        self.hit_err_print = hit_err_print
        self.click_area_rate = click_area_rate
        self.click_hit_det = click_hit_det
        self.click_times = click_times
        self.mdet = None
        super().__init__(name='图片点击({})'.format(pic_name))

    def _hit_optional(self, ctx: Ctx) -> bool:
        # logger.debug('_hit_optional')
        mdet = get_auto_core().loop_find_pics(self.pic_name, to=self.det_to)
        if not mdet.all_detected:
            if self.hit_err_print:
                pass
            return False
        self.mdet = mdet
        return True

    def _exec_optional(self, ctx: Ctx) -> bool:
        if self.click_hit_det:
            mdet = self.mdet
        else:
            mdet = get_auto_core().loop_find_pics(self.pic_name, to=self.det_to)
            logger.info(f'mdet: {mdet},  mdet.all_detected: {mdet.all_detected}, pic_det_list:{mdet.pic_det_list}')
            if not mdet.all_detected:
                logger.error("[图片点击] 识别失败，无法识别. {}".format(self.pic_name))
                return False

        # logger.info(f'self.click_hit_det: {self.click_hit_det}')
        box = mdet.box
        box = box.crop_by_rate(self.click_area_rate[0], self.click_area_rate[1], self.click_area_rate[2], self.click_area_rate[3])
        box.move(self.x_offset, self.y_offset)
        logger.debug("[图片点击] 点击图片({}), 图片区域: {}，最终点击区域: {}".format(self.pic_name, mdet.box,box))
        time.sleep(self.bf_sleep * uniform(0.8, 1.2))
        for i in range(self.click_times):
            get_auto_core().left_click_in_box(
                box,
                af_sleep=uniform(0.2,0.5),
            )
        time.sleep(self.af_sleep * uniform(0.8, 1.2))
        return True

class ExecutorPicClickAndWaitDisappear(Executor):
    def __init__(self, pic_name, det_to=2, wait_to=5, check_interval=0.5, bf_sleep=0, af_sleep=0.1):
        self.pic_name = pic_name
        self.det_to = det_to
        self.wait_to = wait_to
        self.check_interval = check_interval
        self.bf_sleep = bf_sleep
        self.af_sleep = af_sleep
        super().__init__(name='图片点击并等待消失({})'.format(pic_name))

    def _hit_optional(self, ctx: Ctx) -> bool:
        mdet = get_auto_core().loop_find_pics(self.pic_name, to=self.det_to)
        return mdet.is_detected

    def _exec_optional(self, ctx: Ctx) -> bool:
        time.sleep(self.bf_sleep)


        # 先点击图片
        mdet = get_auto_core().loop_find_pics(self.pic_name, to=self.det_to)
        if not mdet.is_detected:
            return False
        logger.debug("[图片点击] 点击图片({}), 区域: {}".format(self.pic_name, mdet.box))
        get_auto_core().left_click_in_box(mdet.box,af_sleep=1)

        to = Timeout(self.wait_to)
        while to.not_timeout():

            # 检查图片是否消失
            mdet = get_auto_core().loop_find_pics_not_exists(self.pic_name, to=self.check_interval)
            if not mdet.is_detected:
                break

            logger.debug("[图片点击] 图片未消失, 重新点击, 检查次数: {}. ".format(self.pic_name, mdet.box, to.check_times))
            logger.debug("[图片点击] 点击图片({}), 区域: {}".format(self.pic_name, mdet.box))
            get_auto_core().left_click_in_box(mdet.box,af_sleep=1)


        if to.is_timeout():
            logger.debug("[图片点击] 图片在指定时间内点击后仍然未消失, 图片：{}".format(self.pic_name))
            return False

        time.sleep(self.af_sleep)
        return True

class ExecutorTryPicClick(Executor):
    def __init__(self, pic_name, det_to=0.5, bf_sleep=0.2, af_sleep=0.3):
        self.pic_name = pic_name
        self.det_to = det_to
        self.bf_sleep = bf_sleep
        self.af_sleep = af_sleep
        super().__init__(name='图片点击({})'.format(pic_name))

    def _hit_optional(self, ctx: Ctx) -> bool:
        return True

    def _exec_optional(self, ctx: Ctx) -> bool:
        mdet = get_auto_core().loop_find_pics(self.pic_name, to=self.det_to)
        if not mdet.is_detected:
            return True

        logger.info("[点击] 点击图片({}), 区域: {}".format(self.pic_name, mdet.box))
        get_auto_core().left_click_in_box(
            mdet.box,
            af_sleep=self.af_sleep * uniform(0.8, 1.2),
            bf_sleep=self.bf_sleep * uniform(0.8, 1.2),
        )
        return True

class ExecutorTryPicMultiClick(Executor):
    def __init__(self, pic_name, det_to=0.5, bf_sleep=0.2, af_sleep=0.3, click_sleep=0.5):
        self.pic_name = pic_name
        self.det_to = det_to
        self.bf_sleep = bf_sleep
        self.af_sleep = af_sleep
        self.click_sleep = click_sleep
        super().__init__(name='多图片点击({})'.format(pic_name))

    def _hit_optional(self, ctx: Ctx) -> bool:
        return True

    def _exec_optional(self, ctx: Ctx) -> bool:
        conf = PicDetConf()
        conf.multi_match = True

        mdet = get_auto_core().loop_find_pics(self.pic_name, to=self.det_to,det_conf=conf)
        logger.debug(mdet)
        if not mdet.is_detected:
            return True

        for box in mdet.boxes:
            logger.info("[点击] 点击图片({}), 区域: {}".format(self.pic_name, box))
            get_auto_core().left_click_in_box(
                box,
                af_sleep=self.click_sleep * uniform(0.8, 1.2)
            )
        return True

class ExecutorTryClickPicDisappear(Executor):
    def __init__(self, pic_name, det_to=0.5, wait_to=5):
        self.pic_name = pic_name
        self.det_to = det_to
        self.wait_to = wait_to
        super().__init__(name='图片点击消失({})'.format(pic_name))

    def _hit_optional(self, ctx: Ctx) -> bool:
        return True

    def _exec_optional(self, ctx: Ctx) -> bool:
        mdet = get_auto_core().loop_find_pics(self.pic_name, to=self.det_to)
        if not mdet.is_detected:
            return True

        check_interval = self.wait_to / 5
        to = Timeout(self.wait_to)
        while to.not_timeout():
            # 检查图片是否消失
            mdet = get_auto_core().loop_find_pics_not_exists(self.pic_name, to=check_interval)
            if not mdet.is_detected:
                return True
            logger.debug("[图片消失] 图片未消失, 重新点击, 检查次数: {}. ".format(self.pic_name, mdet.box, to.check_times))
            logger.debug("[图片消失] 点击图片({}), 区域: {}".format(self.pic_name, mdet.box))
            get_auto_core().left_click_in_box(mdet.box)
        logger.debug("[图片消失] 图片在指定时间内点击后仍然未消失, 图片：{}".format(self.pic_name))
        return False

class ExecutorPicDet(Executor):
    def __init__(self, pic_name, det_to=2, af_sleep=0):
        super().__init__(name='图片检测({})'.format(pic_name))
        self.pic_name = pic_name
        self.det_to = det_to
        self.af_sleep = af_sleep

    def _hit_optional(self, ctx: Ctx) -> bool:
        det = get_auto_core().loop_find_pics(self.pic_name, to=self.det_to)
        if not det.is_detected:
            return False
        return True

    def _exec_optional(self, ctx: Ctx) -> bool:
        sleep_with_rand(self.af_sleep)
        return True

class ExecutorPicNotExists(Executor):
    def __init__(self, pic_name, det_to=2, af_sleep=0):
        super().__init__(name='图片检测不存在({})'.format(pic_name))
        self.pic_name = pic_name
        self.det_to = det_to
        self.af_sleep = af_sleep

    def _hit_optional(self, ctx: Ctx) -> bool:
        det = get_auto_core().loop_find_pics(self.pic_name, to=self.det_to)
        if not det.is_detected:
            logger.debug('存在图片{},报错'.format(self.pic_name))
            return True
        return False

    def _exec_optional(self, ctx: Ctx) -> bool:
        sleep_with_rand(self.af_sleep)
        return True


class ExecutorPicDetAndMouseMove(Executor):
    def __init__(self, pic_name, distance, down=True,det_to=2, af_sleep=0):
        super().__init__(name='图片检测+滑轮移动({})'.format(pic_name))
        self.pic_name = pic_name
        self.det_to = det_to
        self.af_sleep = af_sleep
        self.down = down
        self.distance = distance

    def _hit_optional(self, ctx: Ctx) -> bool:
        det = get_auto_core().loop_find_pics(self.pic_name, to=self.det_to)
        if not det.is_detected:
            return False
        return True

    def _exec_optional(self, ctx: Ctx) -> bool:
        det = get_auto_core().loop_find_pics(self.pic_name, to=self.det_to)
        if not det.is_detected:
            return False
        point = det.box.get_rand_point()
        get_auto_core().wheel_move(self.down,self.distance, point)
        time.sleep(self.af_sleep)
        return True


class ExecutorPicDetNotExists(Executor):
    def __init__(self, pic_name, det_to=3):
        super().__init__(name='图片检测({})'.format(pic_name))
        self.pic_name = pic_name
        self.det_to = det_to


    def _hit_optional(self, ctx: Ctx) -> bool:
        return True

    def _exec_optional(self, ctx: Ctx) -> bool:
        mdet = get_auto_core().loop_find_pics_not_exists(self.pic_name, to=self.det_to)

        if mdet.is_detected:
            return False
        return True

class ExecutorPicDisappear(Executor):
    def __init__(self, pic_name, det_to=0, wait_to=5):
        super().__init__(name='图片检测({})'.format(pic_name))
        self.pic_name = pic_name
        self.det_to = det_to
        self.wait_to = wait_to

    def _hit_optional(self, ctx: Ctx) -> bool:
        det = get_auto_core().loop_find_pics(self.pic_name, to=self.det_to)
        if not det.is_detected:
            return False
        return True

    def _exec_optional(self, ctx: Ctx) -> bool:
        mdet = get_auto_core().loop_find_pics_not_exists(self.pic_name, to=self.wait_to)

        if mdet.is_detected:
            return False
        return True


class ExecutorPicTFSwitch(Executor):
    def __init__(self, true_pic, false_pic, want_true, det_to=2, use_max_score=True,af_sleep=0.5, click_area_rate=(0,0,1,1)):
        super().__init__(name='图片开关检测({}-{})[{}]'.format(true_pic, false_pic, want_true))
        self.want_true = want_true
        self.true_pic = true_pic
        self.false_pic = false_pic
        self.det_to = det_to
        self.af_sleep = af_sleep
        self.click_area_rate = click_area_rate
        self.use_max_score = use_max_score


    @property
    def pics_name(self):
        return [self.true_pic, self.false_pic]

    def _hit_optional(self, ctx: Ctx) -> bool:
        # 至少检测一张图片
        det = get_auto_core().loop_find_pics(self.pics_name, to=self.det_to, min_det_num=1)
        logger.debug('双图检测结果：{}'.format(det))
        if not det.is_detected:
            logger.debug('同时不存在两张图片：{}'.format(self.pics_name))
            return False
        if not self.use_max_score and det.check(includes=self.pics_name):
            logger.debug('不存在两张图片：{}'.format(self.pics_name))
            return False
        return True

    def _exec_optional(self, ctx: Ctx) -> bool:
        mdet = get_auto_core().loop_find_pics(self.pics_name, to=self.det_to, min_det_num=1)
        mdet.filter_not_top1_det() # 只保留分数最高的结果，解决了双图同时存在的问题(识别误差)
        to_click_pic = ''
        if self.want_true and mdet.check(includes=[self.false_pic]):
            to_click_pic = self.false_pic

        if not self.want_true and mdet.check(includes=[self.true_pic]):
            to_click_pic = self.true_pic

        if to_click_pic == '':
            return True

        box = mdet.get(to_click_pic).box
        box = box.crop_by_rate(self.click_area_rate[0], self.click_area_rate[1], self.click_area_rate[2], self.click_area_rate[3])

        logger.debug(f'为了达到目标({self.want_true}), 点击图片({to_click_pic}-{box})')
        get_auto_core().left_click_in_box(
            box,
            af_sleep=self.af_sleep * uniform(0.8, 1.2),
        )
        return True

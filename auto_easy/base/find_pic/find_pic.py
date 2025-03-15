import time

from auto_easy.base.find_pic import ConfBase
from auto_easy.base.find_pic.model import PicV2, PicDetV2, PicDetConf, DetBox, nms_boxes, MPicDetV2
from auto_easy.base.find_pic.pic_handler import *
from auto_easy.base.image.draw import show_image_table, show_multi_image
from auto_easy.base.image.process import contain_color
from auto_easy.constant import get_test_pic
from auto_easy.utils import concurrent_exec_one_func, logger


# 内部全部用cv2进行处理
def find_pic(source, search: PicV2, det_conf: PicDetConf = None) -> PicDetV2:

    pic_source = PicV2.new_auto(source)

    pic_search = PicV2.new_auto(search)
    conf: PicDetConf = ConfBase.new_conf_by_pry([PicDetConf(), pic_search.det_conf, det_conf])

    # TODO: 优化,记录历史匹配成功的scale,后续优先采纳
    if conf.range_scale is not None and conf.cur_scale is None:
        start = conf.range_scale[0]
        end = conf.range_scale[1]
        step = conf.range_scale[2]

        # 并发执行不同比例图片的匹配
        def _f(_conf):
            return find_pic(pic_source, pic_search, _conf)

        args = []
        for scale in np.arange(start, end, step):
            new_conf = conf.deepcopy()
            new_conf.range_scale = None
            new_conf.cur_scale = scale
            args.append(new_conf)
        if len(args) == 1:
            raise Exception('invalid range_scale, {}'.format(conf.range_scale))

        det_list = concurrent_exec_one_func(_f, args)
        # 合并结果
        first_det = det_list[0]
        first_det.merge_others(det_list[1:], dedup=True)
        return first_det

    cur_scale = conf.cur_scale if conf.cur_scale else 1

    # todo: 预留动态处理函数
    img_source = pic_source.cv2_img_bgr.copy()
    img_search = pic_search.cv2_img_bgr.copy()

    handlers = []

    # 根据参数加工图片
    if cur_scale != 1:
        handlers.append(PicResize(conf.cur_scale))

    if conf.color:
        handlers.append(PicColorKeep(conf.color))

    if not conf.rgb:
        handlers.append(PicColorGray())

    if conf.bg_remove:
        handlers.append(PicColorCanny())

    # 匹配区域, None/Box(0,0,0,0) 默认全屏
    match_box = conf.scaled_box if conf.box else None
    if match_box and not match_box.is_empty():
        handlers.append(PicCrop(match_box))  # 注: 这里是使用缩放后的区域进行裁剪

    his_source = []
    his_search = []
    titles = []
    for handler in handlers:
        img_source, img_search = handler.process(img_source, img_search)
        his_source.append(img_source)
        his_search.append(img_search)
        titles.append(handler.name)

        if conf.debug:
            logger.debug(f'img process: [{handler.name}]')

    if conf.debug:

        # print(len(his_source))
        show_multi_image(his_source)
        show_multi_image(his_search)
        # show_image_table([his_source, his_search], titles)

    method = conf.method
    if conf.rgb:
        s_bgr = cv2.split(img_source)  # Blue Green Red
        i_bgr = cv2.split(img_search)
        weight = (0.33, 0.33, 0.33)
        resbgr = [0, 0, 0]
        for i in range(3):  # bgr
            resbgr[i] = cv2.matchTemplate(i_bgr[i], s_bgr[i], method)
        res = resbgr[0] * weight[0] + resbgr[1] * weight[1] + resbgr[2] * weight[2]
    else:
        res = cv2.matchTemplate(img_source, img_search, method)

    w, h = img_search.shape[1], img_search.shape[0]
    yloc, xloc = np.where(res >= conf.sim)
    # 存储匹配结果
    det_boxes = []
    for (x, y) in zip(xloc, yloc):
        similarity = res[y, x]

        # 如果是区域匹配, 则变换为原图的坐标
        actual_x = x if match_box is None else x + match_box.x1
        actual_y = y if match_box is None else y + match_box.y1
        x1, y1, x2, y2 = actual_x, actual_y, actual_x + w, actual_y + h
        sim = float(format(similarity, ".2f"))
        # 将框添加到列表
        det_box = DetBox(
            sim,
            x1, y1, x2, y2
        )

        if len(conf.contain_color) > 0:
            crop_img = pic_source.cv2_img_bgr[y1:y2, x1:x2]
            cover_rate = contain_color(crop_img, conf.contain_color)
            if cover_rate <= 0.1:
                continue

        det_box.name = f'{pic_search.name}-{sim}'
        det_boxes.append(det_box)

    # 执行非极大值抑制, 主要用于消除检测算法输出中的多余重叠框
    det_boxes = nms_boxes(det_boxes)

    sorted_boxes = sorted(det_boxes, key=lambda box: box.sim, reverse=True)
    if not conf.multi_match:
        sorted_boxes = sorted_boxes[:1]

    pic_det = PicDetV2(
        pic_search,
        sorted_boxes,
        cur_scale
    )
    if conf.debug:
        pic_source.show(boxes=sorted_boxes)
    return pic_det


def find_pics_v2(source,
                 searches,
                 pic_det_conf: PicDetConf = None,
                 ) -> MPicDetV2:
    start = time.time()
    pic_source = PicV2.new_auto(source)
    pics_search = [PicV2.new_auto(search) for search in searches]
    if len(pics_search) == 0:
        return MPicDetV2()

    def _det_one(_pic_search):
        return find_pic(pic_source, _pic_search, pic_det_conf)

    det_list = concurrent_exec_one_func(_det_one, pics_search)
    mdet = MPicDetV2(det_list)
    return mdet


if __name__ == '__main__':
    conf = PicDetConf()
    # conf.rgb = False
    # conf.bg_remove = True
    conf.sim = 0.7
    conf.color = "160F09-030304"
    # conf.debug = True
    # conf.box = '778,381,812,416'
    conf.multi_match = True
    # conf.range_scale = '0.90,1.05,0.01'
    conf.cur_scale = 0.99
    det = find_pic(
        get_test_pic('debug/截图.bmp'),
        get_test_pic('debug/装备选项未选.bmp'),
        conf
    )
    print(det)

    # conf = default_det_conf.deepcopy()
    # conf.rgb = False
    # # conf.bg_remove = True
    # conf.sim = 0.8
    # # conf.debug = True
    # conf.multi_match = True
    # conf.range_scale = '0.99,1.01,0.01'
    #
    # det = find_pic(
    #     get_test_pic('find_pic/source_pic_2.bmp'),
    #     get_test_pic('find_pic/search_pic_2.bmp'),
    #     conf
    # )
    # print(det)
    # mdet = find_pics_v2(
    #     get_test_pic('find_pic/pics_source_1.jpg'),
    #     [
    #         get_test_pic('find_pic/pics_search_1_1.bmp'),
    #         get_test_pic('find_pic/pics_search_1_1.bmp'),
    #         PicV2.new_auto(get_test_pic('find_pic/pics_search_1_2.png'), name='search1_2'),
    #         PicV2.new_auto(get_test_pic('find_pic/pics_search_1_2$$$sim=0.7.bmp'), name='search1_2'),
    #     ]
    # )
    # print(mdet)
    # search1 = PicV2.new_auto(get_test_pic('find_pic/pics_search_1_1.bmp'), name='search')
    # search2 = PicV2.new_auto(get_test_pic('find_pic/pics_search_1_2.png'), name='search')
    # mdet = find_pics_v2(
    #     get_test_pic('find_pic/pics_source_1.jpg'),
    #     [
    #         search1,
    #         search2,
    #     ],
    #     pics_det_conf=mdet_conf,
    # )
    # print(mdet)

import cv2

from auto_easy.base.image.cvt import img_2_ndarray_rgb, img_2_ndarray_gbr
from auto_easy.constant import get_test_pic


def parse_color_range_bgr(color_deviation):
    """
    解析大漠偏色范围 (格式: 主色-偏差)
    Args:
        color_deviation (str): 偏色字符串，例如 "C28D3F-3D333E"

    Returns:
        tuple: 下限颜色范围 (BGR), 上限颜色范围 (BGR)
    """
    # 分割主色和偏差
    main_color_hex, deviation_hex = color_deviation.split('-')

    # 将主色和偏差转换为 BGR
    main_color = tuple(int(main_color_hex[i:i + 2], 16) for i in (4, 2, 0))  # 转为BGR顺序
    deviation = tuple(int(deviation_hex[i:i + 2], 16) for i in (4, 2, 0))  # 偏差同样转为BGR顺序

    # 计算下限和上限
    lower_bound = np.clip([m - d for m, d in zip(main_color, deviation)], 0, 255).astype(np.uint8)
    upper_bound = np.clip([m + d for m, d in zip(main_color, deviation)], 0, 255).astype(np.uint8)

    return lower_bound, upper_bound


def img_binarize(img, color_deviation, inverted=False):
    img = img_2_ndarray_rgb(img)

    lower_bound, upper_bound = parse_color_range_bgr(color_deviation)

    # 转为二值化
    binary_img = cv2.inRange(img, lower_bound, upper_bound)
    if inverted:
        inverted = cv2.bitwise_not(binary_img)
        return inverted
    return binary_img


def image_resize(img, scale_factor):
    new_size = (int(img.shape[1] * scale_factor), int(img.shape[0] * scale_factor))
    print(img.shape[1], img.shape[0])
    resized_img = cv2.resize(img, new_size, interpolation=cv2.INTER_CUBIC)
    print(resized_img.shape[1], resized_img.shape[0])
    return resized_img


def image_color_keep(img, color_deviation):
    img = img_2_ndarray_gbr(img)
    lower_bound, upper_bound = parse_color_range_bgr(color_deviation)

    # 创建掩模，保留在颜色范围内的所有像素
    result_image = np.zeros_like(img)
    color_mask = cv2.inRange(img, lower_bound, upper_bound)
    # 只保留掩模中为白色的部分
    result_image[color_mask > 0] = img[color_mask > 0]
    return result_image


import numpy as np
from skimage.metrics import structural_similarity as ssim


def compare_images(image1, image2):
    # 将 PIL Image 转换为 NumPy 数组
    img1 = img_2_ndarray_rgb(image1)
    img2 = img_2_ndarray_rgb(image2)

    # 检查两张图片的尺寸是否相同
    if img1.shape != img2.shape:
        raise ValueError("Images must have the same dimensions for SSIM.")

    # 计算 SSIM
    similarity_index, _ = ssim(img1, img2, win_size=3, full=True, multichannel=True)
    return similarity_index


def contain_color(img, color_range):
    """
    在图片中寻找符合条件的颜色范围，并计算面积占比
    :param image: 输入图片路径
    :param color_range: 偏差参数，格式如 "F7E97D-08123D"
    :return: 占比百分比
    """
    # 解析颜色区间
    lower_bound, upper_bound = parse_color_range_bgr(color_range)
    image = img_2_ndarray_gbr(img)

    # 根据颜色范围生成掩码
    mask = cv2.inRange(image, lower_bound, upper_bound)

    # 计算符合条件的像素数量
    matching_pixels = np.count_nonzero(mask)

    # 计算图片总像素数量
    total_pixels = image.shape[0] * image.shape[1]

    # 是否存在符合条件的颜色
    exists = matching_pixels > 0

    # 计算面积占比（百分比输出）
    area_percentage = (matching_pixels / total_pixels) * 100

    return round(area_percentage, 2)


if __name__ == '__main__':
    # img = image_color_keep()
    print(contain_color(get_test_pic('debug/cs.bmp'), 'BF7600-080700'))
    print(contain_color(get_test_pic('debug/wfcs.bmp'), 'BF7600-080700'))
    # path = r'E:\repo\dnf_tool\biz\det_pic\pics\选择角色\疲劳图标$$$box=86,324,96,338,宽高(10,14).bmp'
    # if not os.path.exists(path):
    #     print(f"File does not exist: {path}")
    # else:
    #     print(f"File found: {path}")
    # img = cv2.imread(path)
    # print(img)

    # img = image_color_keep(path,color_deviation='C4867F-3B777E')
    # cv2.imshow('img', img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # cv2.imwrite(gen_test_pic('lp'), img)
    # similarity_score = compare_images(get_test_pic('xlc.bmp'), get_test_pic('xlc.bmp'))
    # print("Images similarity score (SSIM):", similarity_score)
    # pass
    # sys.exit()
    # 读取输入图像
    # ori_path = 'test_pics/upscaled_image.jpg'
    # resize_path = 'test_pics/resized_img.bmp'
    # binary_path = 'test_picbinary_img.bmp'
    # img = cv2.imread(ori_path)
    #
    # ans = ai_ocr.predict(ori_path, scale_factor=1, allow_rpc=True)
    # print(ans)
    #
    # # 颜色偏差（例如来自大漠偏色计算器）
    # print('放大处理')
    # color_deviation = 'A27842-483B42'
    # color_deviation = '502A0D-482A0E' # 背景色
    # resized_img = image_resize(img, 10)
    # cv2.imwrite(resize_path, resized_img)
    # ans = ai_ocr.predict(resize_path, scale_factor=1, allow_rpc=True)
    # print(ans)
    #
    # # 调用函数处理
    # print('二值化处理')
    # binary_img = img_binarize(resized_img, color_deviation)
    # cv2.imwrite(binary_path, binary_img, )
    # ans = ai_ocr.predict(binary_path, scale_factor=1, allow_rpc=True)
    # print(ans)
    #
    # 保存结果
    # print("二值化处理完成，图像已保存为 binary_image.png")
    #
    # print("二值化处理完成，图像已保存为 resized_img2.png")

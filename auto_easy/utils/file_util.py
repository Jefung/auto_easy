from pathlib import Path

from PIL import Image


def is_image(file_path):
    try:
        img = Image.open(file_path)  # 尝试打开图像文件  
        img.verify()  # 验证文件是否损坏  
        return True
    except (IOError, SyntaxError):  # PIL无法识别的文件类型会抛出IOError  
        return False


def get_app_dir():
    app_data_roaming = os.getenv('APPDATA')
    return os.path.join(app_data_roaming, 'auto_easy')


def get_files(dir_path, file_prefix='', file_ext=''):
    res = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file_prefix != '' and not file.startswith(file_prefix):
                continue
            if file_ext != '' and not file.endswith(file_ext):
                continue
            abs_path = os.path.join(root, file)
            res.append(abs_path)
    return res


def get_statics_dir():
    current_path = Path(__file__).resolve()
    parent_path = current_path.parents[2]
    return os.path.join(parent_path, 'statics')


import requests
import os


def download_file(url, save_path) -> str:
    """
    此函数用于从指定的 URL 下载文件并保存到指定路径。

    :param url: 要下载文件的 URL
    :param save_path: 文件保存的路径
    :return: 如果下载成功返回 True，否则返回 False
    """
    try:
        # 发送 HTTP 请求，设置 stream=True 以支持流式下载
        response = requests.get(url, stream=True)
        # 检查响应状态码，确保请求成功
        response.raise_for_status()

        # 打开指定路径的文件以二进制写入模式
        with open(save_path, 'wb') as file:
            # 遍历响应内容的每个数据块
            for chunk in response.iter_content(chunk_size=8192):
                # 如果数据块不为空，则写入文件
                if chunk:
                    file.write(chunk)
        return ''
    except requests.RequestException as e:
        return f"下载文件时发生错误: {e}"
    except IOError as e:
        return f"保存文件时发生错误: {e}"


def must_get_file(filename, download_url=None):
    dirs = [
        get_statics_dir(),
        get_app_dir(),
    ]
    for d in dirs:
        file_path = os.path.join(d, filename)
        if os.path.exists(file_path):
            return file_path

    if download_url is not None:
        file_path = os.path.join(get_app_dir(), filename)
        err_msg = download_file(download_url, file_path)
        if err_msg != '':
            raise Exception(err_msg)
        return file_path

    raise Exception(f'file not found: {filename}')

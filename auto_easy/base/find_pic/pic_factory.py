import os

from auto_easy.base.find_pic.model import PicV2
from auto_easy.constant import TestPicDir
from auto_easy.utils import concurrent_exec_one_func
from auto_easy.utils.file_util import get_files, is_image


class PicFactory:
    def __init__(self, pic_dir=None):
        self.pic_list: list[PicV2] = []
        self._pic_dir = None
        if pic_dir:
            self.pic_dir = pic_dir

    @property
    def pic_dir(self):
        return self._pic_dir

    @pic_dir.setter
    def pic_dir(self, pic_dir):
        self._pic_dir = pic_dir
        self.load_all_pic()

    def _load_one_pic(self, path) -> PicV2:
        relative_path = os.path.relpath(path, self.pic_dir)
        relative_path = relative_path.replace("\\", "/")
        filename_without_ext = os.path.splitext(relative_path)[0]
        sp = filename_without_ext.split('$$$')
        if len(sp) < 1:
            raise Exception("图片命名格式错误: {}".format(path))
        pic_name = sp[0]
        return PicV2(name=pic_name, path=path)

    def load_all_pic(self):
        files = get_files(self.pic_dir)
        pic_file_list = [path for path in files if is_image(path)]
        pic_list = concurrent_exec_one_func(self._load_one_pic, pic_file_list)
        self.pic_list = pic_list

    def get_pic(self, name) -> PicV2:
        name = name.replace("\\", "/")
        for pic in self.pic_list:
            if pic.name == name:
                return pic
        return None

    def get_pics(self, name) -> list[PicV2]:
        name = name.replace("\\", "/")
        ans = []
        for pic in self.pic_list:
            if pic.name == name:
                ans.append(pic)
        return ans

    def get_pics_by_prefix(self, prefix) -> list[PicV2]:
        prefix = prefix.replace("\\", "/")
        ans = []
        for pic in self.pic_list:
            if pic.name.startswith(prefix):
                ans.append(pic)
        return ans

    def get_all_pics(self, prefix_excludes=None) -> list[PicV2]:
        prefix_excludes = [] if prefix_excludes is None else prefix_excludes
        ans = []
        for pic in self.pic_list:
            filter = False
            for pic_exclude in prefix_excludes:
                if pic.name.startswith(pic_exclude):
                    filter = True
                    break
            if not filter:
                ans.append(pic)

        return ans


if __name__ == '__main__':
    pic_factory = PicFactory()
    pic_factory.pic_dir = TestPicDir
    for pic in pic_factory.pic_list:
        print(pic)

    print(pic_factory.get_pic('find_pic\search_pic_1'))

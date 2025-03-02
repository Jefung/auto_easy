import os

TestPicDir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'test_pics')


def get_test_pic(pic_name):
    return os.path.join(TestPicDir, pic_name)


def gen_test_pic(pic_name):
    return os.path.join(TestPicDir, pic_name)

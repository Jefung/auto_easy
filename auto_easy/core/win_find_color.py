from auto_easy.base.find_color import find_color, find_best_color
from auto_easy.base.windows import Window


class WinFindColor(Window):
    def __init__(self, window_id=None, pic_dir=None):
        Window.__init__(self, window_id=window_id)

    def find_color(self, color, box=None) -> bool:
        img = self.capture_window()
        if box is not None:
            img = img.crop(box.tuple())
        exists, cover_rate = find_color(img, color)
        return exists

    def find_most_color(self, colors_offset, min_area_rate=0.0, box=None):
        screen = self.capture(box)
        return find_best_color(screen, colors_offset, min_area_rate)

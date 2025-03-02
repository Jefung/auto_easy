class Ctx:
    def __init__(self):
        pass


class DepInfo:
    def __init__(self, pic_includes=None, pic_excludes=None, ai_includes=None, ai_excludes=None):
        self.pic_includes = pic_includes if pic_includes is not None else []
        self.pic_excludes = pic_excludes if pic_excludes is not None else []
        self.ai_includes = ai_includes if ai_includes is not None else []
        self.ai_excludes = ai_excludes if ai_excludes is not None else []

    def merge_other(self, other):
        from auto_easy.utils import ab_union
        self.pic_includes = ab_union(self.pic_includes, other.pic_includes)
        self.pic_excludes = ab_union(self.pic_excludes, other.pic_excludes)
        self.ai_includes = ab_union(self.ai_includes, other.ai_includes)
        self.ai_excludes = ab_union(self.ai_excludes, other.ai_excludes)

    def merge_others(self, others):
        assert isinstance(others, list)
        for other in others:
            self.merge_other(other)

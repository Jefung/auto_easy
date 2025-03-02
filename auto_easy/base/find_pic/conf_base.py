import copy


class ConfItem:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class ConfBase:
    def __init__(self):
        self._property_set_dict = {}  # key为被设置的key
        self._test_property = None

    def __setattr__(self, name, value):
        if self.is_property_attr(name):
            self._property_set_dict[name] = ConfItem(name, value)
        super().__setattr__(name, value)  # 其他属性正常设置

    def is_property_attr(self, key):
        if not hasattr(self.__class__, key):
            return False
        if isinstance(getattr(self.__class__, key), property):
            return True
        return False

    def get_property_set_dict(self):
        return self._property_set_dict

    @property
    def test_property(self):
        return self._test_property

    @test_property.setter
    def test_property(self, value):
        self._test_property = value

    def copy(self):
        obj = copy.deepcopy(self)
        obj._property_set_dict = {}
        return obj

    @staticmethod
    def new_conf_by_pry(confs):
        confs = [conf for conf in confs if conf is not None]
        if len(confs) == 0:
            return None
        base_conf = confs[0].copy()
        for conf in confs[1:]:
            for item in conf.get_property_set_dict().values():
                setattr(base_conf, item.name, item.value)
        return base_conf


# 派生类
class DerivedClass(ConfBase):
    def __init__(self):
        super().__init__()
        self._value3 = None

    @property
    def value3(self):
        return self._value3

    @value3.setter
    def value3(self, new_value):
        self._value3 = new_value

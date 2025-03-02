import builtins


def is_class_name(obj, cls):
    mro_list = obj.__class__.__mro__
    mro_name_list = [c.__name__ for c in mro_list]
    return cls.__name__ in mro_name_list


def is_builtins(obj):
    return isinstance(obj, builtins.object)


def cls_to_dict(obj):
    if not hasattr(obj, '__dict__'):
        return obj
    d = vars(obj)
    for k, v in d.items():
        if isinstance(v, list) and len(v) > 0 and is_builtins(v[0]):
            for idx, list_val in enumerate(v):
                v[idx] = cls_to_dict(list_val)
            continue
        if is_builtins(v):
            d[k] = cls_to_dict(v)
            continue
    return d


def set_obj_by_dict(obj, d):
    for k, v in obj.__dict__.items():
        if k in d:
            setattr(obj, k, d[k])


# 判断是对象还是类
def is_cls(v):
    return isinstance(v, type)


def is_actual_subclass(subclass, superclass):
    subclass = subclass
    if not is_cls(subclass):
        subclass = subclass.__class__
    # 判断 subclass 是否是 superclass 的实际子类
    return subclass == superclass or (issubclass(subclass, superclass) and superclass in subclass.__mro__)

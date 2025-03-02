def a_rm_ab_intersect(a, b):
    """
    从数组A中剔除A和B的交集，返回处理后的数组
    """
    return [elem for elem in a if elem not in b]


def ab_intersect(a, b):
    return [x for x in a if x in b]


def ab_union(a, b):
    result = a.copy()
    for element in b:
        if element not in result:
            result.append(element)
    return result

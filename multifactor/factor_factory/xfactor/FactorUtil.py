import importlib


def get_factor_depend_data_types(factor_class_list):
    depend_data_types = set()
    for factor_class in factor_class_list:
        depend_data_types.update(factor_class.depend_data)
    return list(depend_data_types)


def get_factor_depend_factors(factor_class_list):
    depend_factors = set()
    for factor_class in factor_class_list:
        depend_factors.update(factor_class.depend_factors)
    return list(depend_factors)


def get_factor_depend_nonfactors(factor_class_list):
    depend_nonfactors = set()
    for factor_class in factor_class_list:
        depend_nonfactors.update(factor_class.depend_nonfactors)
    return list(depend_nonfactors)


def get_max_data_exceed(factor_class_list):
    return max([factor_class.lag + max(factor_class.reform_window - 1, 0) for factor_class in factor_class_list])


def get_class(kls):
    parts = kls.split(".")
    module = ".".join(parts[:-1])
    if check_module(module):
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)
        return m
    else:
        raise Exception("No factor module:" + module)


def check_module(module_name):
    """检查模块时候能被导入而不用实际的导入模块"""
    return importlib.util.find_spec(module_name)


def get_factor_module(factor_name):
    if check_module(".".join(["factor", factor_name])):
        return "factor"
    elif check_module(".".join(["nonfactor", factor_name])):
        return "nonfactor"
    else:
        return None


def get_factor_class(factor_name):
    module_name = get_factor_module(factor_name)
    if module_name:
        return get_class(".".join([module_name, factor_name, factor_name]))
    else:
        raise Exception("No factor found:" + factor_name)


def get_factor_class_list(factor_name_list):
    return [get_factor_class(factor_name) for factor_name in factor_name_list]


def is_same_freq_factor(factor_class_list):
    freq_set = set()
    for factor in factor_class_list:
        freq_set.add(factor.factor_type)
    return len(freq_set) == 1

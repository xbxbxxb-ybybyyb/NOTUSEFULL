# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     __init__.py
   Description :
   Author :       K0380044
   date：          2019/7/3
-------------------------------------------------
   Change Activity:
                   2019/7/3:
-------------------------------------------------
"""
import ray
from SmartFactor.logger import setup_logging
fac_logger = setup_logging("fac_logger")
from .MetaFactor import MetaBaseFactor
from .HFBaseFactor import HFBaseFactor
from .BaseFactor import Factor


def get_custom_factor_class(BaseFactorClass, class_attrs):
    factor_name = getattr(BaseFactorClass, "factor_name", '')
    if not factor_name:
        raise Exception("因子类名不存在：请为因子类{}设置factor_name！".format(BaseFactorClass))
    assert BaseFactorClass.__name__ == BaseFactorClass.factor_name, "因子名称冲突：因子类名{}与因子名{}不一致！".format(BaseFactorClass.__name__,factor_name)
    assert BaseFactorClass.__base__ == HFBaseFactor or BaseFactorClass.__base__ == Factor, "因子类{}的基类必须为HFBaseFactor或Factor！".format(BaseFactorClass)
    assert type
    return MetaBaseFactor(factor_name, (BaseFactorClass,), class_attrs)

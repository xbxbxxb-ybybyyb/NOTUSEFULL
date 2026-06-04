# _*_ coding:utf-8 _*_

from enum import IntEnum,unique


@unique
class KLINE_TYPE(IntEnum):
    K_1MIN    = 1             # 分钟K线
    K_DAY     = 2             # 日K线
    TICK      = 3             # tick数据







#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/3/31 14:04
from enum import Enum, unique


@unique
class DailyMonitor(Enum):
    NORMAL = 0
    MISSING = 1
    EMPTY = 2
    UNKOWN = 3

@unique
class MinuteMonitor(Enum):
    NORMAL = 0
    MISSING = 1
    EMPTY = 2
    UNKOWN = 3

@unique
class TickMonitor(Enum):
    NORMAL = 0
    MISSING = 1
    EMPTY = 2
    POSTPONE_NORMAL = 3
    POSTPONE_MISSING = 4
    UNKOWN = 5

@unique
class TransactionMonitor(Enum):
    NORMAL = 0
    MISSING = 1
    EMPTY = 2
    UNKOWN = 3

@unique
class OrderMonitor(Enum):
    NORMAL = 0
    MISSING = 1
    EMPTY = 2
    UNKOWN = 3
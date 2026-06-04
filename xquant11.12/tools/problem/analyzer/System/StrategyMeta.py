# Updated on 2018/7/16 by 010022 -- 改造以支持取跨日数据+并行化运算
# -*- coding: utf-8 -*-


class StrategyMeta:
    def __init__(self, strategy):
        self.__strategy = strategy
        self.__daysList = []

    # dayslist : List[List[]] 第一维是股票代码索引
    def setDaysList(self, daysList):
        self.__daysList = daysList

    def getStrategy(self):
        return self.__strategy

    def getDaysList(self, index):
        return self.__daysList[index]

    def getNumIntervals(self, index):
        return self.__daysList[index].__len__()

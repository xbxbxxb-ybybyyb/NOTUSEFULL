# -*- coding: utf-8 -*-


class MergeMeta:
    def __init__(self, strategyBase, strategyIndex, codeGroupIndex, numIntervals):
        """
        :param strategyIndex: int
        :param codeGroupIndex: int
        :param numIntervals: int the number of day lists
        """
        self.__strategyBase = strategyBase
        self.__strategyIndex = strategyIndex
        self.__codeGroupIndex = codeGroupIndex
        self.__numIntervals = numIntervals    # 一共有几个切分后的日期段，每个日期段都会生成一个文件

    def getStrategyBase(self):
        return self.__strategyBase

    def getStrategyIndex(self):
        return self.__strategyIndex

    def getCodeGroupIndex(self):
        return self.__codeGroupIndex

    def getNumIntervals(self):
        return self.__numIntervals

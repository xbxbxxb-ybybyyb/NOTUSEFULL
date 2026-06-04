# -*- coding: utf-8 -*-


class TaskMeta:
    """
    The meta info for a separate task.
    """
    def __init__(self, strategyBase, strategyIndex, codeGroupIndex, days, dayIndex):
        """
        :param strategyBase: StrategyBase
        :param strategyIndex: int
        :param codeGroupIndex: int
        :param days: list(str)
        :param dayIndex: int
        """
        self.__strategyBase = strategyBase
        self.__strategyIndex = strategyIndex
        self.__codeGroupIndex = codeGroupIndex
        self.__days = days
        self.__dayIndex = dayIndex    # 该任务的日期段是所有日期段中的第几个（从0开始）

    def getStrategyBase(self):
        return self.__strategyBase

    def getStrategyIndex(self):
        return self.__strategyIndex

    def getCodeGroupIndex(self):
        return self.__codeGroupIndex

    def getDays(self):
        return self.__days

    def getDayIndex(self):
        return self.__dayIndex

    def getTradingUnderlyingCode(self):
        return self.__strategyBase.getTradingUnderlyingCode()[self.__codeGroupIndex]

    def getFactorUnderlyingCode(self):
        return self.__strategyBase.getFactorUnderlyingCode()

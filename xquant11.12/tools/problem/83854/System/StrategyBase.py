# -*- coding: utf-8 -*-
from System.Strategy import Strategy


class StrategyBase:
    """
    Used to serialize the Strategies to the Spark Executors. This class is added because the Strategy class
    may be modified later, and it may contain some fields which cannot be serialized to the Executors. So,
    the StrategyBase class inherits the necessary fields from the Strategy class.
    """
    def __init__(self, strategy):
        self.__strategyName = strategy.getStrategyName()
        self.__tradingUnderlyingCode = strategy.getTradingUnderlyingCode()
        self.__factorUnderlyingCode = strategy.getFactorUnderlyingCode()
        self.__paraFactor = strategy.getParaFactor()
        self.__paraTag = strategy.getParaTag()
        self.__startDateTime = strategy.getStartDateTime()
        self.__endDateTime = strategy.getEndDateTime()

    def getStrategyName(self):
        return self.__strategyName

    def getTradingUnderlyingCode(self):
        return self.__tradingUnderlyingCode

    def getFactorUnderlyingCode(self):
        return self.__factorUnderlyingCode

    def getParaFactor(self):
        return self.__paraFactor

    def getParaTag(self):
        return self.__paraTag

    def getStartDateTime(self):
        return self.__startDateTime

    def getEndDateTime(self):
        return self.__endDateTime

    def toStrategy(self):
        strategy = Strategy()
        strategy.setStrategyName(self.__strategyName)
        strategy.setTradingUnderlyingCode(self.__tradingUnderlyingCode)
        strategy.setFactorUnderlyingCode(self.__factorUnderlyingCode)
        strategy.setParaFactor(self.__paraFactor)
        strategy.setParaTag(self.__paraTag)
        strategy.setStartDateTime(self.__startDateTime)
        strategy.setEndDateTime(self.__endDateTime)
        return strategy

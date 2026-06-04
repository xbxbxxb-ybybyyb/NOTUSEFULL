# -*- coding: utf-8 -*-


class Strategy:
    def __init__(self):
        self.__strategyName = ""
        self.__tradingUnderlyingCode = []
        self.__factorUnderlyingCode = []
        self.__paraFactor = []
        self.__paraTag = []
        self.__startDateTime = None
        self.__endDateTime = None

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

    def setStrategyName(self, strategyName):
        self.__strategyName = strategyName

    def setTradingUnderlyingCode(self, tradingUnderlyingCode):
        self.__tradingUnderlyingCode = tradingUnderlyingCode

    def setFactorUnderlyingCode(self, factorUnderlyingCode):
        self.__factorUnderlyingCode = factorUnderlyingCode

    def setParaFactor(self, paraFactor):
        self.__paraFactor = paraFactor

    def setParaTag(self, paraTag):
        self.__paraTag = paraTag

    def setStartDateTime(self, startDateTime):
        self.__startDateTime = startDateTime

    def setEndDateTime(self, endDateTime):
        self.__endDateTime = endDateTime

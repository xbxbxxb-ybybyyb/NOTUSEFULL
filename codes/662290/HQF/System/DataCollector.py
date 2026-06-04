# -*- coding: utf-8 -*-
"""
Created on Mon Aug  7 19:24:22 2017

@author: 006547
"""
from System.Data import Data


class DataCollector:
    def __init__(self, tradingUnderlyingCode, factorUnderlyingCode):
        self.__tradingUnderlyingData = []
        if len(tradingUnderlyingCode) > 0:
            for i in range(len(tradingUnderlyingCode)):
                self.__tradingUnderlyingData.append(Data())
        self.__factorUnderlyingData = []
        if len(factorUnderlyingCode) > 0:
            for i in range(len(factorUnderlyingCode)):
                self.__factorUnderlyingData.append(Data())
        self.__tradingUnderlyingCode = tradingUnderlyingCode[:]
        self.__factorUnderlyingCode = factorUnderlyingCode[:]

    def addSliceData(self, sliceData):
        for i in range(len(self.__tradingUnderlyingCode)):
            if sliceData.code == self.__tradingUnderlyingCode[i]:
                self.__tradingUnderlyingData[i].addData(sliceData, sliceData.timeStamp)
        for i in range(len(self.__factorUnderlyingCode)):
            if sliceData.code == self.__factorUnderlyingCode[i]:
                self.__factorUnderlyingData[i].addData(sliceData, sliceData.timeStamp)

    def getTradingUnderlyingData(self):
        return self.__tradingUnderlyingData

    def getFactorUnderlyingData(self):
        return self.__factorUnderlyingData

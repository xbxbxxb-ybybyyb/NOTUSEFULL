# -*- coding: utf-8 -*-
"""
Created on 2017/8/31 17:54

@author: 006547
"""
# Tag的基类，用于封装Tag获取行情和因子的接口


class BaseTag:
    def __init__(self, para, factorManagement):
        self.__factorManagement = factorManagement
        self.__indexTradingUnderlying = para['indexTradingUnderlying']
        self.__indexFactorUnderlying = para['indexFactorUnderlying']
        self.__tradingUnderlyingCode = self.__factorManagement.getTradingUnderlyingCode()
        self.__factorUnderlyingCode = self.__factorManagement.getFactorUnderlyingCode()
        # 获取数据和其他因子值的接口
        self.__tradingUnderlyingData = self.__factorManagement.getDataCollector().getTradingUnderlyingData()
        self.__factorUnderlyingData = self.__factorManagement.getDataCollector().getFactorUnderlyingData()

    def getFactorData(self, para):
        factor = self.__factorManagement.getFactorData(para)
        return factor

    def getTradingUnderlyingData(self, index):
        return self.__tradingUnderlyingData[index]

    def getFactorUnderlyingData(self, index):
        return self.__factorUnderlyingData[index]

    def getIndexTradingUnderlying(self):
        return self.__indexTradingUnderlying

    def getIndexFactorUnderlying(self):
        return self.__indexFactorUnderlying

    def getTradingUnderlyingCode(self):
        return self.__tradingUnderlyingCode

    def getFactorUnderlyingCode(self):
        return self.__factorUnderlyingCode

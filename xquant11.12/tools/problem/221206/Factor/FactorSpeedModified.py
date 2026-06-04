# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 22:27:59 2017

@author: 006547
"""
from System.Factor import Factor


class FactorSpeedModified(Factor):  # 因子类
    def __init__(self, para, factorManagement):  # 传入因子参数,归属的因子管理模块，需要用到的其他因子或非因子
        Factor.__init__(self, para, factorManagement)
        # 因子参数
        self.__paraEmaMidPriceLag = para['paraEmaMidPriceLag']
        self.__paraLag = para['paraLag']
        # 因子计算会用到的中间变量,取数据时候要注意会不会出现取出的因子还没有计算出值
        # 如果需要实例化因子作为中间变量，则name不要以factor开头，否则会输出到最终的结果中
        # 如果需要实例化因子或者非因子，需要考虑注册因子的先后顺序，即factorManagement.registerFactor(self)
        paraEmaMidPrice = {"name": "emaMidPrice", "className": "Ema",
                           "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                           "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                           "paraLag": self.__paraEmaMidPriceLag,
                           "paraOriginalData": {"name": "midPrice", "className": "MidPrice",
                                                "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__emaMidPrice = self.getFactorData(paraEmaMidPrice)
        factorManagement.registerFactor(self, para)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])

    def calculate(self):
        if len(self.__emaMidPrice.getContent()) > self.__paraLag:
            lastFactorSpeed = (self.__emaMidPrice.getLastContent() / self.__emaMidPrice.getContent()[
                int(-1 - self.__paraLag)] - 1) / (self.__paraLag / 20)
        else:
            lastFactorSpeed = (self.__emaMidPrice.getLastContent() / self.__emaMidPrice.getContent()[0] - 1) / (len(self.__emaMidPrice.getContent()) / 20)
        self.addData(lastFactorSpeed, self.__data.getLastTimeStamp())

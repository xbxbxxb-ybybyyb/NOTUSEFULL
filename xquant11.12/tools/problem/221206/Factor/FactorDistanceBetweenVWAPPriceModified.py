# -*- coding: utf-8 -*-
"""
Created on 2017/12/13 9:32

@author: 006547
"""
# 计算两个EMA之间的距离

from System.Factor import Factor
import numpy as np

class FactorDistanceBetweenVWAPPriceModified(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)

        self.__paraFastLag = para['paraFastLag']
        self.__paraSlowLag = para['paraSlowLag']

        paraVWAPPriceFast = {"name": "VWAPPriceFast", "className": "VWAPPrice",
                             "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                             "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                             "N": self.__paraFastLag}
        self.__VWAPPriceFast = self.getFactorData(paraVWAPPriceFast)
        paraVWAPPriceSlow = {"name": "VWAPPriceFast", "className": "VWAPPrice",
                             "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                             "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                             "N": self.__paraSlowLag}
        self.__VWAPPriceSlow = self.getFactorData(paraVWAPPriceSlow)

        factorManagement.registerFactor(self, para)

    def calculate(self):
        p_fast = self.__VWAPPriceFast.getLastContent()
        p_slow = self.__VWAPPriceSlow.getLastContent()
        if p_fast > 0.01 and p_slow > 0.01:
            lastFactor = 1000 * (p_fast - p_slow) / p_fast
        else:
            if len(self.getContent()) == 0:
                lastFactor = 0.0
            else:
                lastFactor = self.getLastContent()
        self.addData(lastFactor, self.__VWAPPriceFast.getLastTimeStamp())

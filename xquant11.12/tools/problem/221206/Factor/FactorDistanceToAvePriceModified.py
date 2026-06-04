"""
@author: 006688
计算当前中间价相对于全天成交均价的距离，即相对于黄色均线的位置
@ revised by 006566 on 2018/7/26
"""

from System.Factor import Factor
import numpy as np

class FactorDistanceToAvePriceModified(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__midPrice = self.getFactorData({"name": "midPrice", "className": "MidPrice",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        self.__avePrice = self.getFactorData({"name": "avePrice", "className": "AvePrice",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()})

        factorManagement.registerFactor(self, para)

    def calculate(self):
        midPrice = self.__midPrice.getLastContent()
        avePrice = self.__avePrice.getLastContent()
        if avePrice > 0.01 and midPrice > 0.01:
            value = midPrice / avePrice - 1
        else:
            if len(self.getContent()) == 0:
                value = 0.0
            else:
                value = self.getLastContent()
        self.addData(value, self.__midPrice.getLastTimeStamp())

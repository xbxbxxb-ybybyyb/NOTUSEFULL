# -*- coding: utf-8 -*-
"""
Created on 2019/8/27
@author: 006566 郑润泽
从OrderEvaluate中将AccAmountSell取出来
（注意用的是OrderEvaluate，而非OrderEvaluate2）
"""

from System.Factor import Factor


class FactorAccAmountSell(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        paraOrderEvaluate = {"name": "orderEvaluate", "className": "OrderEvaluate",
                             "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                             "indexFactorUnderlying": self.getIndexFactorUnderlying()}

        self.__paraOrderEvaluate = self.getFactorData(paraOrderEvaluate)
        factorManagement.registerFactor(self, para)

    def calculate(self):
        factorValue = self.__paraOrderEvaluate.getAccAmountSell()[-1]
        self.addData(factorValue, self.__data.getLastTimeStamp())

# -*- coding: utf-8 -*-
"""
Created on 2018/7/11 18:48
@author: 013050
@revised by 006566 2018/7/25
"""

from System.Factor import Factor
import math
import numpy as np

class FactorSellPower(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraMAAmountLag = para["paraMAAmountLag"]

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__historyAmount = self.getFactorData({"name": "historyAmount", "className": "HistoryAmount",
                                                   "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                   "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        paraOrderEvaluate = {"name": "orderEvaluate", "className": "OrderEvaluate2",
                             "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                             "indexFactorUnderlying": self.getIndexFactorUnderlying()}

        self.__paraOrderEvaluate = self.getFactorData(paraOrderEvaluate)
        self.__eps = 1e-5
        factorManagement.registerFactor(self, para)

    def calculate(self):
        accAskAmount = self.__paraOrderEvaluate.getAccAmountSell()[-1]
        maAmount  = np.mean(self.__historyAmount.getContent()[-self.__paraMAAmountLag:])
        if accAskAmount < 0.0 or maAmount <= 0.0:
            FactorValue = 0.0 
        else:
            FactorValue = math.log(accAskAmount / maAmount + self.__eps)  
        self.addData(FactorValue, self.__data.getLastTimeStamp())

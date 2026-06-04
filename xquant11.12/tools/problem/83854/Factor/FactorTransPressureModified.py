# -*- coding: utf-8 -*-
"""
Created on 2018/7/11 18:48
@author: 013050
@revised by 006566 2018/7/25
"""

from System.Factor import Factor
import math


class FactorTransPressureModified(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraDecayNum = para['paraDecayNum']
        self.__paraMALag = para['paraMALag']
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        paraTradeNumPressure = {"name": "TradeNumWeighted", "className": "TradeNumWeighted",
                                "paraDecayNum": self.__paraDecayNum,
                                "paraMALag": self.__paraMALag,
                                "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                "indexFactorUnderlying": self.getIndexFactorUnderlying()}
        self.__TradeNumPressure = self.getFactorData(paraTradeNumPressure)
        factorManagement.registerFactor(self, para)
        self.__TradeNumPressureBid = []
        self.__TradeNumPressureAsk = []
        self.__eps = 1e-5

    def calculate(self):
        PressureBid = self.__TradeNumPressure.getLastContent()[0]
        PressureAsk = self.__TradeNumPressure.getLastContent()[1]
        if PressureBid < 0 or PressureAsk < 0:
            FactorValue = 0.0
        else:
            FactorValue = math.log(PressureBid + self.__eps) - math.log(PressureAsk + self.__eps)
        self.__TradeNumPressureBid.append(PressureBid)
        self.__TradeNumPressureAsk.append(PressureAsk)
        self.addData(FactorValue, self.__data.getLastTimeStamp())

    def getNumPressureBid(self):
        return self.__TradeNumPressureBid

    def getNumPressureAsk(self):
        return self.__TradeNumPressureAsk

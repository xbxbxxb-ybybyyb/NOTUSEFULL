# -*- coding: utf-8 -*-
"""
Created on 2018/7/11 18:48
@author: 013050
@revised by 006566 2018/7/25
"""

from System.Factor import Factor
import math


class FactorTransPressureVolModified(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraDecayNum = para['paraDecayNum']
        self.__paraMALag = para['paraMALag']
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        paraTradeVolumePressure = {"name": "TradeVolumeWeighted", "className": "TradeVolumeWeighted",
                                   "paraDecayNum": self.__paraDecayNum,
                                   "paraMALag": self.__paraMALag,
                                   "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                   "indexFactorUnderlying": self.getIndexFactorUnderlying()}
        self.__TradeVolumePressure = self.getFactorData(paraTradeVolumePressure)
        factorManagement.registerFactor(self, para)
        self.__TradeVolumePressureBid = []
        self.__TradeVolumePressureAsk = []
        self.__eps = 1e-5
    def calculate(self):
        PressureBid = self.__TradeVolumePressure.getLastContent()[0]
        PressureAsk = self.__TradeVolumePressure.getLastContent()[1]
        if PressureBid < 0 or PressureAsk < 0:
            FactorValue = 0.0
        else:
            FactorValue = math.log(PressureBid + self.__eps) - math.log(PressureAsk + self.__eps)
        self.__TradeVolumePressureBid.append(PressureBid)
        self.__TradeVolumePressureAsk.append(PressureAsk)
        self.addData(FactorValue, self.__data.getLastTimeStamp())

    def getVolumePressureBid(self):
        return self.__TradeVolumePressureBid

    def getVolumePressureAsk(self):
        return self.__TradeVolumePressureAsk

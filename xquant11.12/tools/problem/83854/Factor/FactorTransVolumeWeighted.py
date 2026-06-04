# -*- coding: utf-8 -*-
"""
Created on 2018/7/11 18:48
@author: 013050
@revised by 006566 2018/7/25
"""

from System.Factor import Factor
import math


class FactorTransVolumeWeighted(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraDecayNum = para['paraDecayNum']
        self.__paraMALag = para['paraMALag']
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        paraTradeVolume = {"name": "TradeVolumeWeighted", "className": "TradeVolumeWeighted",
                                   "paraDecayNum": self.__paraDecayNum,
                                   "paraMALag": self.__paraMALag,
                                   "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                   "indexFactorUnderlying": self.getIndexFactorUnderlying()}
        self.__TradeVolume = self.getFactorData(paraTradeVolume)
        factorManagement.registerFactor(self, para)

    def calculate(self):
        VolumBid = self.__TradeVolume.getLastContent()[0]
        VolumAsk = self.__TradeVolume.getLastContent()[1]
        if VolumBid < 0 or VolumAsk < 0:
            FactorValue = 0.0
        else:
            FactorValue = VolumBid + VolumAsk
        self.addData(FactorValue, self.__data.getLastTimeStamp())


# -*- coding: utf-8 -*-
"""
Created on 2018/7/11 18:48
@author: 013050
@revised by 006566 2018/7/25
"""

from System.Factor import Factor
import math


class FactorTransBuyVolumeDistance(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraDecayNum = para['paraDecayNum']
        self.__paraMALag = para['paraMALag']
        self.__paraMAFastLag = para['paraMAFastLag']
        self.__paraMASlowLag = para['paraMASlowLag']
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        paraEmaTradeVolumeFast = {"name": "emaTradeVolumeFast", "className": "Ema",
                                    "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                    "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                    "paraLag": self.__paraMAFastLag,
                                    "paraOriginalData":{"name": "TradeVolumeWeighted", "className": "TradeVolumeWeighted",
                                           "paraDecayNum": self.__paraDecayNum,
                                           "paraMALag": self.__paraMALag,
                                           "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                           "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__EmaTradeVolumeFast = self.getFactorData(paraEmaTradeVolumeFast)
        paraEmaTradeVolumeSlow = {"name": "emaTradeVolumeSlow", "className": "Ema",
                                          "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                          "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                          "paraLag": self.__paraMASlowLag,
                                          "paraOriginalData": {"name": "TradeVolumeWeighted",
                                                               "className": "TradeVolumeWeighted",
                                                               "paraDecayNum": self.__paraDecayNum,
                                                               "paraMALag": self.__paraMALag,
                                                               "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                               "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__EmaTradeVolumeSlow = self.getFactorData(paraEmaTradeVolumeSlow)
        factorManagement.registerFactor(self, para)
        self.__eps = 1e-5
    def calculate(self):
        FastBidVolume = self.__EmaTradeVolumeFast.getLastContent()[0]
        SlowBidVolume = self.__EmaTradeVolumeSlow.getLastContent()[0]
        if FastBidVolume < 0 or SlowBidVolume < 0:
                FactorValue = 0.0
        else:
            FactorValue = math.log(FastBidVolume + self.__eps) - math.log(SlowBidVolume + self.__eps)
        self.addData(FactorValue, self.__data.getLastTimeStamp())
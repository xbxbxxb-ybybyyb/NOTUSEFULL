# -*- coding: utf-8 -*-
"""
Created on 2018/7/11 18:48
@author: 013050
@revised by 006566 2018/7/25
"""

from System.Factor import Factor
import math


class FactorTransVolumeWeightedSwing(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraDecayNum = para['paraDecayNum']
        self.__paraMALag = para['paraMALag']
        self.__paraDiffLag = para['paraDiffLag']
        self.__paraVolumeLag = para['paraVolumeLag']
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        paraEmaTradeVolumeDiff = {"name": "emaTradeVolumeDiff", "className": "Ema",
                                    "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                    "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                    "paraLag": self.__paraDiffLag,
                                    "paraOriginalData":{"name": "factorTransVolumeWeightedDiff", "className": "FactorTransVolumeWeightedDiff",
                                           "paraDecayNum": self.__paraDecayNum,
                                           "paraMALag": self.__paraMALag,
                                           "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                           "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__EmaTradeVolumeDiff = self.getFactorData(paraEmaTradeVolumeDiff)
        paraEmaTradeVolume = {"name": "emaTradeVolume", "className": "Ema",
                                          "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                          "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                          "paraLag": self.__paraVolumeLag,
                                          "paraOriginalData": {"name": "factorTransVolumeWeighted",
                                                               "className": "FactorTransVolumeWeighted",
                                                               "paraDecayNum": self.__paraDecayNum,
                                                               "paraMALag": self.__paraMALag,
                                                               "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                               "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__EmaTradeVolume = self.getFactorData(paraEmaTradeVolume)
        factorManagement.registerFactor(self, para)
    def calculate(self):
        DiffVolume = self.__EmaTradeVolumeDiff.getLastContent()
        TradeVolume = self.__EmaTradeVolume.getLastContent()
        if TradeVolume <= 0:
            FactorValue = 0.0
        else:
            FactorValue = DiffVolume / TradeVolume
        self.addData(FactorValue, self.__data.getLastTimeStamp())
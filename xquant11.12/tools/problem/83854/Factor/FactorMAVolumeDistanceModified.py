# -*- coding: utf-8 -*-
"""
Created on 2018/7/11 18:48

@author: 013050
"""

from System.Factor import Factor
import math
import numpy as np
class FactorMAVolumeDistanceModified(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraMAFastLag = para["paraMAFastLag"]
        self.__paraMASlowLag = para["paraMASlowLag"]

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__volume = self.getFactorData({"name": "volume", "className": "Volume",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()})

        self.__historyVolume = self.getFactorData({"name": "historyVolume", "className": "HistoryVolume",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        paraMAVolume = {"name": "MAVolume", "className": "MA",
                       "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                       "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                       "paraLag": self.__paraMAFastLag,
                       "paraOriginalData": {"name": "volume", "className": "Volume",
                                            "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                            "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__MAVolume = self.getFactorData(paraMAVolume)
        self.__eps = 1e-5
        factorManagement.registerFactor(self, para)

    def calculate(self):
        lastMAVolume = self.__MAVolume.getLastContent()
        slowMAVolume = np.mean(self.__historyVolume.getContent()[-self.__paraMASlowLag:])
        if lastMAVolume < 0 or slowMAVolume < 0:
            FactorValue = 0.0
        else:
            FactorValue = math.log((lastMAVolume + self.__eps) / (slowMAVolume + self.__eps))
        self.addData(FactorValue, self.__data.getLastTimeStamp())



# -*- coding: utf-8 -*-
"""
Created on 2018/7/11 18:48
@author: 013050
@revised by 006566 2018/7/25
"""

from System.Factor import Factor
import math
import numpy as np

class FactorDistanceToVwapPriceWeighted(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraMALongLag = para["paraMALongLag"]
        self.__paraMAShortLag = para["paraMAShortLag"]
        self.__paraMASlowLag = para["paraMASlowLag"]
        self.__paraMATinyLag = para["paraMATinyLag"]

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__historyAmount = self.getFactorData({"name": "historyAmount", "className": "HistoryAmount",
                                                   "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                   "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        self.__historyVolume = self.getFactorData({"name": "historyVolume", "className": "HistoryVolume",
                                                   "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                   "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        paraEmaMidPrice = {"name": "emaMidPrice", "className": "Ema",
                           "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                           "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                           "paraLag": self.__paraMATinyLag,
                           "paraOriginalData": {"name": "midPrice", "className": "MidPrice",
                                                "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__emaMidPrice = self.getFactorData(paraEmaMidPrice)
        paraEmaVolume = {"name": "emaVolume", "className": "Ema",
                         "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                         "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                         "paraLag": self.__paraMAShortLag,
                         "paraOriginalData": {"name": "volume", "className": "Volume",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__emaVolumeShort = self.getFactorData(paraEmaVolume)
        paraEmaVolume = {"name": "emaVolume", "className": "Ema",
                         "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                         "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                         "paraLag": self.__paraMALongLag,
                         "paraOriginalData": {"name": "volume", "className": "Volume",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__emaVolumeLong = self.getFactorData(paraEmaVolume)
        paraEmaVolume = {"name": "emaVolume", "className": "Ema",
                         "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                         "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                         "paraLag": self.__paraMATinyLag,
                         "paraOriginalData": {"name": "volume", "className": "Volume",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__emaVolumeTiny = self.getFactorData(paraEmaVolume)
        factorManagement.registerFactor(self, para)

    def calculate(self):
        ShortMAVolume = np.mean(self.__historyVolume.getContent()[-self.__paraMAShortLag:])
        LongMAVolume = np.mean(self.__historyVolume.getContent()[-self.__paraMALongLag:])
        SlowMAVolume = np.mean(self.__historyVolume.getContent()[-self.__paraMASlowLag:])
        EmaMidPrice = self.__emaMidPrice.getLastContent()
        if EmaMidPrice <= 0 or ShortMAVolume <= 0 or LongMAVolume <= 0 or SlowMAVolume <= 0:
            FactorValue = 0.0
        else:
            ShortVwapPrice = sum(self.__historyAmount.getContent()[-self.__paraMAShortLag:]) / sum(self.__historyVolume.getContent()[-self.__paraMAShortLag:])
            LongVwapPrice = sum(self.__historyAmount.getContent()[-self.__paraMALongLag:]) / sum(self.__historyVolume.getContent()[-self.__paraMALongLag:])
            
            LongEMAVolume = self.__emaVolumeLong.getLastContent()
            ShortEMAVolume = self.__emaVolumeLong.getLastContent()
            TinyEMAVolume = self.__emaVolumeLong.getLastContent()
            
            if LongVwapPrice <= 0 or ShortVwapPrice <= 0 or ShortEMAVolume <= 0 or TinyEMAVolume <= 0:
                FactorValue = 0.0
            else:
                FactorLong = 1000 * (1 - EmaMidPrice / LongVwapPrice) * math.sqrt((LongEMAVolume / TinyEMAVolume) / (LongMAVolume / SlowMAVolume))
                FactorShort = 1000 * (EmaMidPrice / ShortVwapPrice - 1) * math.sqrt((TinyEMAVolume / ShortEMAVolume) * (ShortMAVolume / SlowMAVolume))
                FactorValue = 0.5 * (FactorLong + FactorShort)

        self.addData(FactorValue, self.__data.getLastTimeStamp())

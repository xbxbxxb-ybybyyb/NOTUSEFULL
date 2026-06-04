# -*- coding: utf-8 -*-
"""
Created on 2018/4/12
@author: ZhuHaiGang
"""


from System.Factor import Factor
import numpy as np

class FactorDistanceToVwapModified(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraLag = para["paraLag"]

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__midPrice = self.getFactorData({"name": "midPrice", "className": "MidPrice",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        paraVWAPPrice = {"name": "VWAPPriceFast", "className": "VWAPPrice",
                             "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                             "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                             "N": self.__paraLag}
        self.__VWAPPrice = self.getFactorData(paraVWAPPrice)

        factorManagement.registerFactor(self, para)

    def calculate(self):
        lastData = self.__data.getLastContent()
        p_vwap = self.__VWAPPrice.getLastContent()
        p_mid = self.__midPrice.getLastContent()
        if p_vwap <= 0.01 or p_mid <= 0.01:
            if len(self.getContent()) == 0:
                distance = 0.0
            else:
                distance = self.getLastContent()
        else:
            distance = p_mid / p_vwap - 1
        self.addData(distance, lastData.timeStamp)



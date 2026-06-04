# -*- coding: utf-8 -*-
"""
Created on 2018/4/12
@author: ZhuHaiGang
"""


from System.Factor import Factor
import numpy as np

class FactorDistanceToHighModified(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraLag = para["paraLag"]

        self.__midPrice = self.getFactorData({"name": "midPrice", "className": "MidPrice",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        factorManagement.registerFactor(self, para)

    def calculate(self):
        length = min(len(self.__midPrice.getContent()), self.__paraLag)
        if length > 1:
            high_price = max(self.__midPrice.getContent()[-length:])
            is_not_valid = False

            if high_price < 0.01:
                is_not_valid = True

            if is_not_valid:
                if len(self.getContent()) == 0:
                    distance = 0.0
                else:
                    distance = self.getLastContent()
            else:
                distance = self.__midPrice.getLastContent() / high_price - 1
        else:
            distance = 0.0
        self.addData(distance, self.__midPrice.getLastTimeStamp())

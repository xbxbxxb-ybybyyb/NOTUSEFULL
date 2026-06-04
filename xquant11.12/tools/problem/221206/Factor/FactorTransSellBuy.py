# -*- coding: utf-8 -*-
# @Time    : 2018/7/11 10:30
# @Author  : 011673
# @File    : FactorSellPresure.py
from System.Factor import Factor
import math
import numpy as np


class FactorTransSellBuy(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__paraDecayNum = para['paraDecayNum']
        self.__transaction_distribution=self.getFactorData({'name':'transactionDistribution',
                                                            'className':'TransactionDistribution',
                                                            'paraDecayNum': self.__paraDecayNum,
                                                            "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                            "indexFactorUnderlying": self.getIndexFactorUnderlying()
                                                            })
        self.__paraLag = para['paraLag']
        self.__last_buy_vol = None
        self.__last_sell_vol = None
        self.__eps = 1e-5
        factorManagement.registerFactor(self, para)

    def calculate(self):
        self.__last_buy_vol = self.ema(self.__last_buy_vol, self.__transaction_distribution.getLastContent()[0], self.__paraLag)
        self.__last_sell_vol = self.ema(self.__last_sell_vol, self.__transaction_distribution.getLastContent()[2], self.__paraLag)
        if self.__last_buy_vol < 0 or self.__last_sell_vol < 0:
            val = 0.0
        else:
            val = math.log((self.__last_sell_vol + self.__eps) / (self.__last_buy_vol + self.__eps))
        self.addData(val, self.__data.getLastTimeStamp())

    def ema(self, last_ema, value, n):
        alpha = 2 / (n + 1)
        if last_ema is None:
            ema_pre = value
        else:
            ema_pre = last_ema
        ema_new = value * alpha + ema_pre * (1 - alpha)
        return (ema_new)
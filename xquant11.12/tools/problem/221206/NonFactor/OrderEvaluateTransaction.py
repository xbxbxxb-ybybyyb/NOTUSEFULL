# -*- coding: utf-8 -*-
"""
Created on 2018/7/11 9:27

@author: 006547
"""


import numpy as np

from System.Factor import Factor


class OrderEvaluateTransaction(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__midPrice = self.getFactorData({"name": "midPrice", "className": "MidPrice",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        factorManagement.registerFactor(self, para)
        self.__AccAmountBuy = []  # 存放买压
        self.__AccAmountSell = []  # 存放卖压

    def calculate(self):
        factorValue = [0, 0]
        if len(self.__data.getContent()) > 1:
            dataNow = self.__data.getLastContent()  # 当前切片数据
            transactionData = np.array(dataNow.transactionData)

            if len(transactionData) > 0:
                # 利用还原出的当前切片的委托，计算买卖压
                OrderAmount = (transactionData[:, 3] * transactionData[:, 4]) / (1 + np.exp(-1000 * transactionData[:, 2] * (transactionData[:, 3] / self.__midPrice.getContent()[-2] - 1)))
                OrderAmountBuy = sum(OrderAmount[transactionData[:, 2] == 1])
                OrderAmountSell = sum(OrderAmount[transactionData[:, 2] != 1])

                self.__AccAmountBuy.append(OrderAmountBuy)
                self.__AccAmountSell.append(OrderAmountSell)
                factorValue = [OrderAmountBuy, OrderAmountSell]
        self.addData(factorValue, self.__data.getLastTimeStamp())

    def getAccAmountBuy(self):
        return self.__AccAmountBuy

    def getAccAmountSell(self):
        return self.__AccAmountSell

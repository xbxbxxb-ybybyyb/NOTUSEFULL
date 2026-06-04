# -*- coding: utf-8 -*-
"""
Created on 2019/8/27
@author: 006566 郑润泽
TradeNum 逐笔成交中成交的数量
"""

from System.Factor import Factor


class FactorTradeNum(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        factorManagement.registerFactor(self, para)

    def calculate(self):
        transaction_data = self.__data.getLastContent().transactionData
        factor_value = transaction_data.__len__()
        self.addData(factor_value, self.__data.getLastTimeStamp())

# -*- coding: utf-8 -*-
"""
Created on 2019/8/27
@author: 006566 郑润泽
TradeNum 逐笔成交中主买成交的金额
"""

from System.Factor import Factor


class FactorBuyTradeAmt(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        factorManagement.registerFactor(self, para)

    def calculate(self):
        transaction_data = self.__data.getLastContent().transactionData
        factor_value = 0
        if transaction_data.__len__() > 0:
            for i_trade_recode in transaction_data:
                # 每条交易记录有5条内容：(0,1) 买 / 卖委托号、(2)方向、(3)价格、(4)数量
                if i_trade_recode[2] == 1:
                    factor_value += (i_trade_recode[4] * i_trade_recode[3])
        self.addData(factor_value, self.__data.getLastTimeStamp())

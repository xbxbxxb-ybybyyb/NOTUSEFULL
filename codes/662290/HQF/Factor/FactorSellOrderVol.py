# -*- coding: utf-8 -*-
"""
Created on 2019/8/27
@author: 006566 郑润泽
OrderEvaluate中提取虚拟委托订单，汇总新增卖委托量
"""

from System.Factor import Factor


class FactorSellOrderVol(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        paraOrderEvaluate = {"name": "orderEvaluate", "className": "OrderEvaluate",
                             "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                             "indexFactorUnderlying": self.getIndexFactorUnderlying()}

        self.__paraOrderEvaluate = self.getFactorData(paraOrderEvaluate)
        factorManagement.registerFactor(self, para)

    def calculate(self):
        OrderBookTmp = self.__paraOrderEvaluate.getOrderBook()
        factorValue = 0
        # 订单示例: [1534728619, 634.0, 3200.0, 'B']
        if OrderBookTmp[-1].__len__() > 0:
            for i_order in OrderBookTmp[-1]:
                if i_order[3] == 'S':
                    factorValue += i_order[2]
        self.addData(factorValue, self.__data.getLastTimeStamp())

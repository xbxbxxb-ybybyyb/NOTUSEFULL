# -*- coding: utf-8 -*-
"""
Created on 2019/8/27
@author: 006566 郑润泽
OrderEvaluate中提取虚拟委托订单，汇总新增买委托量，对于低于上个Tick中间价的，即认为是消极委托
"""

from System.Factor import Factor


class FactorPassiveBuyOrderVol(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        paraOrderEvaluate = {"name": "orderEvaluate", "className": "OrderEvaluate",
                             "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                             "indexFactorUnderlying": self.getIndexFactorUnderlying()}
        self.__paraOrderEvaluate = self.getFactorData(paraOrderEvaluate)
        self.__midPrice = self.getFactorData({"name": "midPrice", "className": "MidPrice",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        factorManagement.registerFactor(self, para)

    def calculate(self):
        OrderBookTmp = self.__paraOrderEvaluate.getOrderBook()
        factorValue = 0
        midPrice = self.__midPrice.getContent()
        if midPrice.__len__() >= 2:
            lastMidPrice = midPrice[-2]
            # 订单示例: [1534728619, 634.0, 3200.0, 'B']
            if OrderBookTmp[-1].__len__() > 0:
                for i_order in OrderBookTmp[-1]:
                    if i_order[3] == 'B' and i_order[1] < lastMidPrice:
                        factorValue += i_order[2]
        else:
            factorValue = 0
        self.addData(factorValue, self.__data.getLastTimeStamp())

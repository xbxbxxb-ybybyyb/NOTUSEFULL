# -*- coding: utf-8 -*-
"""
@author: 006566
过去N个tick的VWAP
1. 如果过去的tick数 < N，那么tick_len = 过去的tick数；如过去的tick数 >= n，那么tick_len = N
2. VWAP = 过去tick_len的 amount / volume；如分母为0，则沿用前值，如没有前值，则用中间价
最极端的情况可以试退市的股票，例如000511.SZ - 2018/6/11，全天只成交了3笔共12手
"""

from System.Factor import Factor


class VWAPPrice(Factor):  # 非因子类，利用率较高的中间变量
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        # 因子参数
        self.__n = para["N"]
        factorManagement.registerFactor(self, para)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__midPrice = self.getFactorData(
            {"name": "midPrice", "className": "MidPrice", "indexTradingUnderlying": self.getIndexTradingUnderlying(),
             "indexFactorUnderlying": self.getIndexFactorUnderlying()})

    def calculate(self):
        if self.__data.getContent().__len__() <= self.__n:
            tick_len = self.__data.getContent().__len__()
        else:
            tick_len = self.__n
        total_amount = 0
        total_volume = 0
        for i in range(tick_len):
            total_amount += self.__data.getContent()[-i-1].amount
            total_volume += self.__data.getContent()[-i-1].volume
        if total_volume > 0:  # 如分母（交易量）不为0，则以交易额/交易量
            vwapPrice = total_amount / total_volume
        elif self.getLastContent() > 0:  # 如分母（交易量）为0，则优先取前值
            vwapPrice = self.getLastContent()
        else:  # 如前值也为0，则以中间价代替
            vwapPrice = self.__midPrice.getLastContent()

        self.addData(vwapPrice, self.__data.getLastTimeStamp())

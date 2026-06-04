# -*- coding: utf-8 -*-
"""
Created on Tue Aug  8 10:45:37 2017

@author: 006547
"""

from System.Factor import Factor


class MidPrice(Factor):  # 非因子类，利用率较高的中间变量
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        # 因子计算会用到的中间变量,取数据时候要注意会不会出现取出的因子还没有计算出值
        # 如果需要实例化因子作为中间变量，则name不要以factor开头，否则会输出到最终的结果中
        # 如果需要实例化因子或者非因子，需要考虑注册因子的先后顺序，即factorManagement.registerFactor(self)
        factorManagement.registerFactor(self, para)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])

    def calculate(self):
        lastData = self.__data.getLastContent()
        if lastData.askPrice[0] == 0 or lastData.bidPrice[0] == 0:
            lastMidPrice = self.getLastContent()
            if lastMidPrice == 0:
                if lastData.askPrice[0] != 0:
                    lastMidPrice = lastData.askPrice[0]
                if lastData.bidPrice[0] != 0:
                    lastMidPrice = lastData.bidPrice[0]
        else:
            lastMidPrice = (lastData.askPrice[0] + lastData.bidPrice[0]) / 2
        self.addData(lastMidPrice, lastData.timeStamp)

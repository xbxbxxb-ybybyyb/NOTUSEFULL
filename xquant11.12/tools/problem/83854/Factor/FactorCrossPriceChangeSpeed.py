# -*- coding: utf-8 -*-
"""
Created on 2018/7/14 15:41

@author: 013050
"""
# 当前这波趋势的涨跌幅
from System.Factor import Factor


class FactorCrossPriceChangeSpeed(Factor):
    def __init__(self, para, factorManagement):  # 传入因子参数,归属的因子管理模块，需要用到的其他因子或非因子
        Factor.__init__(self, para, factorManagement)
        # 因子参数
        self.__paraFastLag = para['paraFastLag']
        self.__paraSlowLag = para['paraSlowLag']
        # 因子计算会用到的中间变量,取数据时候要注意会不会出现取出的因子还没有计算出值
        # 如果需要实例化因子作为中间变量，则name不要以factor开头，否则会输出到最终的结果中
        # 如果需要实例化因子或者非因子，需要考虑注册因子的先后顺序，即factorManagement.registerFactor(self)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__crossPoint = self.getFactorData({"name": "crossPoint", "className": "CrossPoint",
                                                  "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                  "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                                  "paraFastLag": self.__paraFastLag, "paraSlowLag": self.__paraSlowLag})
        factorManagement.registerFactor(self, para)

    def calculate(self):
        self.addData(20*self.__crossPoint.getLastContent()[1], self.__data.getLastTimeStamp())

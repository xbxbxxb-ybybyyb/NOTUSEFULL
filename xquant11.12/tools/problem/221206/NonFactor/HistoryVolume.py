# -*- coding: utf-8 -*-
"""
Created on 2018/7/12 10:43

@author: 013050
"""
# 成交量
from System.Factor import Factor


class HistoryVolume(Factor):  # 非因子类，利用率较高的中间变量
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        # 因子计算会用到的中间变量,取数据时候要注意会不会出现取出的因子还没有计算出值
        # 如果需要实例化因子作为中间变量，则name不要以factor开头，否则会输出到最终的结果中
        # 如果需要实例化因子或者非因子，需要考虑注册因子的先后顺序，即factorManagement.registerFactor(self)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__isHistoryLoaded = False
        self.__volume = self.getFactorData({"name": "volume", "className": "Volume",
                                            "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                            "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        factorManagement.registerFactor(self, para)

    def calculate(self):
        if not self.__isHistoryLoaded:
            self.__isHistoryLoaded = True
            slice_data = self.getPreDayTicks()
            if slice_data is not None:
                for i in range(len(slice_data)):
                    self.addData(slice_data[i].volume, slice_data[i].timeStamp)

        self.addData(self.__volume.getLastContent(), self.__data.getLastTimeStamp())








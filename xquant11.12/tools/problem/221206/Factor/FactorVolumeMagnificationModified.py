# -*- coding: utf-8 -*-
"""
Created on 2017/8/31 10:56

@author: 006547
"""
from System.Factor import Factor
import math

class FactorVolumeMagnificationModified(Factor):
    def __init__(self, para, factorManagement):  # 传入因子参数,归属的因子管理模块，需要用到的其他因子或非因子
        Factor.__init__(self, para, factorManagement)
        self.__paraFastLag = para['paraFastLag']
        self.__paraSlowLag = para['paraSlowLag']
        # 因子计算会用到的中间变量,取数据时候要注意会不会出现取出的因子还没有计算出值
        # 如果需要实例化因子作为中间变量，则name不要以factor开头，否则会输出到最终的结果中
        # 如果需要实例化因子或者非因子，需要考虑注册因子的先后顺序，即factorManagement.registerFactor(self)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        paraEmaVolume = {"name": "emaVolume", "className": "Ema",
                         "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                         "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                         "paraLag": self.__paraFastLag,
                         "paraOriginalData": {"name": "volume", "className": "Volume",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__emaVolumeFast = self.getFactorData(paraEmaVolume)
        paraEmaVolume = {"name": "emaVolume", "className": "Ema",
                         "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                         "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                         "paraLag": self.__paraSlowLag,
                         "paraOriginalData": {"name": "volume", "className": "Volume",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__emaVolumeSlow = self.getFactorData(paraEmaVolume)
        self.__eps = 1e-5
        factorManagement.registerFactor(self, para)

    def calculate(self):
        fast_vol = self.__emaVolumeFast.getLastContent()
        slow_vol = self.__emaVolumeSlow.getLastContent()
        if fast_vol < 0 or slow_vol < 0:
            factorValue = 0.0
        else:
            factorValue = math.log((fast_vol + self.__eps) / (slow_vol + self.__eps))
        self.addData(factorValue, self.__data.getLastTimeStamp())

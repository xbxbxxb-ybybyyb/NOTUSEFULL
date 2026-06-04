# -*- coding: utf-8 -*-
"""
Created on 2018/1/29 19:24

@author: 006547
"""
from System.Factor import Factor


class OrderBookMultiple(Factor):  # 盘口numOrder档新增单相对于平均挂单量的倍数
    def __init__(self, para, factorManagement):  # 传入因子参数,归属的因子管理模块，需要用到的其他因子或非因子
        Factor.__init__(self, para, factorManagement)
        # 因子参数
        self.__paraNumOrderMax = para['paraNumOrderMax']
        self.__paraNumOrderMin = para['paraNumOrderMin']
        self.__paraNumOrderMaxForAveOrderVolume = para["paraNumOrderMaxForAveOrderVolume"]
        self.__paraNumOrderMinForAveOrderVolume = para["paraNumOrderMinForAveOrderVolume"]
        self.__paraEmaAveOrderVolumeLag = para['paraEmaAveOrderVolumeLag']
        # 因子计算会用到的中间变量,取数据时候要注意会不会出现取出的因子还没有计算出值
        # 如果需要实例化因子作为中间变量，则name不要以factor开头，否则会输出到最终的结果中
        # 如果需要实例化因子或者非因子，需要考虑注册因子的先后顺序，即factorManagement.registerFactor(self)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])

        self.__aveOrderVolume = self.getFactorData({"name": "aveOrderVolume", "className": "AveOrderVolume",
                                                    "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                    "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                                    "paraNumOrderMax": self.__paraNumOrderMax,
                                                    "paraNumOrderMin": self.__paraNumOrderMin})

        paraEmaAveOrderVolume = {"name": "emaAveOrderVolume", "className": "Ema",
                                 "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                 "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                 "paraLag": self.__paraEmaAveOrderVolumeLag,
                                 "paraOriginalData": {"name": "aveOrderVolume", "className": "AveOrderVolume",
                                                      "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                      "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                                      "paraNumOrderMax": self.__paraNumOrderMaxForAveOrderVolume,
                                                      "paraNumOrderMin": self.__paraNumOrderMinForAveOrderVolume}}
        self.__emaAveOrderVolume = self.getFactorData(paraEmaAveOrderVolume)
        factorManagement.registerFactor(self, para)

    def calculate(self):
        askOrderBookMultiple = 0
        bidOrderBookMultiple = 0
        aveVolumeBid = self.__aveOrderVolume.getLastContent()[0]  # N档买盘的平均挂单量
        aveVolumeAsk = self.__aveOrderVolume.getLastContent()[1]  # N档卖盘的平均挂单量
        if self.__emaAveOrderVolume.getLastContent()[0] != 0:
            bidOrderBookMultiple = aveVolumeBid / self.__emaAveOrderVolume.getLastContent()[0]
        if self.__emaAveOrderVolume.getLastContent()[1] != 0:
            askOrderBookMultiple = aveVolumeAsk / self.__emaAveOrderVolume.getLastContent()[1]

        factorValue = [bidOrderBookMultiple, askOrderBookMultiple]
        self.addData(factorValue, self.__data.getLastTimeStamp())

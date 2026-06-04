# -*- coding: utf-8 -*-
"""
Created on 2018/6/12 14:41
通过OrderEvaluate还原委托，与benchmarkPrice比较，统计主动成交的买量和卖量
@author: 006566
"""
from System.Factor import Factor
import math
import numpy as np

class ActiveVol(Factor):
    def __init__(self, para, factorManagement):  # 传入因子参数,归属的因子管理模块，需要用到的其他因子或非因子
        Factor.__init__(self, para, factorManagement)
        # 因子参数
        # 因子计算会用到的中间变量,取数据时候要注意会不会出现取出的因子还没有计算出值
        # 如果需要实例化因子作为中间变量，则name不要以factor开头，否则会输出到最终的结果中
        # 如果需要实例化因子或者非因子，需要考虑注册因子的先后顺序，即factorManagement.registerFactor(self)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__orderEvaluate = self.getFactorData({"name": "orderEvaluate", "className": "OrderEvaluate",
                                                   "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                   "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        self.__benchmarkPriceType = para["benchmarkPriceType"]
        self.__benchmarkPriceLag = para["benchmarkPriceLag"]

        self.__paraMAVolumeLag = para["paraMAVolumeLag"]
        self.__historyVolume = self.getFactorData({"name": "historyVolume", "className": "HistoryVolume",
                                                   "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                   "indexFactorUnderlying": self.getIndexFactorUnderlying()})

        paraMAPrice = {"name": "MAPrice", "className": "MA",
                       "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                       "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                       "paraLag": self.__benchmarkPriceLag,
                       "paraOriginalData": {"name": "midPrice", "className": "MidPrice",
                                            "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                            "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__MAPrice = self.getFactorData(paraMAPrice)
        self.__eps = 1e-5
        factorManagement.registerFactor(self, para)

    def calculate(self):
        OrderBook = self.__orderEvaluate.getOrderBook()[-1]  # 通过orderEvaluate获取订单流簿
        activeVolBuy = 0
        activeVolSell = 0
        keyAskP = 0
        if OrderBook.__len__() > 0:
            if self.__benchmarkPriceType == "P1":  # 如基准价格的类型是"P1"，则以买卖1档作为keyAskP和keyBidP
                keyAskP = self.__data.getContent()[-2].askPrice[0]  # 上个tick的卖1价
                keyBidP = self.__data.getContent()[-2].bidPrice[0]  # 上个tick的买1价
            elif self.__benchmarkPriceType == "MA":  # 如基准价格的类型是"MA"，则以均价作为keyAskP和keyBidP
                keyAskP = self.__MAPrice.getContent()[-2]
                keyBidP = self.__MAPrice.getContent()[-2]
            for iOrder in OrderBook:  # 将订单流簿中的订单遍历
                if iOrder[1] >= keyAskP and iOrder[3] == "B":  # 若有大于等于keyAskP的买单，则记为主动买单
                    activeVolBuy += iOrder[2]
                elif iOrder[1] <= keyBidP and iOrder[3] == "S":
                    activeVolSell += iOrder[2]

        if activeVolBuy < 0 or activeVolSell < 0:
            factorValue = [0.0, 0.0, 0.0]
        else:
            factorValue = [activeVolBuy, activeVolSell, math.log((activeVolBuy + self.__eps) / (activeVolSell + self.__eps))]

        if len(self.__historyVolume.getContent()) <= self.__paraMAVolumeLag:
            factorValue[0] = float(len(self.__historyVolume.getContent()) * factorValue[0]) / sum(self.__historyVolume.getContent())
            factorValue[1] = float(len(self.__historyVolume.getContent()) * factorValue[1]) / sum(
                self.__historyVolume.getContent())
        else:
            factorValue[0] = float(self.__paraMAVolumeLag * factorValue[0]) / sum(
                self.__historyVolume.getContent()[-self.__paraMAVolumeLag:])
            factorValue[1] = float(self.__paraMAVolumeLag * factorValue[1]) / sum(
                self.__historyVolume.getContent()[-self.__paraMAVolumeLag:])

        self.addData(factorValue, self.__data.getLastTimeStamp())

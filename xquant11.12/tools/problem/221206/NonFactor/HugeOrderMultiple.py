# -*- coding: utf-8 -*-
"""
Created on 2017/9/6 8:55

@author: 006547
"""
import numpy as np
from System.Factor import Factor


class HugeOrderMultiple(Factor):  # 盘口numOrder档新增单相对于平均挂单量的倍数
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
        self.__orderEvaluate = self.getFactorData({"name": "orderEvaluate", "className": "OrderEvaluate",
                                                   "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                   "indexFactorUnderlying": self.getIndexFactorUnderlying()})
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
        askHugeOrderMultiple = 0
        bidHugeOrderMultiple = 0
        OrderBook = self.__orderEvaluate.getOrderBook()[-1]
        if OrderBook.__len__() > 0:
            # 分析卖盘
            volumeB = 0
            volumeS = 0
            volumeC = 0
            orderPriceList = []
            orderVolumeList = []
            orderDirectionList = []
            for iOrder in OrderBook:
                orderPriceList.append(iOrder[1])
                orderVolumeList.append(iOrder[2])
                orderDirectionList.append(iOrder[3])
            askPrice = np.array(self.__data.getLastContent().askPrice)
            numOrderAskPrice = askPrice[self.__paraNumOrderMin-1:self.__paraNumOrderMax]
            if numOrderAskPrice.__len__() > 0:
                for iNumOrderAskPrice in numOrderAskPrice:
                    position = np.argwhere(orderPriceList == iNumOrderAskPrice)
                    if position.__len__() >= 1:
                        if orderDirectionList[int(position[0][0])] == "B":
                            volumeB += orderVolumeList[int(position[0][0])]
                        if orderDirectionList[int(position[0][0])] == "S":
                            volumeS += orderVolumeList[int(position[0][0])]
                        if orderDirectionList[int(position[0][0])] == "C":
                            volumeC += orderVolumeList[int(position[0][0])]
            if self.__emaAveOrderVolume.getLastContent()[1] != 0:
                askHugeOrderMultiple = (volumeS - volumeB - volumeC) / self.__emaAveOrderVolume.getLastContent()[1]
            else:
                askHugeOrderMultiple = 0
            # 分析买盘
            volumeB = 0
            volumeS = 0
            volumeC = 0
            bidPrice = np.array(self.__data.getLastContent().bidPrice)
            numOrderBidPrice = bidPrice[self.__paraNumOrderMin-1:self.__paraNumOrderMax]
            if numOrderBidPrice.__len__() > 0:
                for iNumOrderBidPrice in numOrderBidPrice:
                    position = np.argwhere(orderPriceList == iNumOrderBidPrice)
                    if position.__len__() == 1:
                        if orderDirectionList[int(position[0][0])] == "B":
                            volumeB += orderVolumeList[int(position[0][0])]
                        if orderDirectionList[int(position[0][0])] == "S":
                            volumeS += orderVolumeList[int(position[0][0])]
                        if orderDirectionList[int(position[0][0])] == "C":
                            volumeC += orderVolumeList[int(position[0][0])]
                    elif position.__len__() > 1:
                        if orderDirectionList[int(position[-1][0])] == "B":
                            volumeB += orderVolumeList[int(position[-1][0])]
                        if orderDirectionList[int(position[-1][0])] == "S":
                            volumeS += orderVolumeList[int(position[-1][0])]
                        if orderDirectionList[int(position[-1][0])] == "C":
                            volumeC += orderVolumeList[int(position[-1][0])]
            if self.__emaAveOrderVolume.getLastContent()[0] != 0:
                bidHugeOrderMultiple = (volumeB - volumeS - volumeC) / self.__emaAveOrderVolume.getLastContent()[0]
            else:
                bidHugeOrderMultiple = 0
        factorValue = [bidHugeOrderMultiple, askHugeOrderMultiple]
        self.addData(factorValue, self.__data.getLastTimeStamp())

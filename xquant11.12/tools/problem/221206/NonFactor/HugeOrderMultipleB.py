# -*- coding: utf-8 -*-
"""
Created on 2018/6/11 10:55

@author: 006566
与原HugeOrderMultiple的区别是： 不再区分买盘和卖盘的HugeOrderMultiple，而是将所有委托合在一起看
"""
import numpy as np
from System.Factor import Factor


class HugeOrderMultipleB(Factor):
    def __init__(self, para, factorManagement):  # 传入因子参数,归属的因子管理模块，需要用到的其他因子或非因子
        Factor.__init__(self, para, factorManagement)
        # 因子参数
        self.__paraNumOrderMax = para['paraNumOrderMax']
        self.__paraNumOrderMin = para['paraNumOrderMin']
        # 因子计算会用到的中间变量,取数据时候要注意会不会出现取出的因子还没有计算出值
        # 如果需要实例化因子作为中间变量，则name不要以factor开头，否则会输出到最终的结果中
        # 如果需要实例化因子或者非因子，需要考虑注册因子的先后顺序，即factorManagement.registerFactor(self)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__orderEvaluate = self.getFactorData({"name": "orderEvaluate", "className": "OrderEvaluate",
                                                   "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                   "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        factorManagement.registerFactor(self, para)

    def calculate(self):
        OrderBook = self.__orderEvaluate.getOrderBook()[-1]
        volumeB = 0
        volumeS = 0
        volumeC = 0
        if OrderBook.__len__() > 0:
            # 分析卖盘
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
            # 分析买盘，但不将volumeB, volumeS和volumeC清零
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
        factorValue = [volumeB, volumeS, volumeB - volumeS]
        self.addData(factorValue, self.__data.getLastTimeStamp())

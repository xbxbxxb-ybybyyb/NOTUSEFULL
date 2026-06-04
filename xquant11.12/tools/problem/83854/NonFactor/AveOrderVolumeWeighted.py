# -*- coding: utf-8 -*-
"""
Created on 2017/8/29 15:00

@author: 006547
"""

from System.Factor import Factor
import numpy as np
import math

class AveOrderVolumeWeighted(Factor):  # 非因子类，利用率较高的中间变量
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__numOrderMax = para["paraNumOrderMax"]
        self.__numOrderMin = para["paraNumOrderMin"]
        self.__weightDecay = para["weightDecay"]
        # 因子计算会用到的中间变量,取数据时候要注意会不会出现取出的因子还没有计算出值
        # 如果需要实例化因子作为中间变量，则name不要以factor开头，否则会输出到最终的结果中
        # 如果需要实例化因子或者非因子，需要考虑注册因子的先后顺序，即factorManagement.registerFactor(self)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        factorManagement.registerFactor(self, para)
        # content中存的是[lastAveBidVolume, lastAveAskVolume]

    def calculate(self):
        lastData = self.__data.getLastContent()
        lastAskVolume = np.array(self.__data.getLastContent().askVolume)
        lastAskVolume = lastAskVolume[lastAskVolume > 0]
        numOrderMax = int(min([len(lastAskVolume), self.__numOrderMax]))
        if numOrderMax == 0 or len(lastAskVolume) < self.__numOrderMin:
            lastAveAskVolume = 0
        else:
            volume_list = lastAskVolume[self.__numOrderMin-1:numOrderMax].tolist()
            lastAveAskVolume = 0.0
            for i in range(len(volume_list)):
                lastAveAskVolume = lastAveAskVolume + volume_list[i] * math.pow(self.__weightDecay, i)

            lastAveAskVolume = lastAveAskVolume / len(volume_list)

        lastBidVolume = np.array(self.__data.getLastContent().bidVolume)
        lastBidVolume = lastBidVolume[lastBidVolume > 0]
        numOrderMax = int(min([len(lastBidVolume), self.__numOrderMax]))
        if numOrderMax == 0 or len(lastBidVolume) < self.__numOrderMin:
            lastAveBidVolume = 0.0
        else:
            volume_list = lastBidVolume[self.__numOrderMin - 1:numOrderMax].tolist()
            lastAveBidVolume = 0.0
            for i in range(len(volume_list)):
                lastAveBidVolume = lastAveBidVolume + volume_list[i] * math.pow(self.__weightDecay, i)

            lastAveBidVolume = lastAveBidVolume / len(volume_list)

        self.addData([lastAveBidVolume, lastAveAskVolume], lastData.timeStamp)

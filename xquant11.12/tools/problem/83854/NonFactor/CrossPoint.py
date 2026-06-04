# -*- coding: utf-8 -*-
"""
Created on 2018/7/11 18:48
@author: 013050
@Revised by 006566 on 2018/7/26-27
"""
from System.Factor import Factor


class CrossPoint(Factor):  # 非因子类，利用率较高的中间变量
    def __init__(self, para, factorManagement):  # 传入因子参数,归属的因子管理模块，需要用到的其他因子或非因子
        Factor.__init__(self, para, factorManagement)
        # 因子参数
        self.__paraFastLag = para['paraFastLag']
        self.__paraSlowLag = para['paraSlowLag']
        # 因子计算会用到的中间变量,取数据时候要注意会不会出现取出的因子还没有计算出值
        # 如果需要实例化因子作为中间变量，则name不要以factor开头，否则会输出到最终的结果中
        # 如果需要实例化因子或者非因子，需要考虑注册因子的先后顺序，即factorManagement.registerFactor(self)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        paraEmaMidPrice = {"name": "emaMidPrice", "className": "Ema",
                           "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                           "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                           "paraLag": self.__paraFastLag,
                           "paraOriginalData": {"name": "midPrice", "className": "MidPrice",
                                                "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__emaMidPriceFast = self.getFactorData(paraEmaMidPrice)
        paraEmaMidPrice = {"name": "emaMidPrice", "className": "Ema",
                           "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                           "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                           "paraLag": self.__paraSlowLag,
                           "paraOriginalData": {"name": "midPrice", "className": "MidPrice",
                                                "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__emaMidPriceSlow = self.getFactorData(paraEmaMidPrice)
        # 引用其他因子与非因子
        self.__midPrice = self.getFactorData({"name": "midPrice", "className": "MidPrice",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        self.__direction = []
        self.__directionDiff = []
        self.__crossPos = [-1]  # 记录非零的位置，即交叉位置
        self.__boardCrossPosition = []
        self.__crossPointInfo = []
        self.__priceEdge = []
        self.__ratio1 = []
        self.__ratio2 = []
        self.__emaRatio = []
        self.__aveAmplitude = []
        factorManagement.registerFactor(self, para)

    def calculate(self):
        if self.__emaMidPriceFast.getLastContent() > self.__emaMidPriceSlow.getLastContent():
            self.__direction.append(1)
        else:
            self.__direction.append(0)

        if len(self.__direction) > 2:
            self.__directionDiff.append(self.__direction[-1] - self.__direction[-2])
            if self.__directionDiff[-1] != 0:
                if self.__crossPos.__len__() >= 2:
                    self.__crossPos.append(len(self.__directionDiff) - 2)
                else:
                    self.__crossPos.append(len(self.__directionDiff) - 1)
                self.__boardCrossPosition.append(self.__crossPos[-1] + 1)
                if len(self.__crossPos) == 2:
                    if self.__directionDiff[self.__crossPos[1]] == 1:
                        self.__directionDiff.insert(0, -1)
                        self.__crossPointInfo.append([0, -1, 0])
                        self.__priceEdge.append(self.__midPrice.getContent()[self.__crossPointInfo[-1][0]])
                    elif self.__directionDiff[self.__crossPos[1]] == -1:
                        self.__directionDiff.insert(0, 1)
                        self.__crossPointInfo.append([0, 1, 0])
                        self.__priceEdge.append(self.__midPrice.getContent()[self.__crossPointInfo[-1][0]])

                if self.__directionDiff[-1] == 1:
                    price_bottom = min(self.__midPrice.getContent()[(self.__crossPos[-2] + 2):(self.__crossPos[-1] + 2)])
                    pos_begin = self.__midPrice.getContent()[(self.__crossPos[-2] + 2):(
                        self.__crossPos[-1] + 2)].index(price_bottom) + self.__crossPos[-2] + 2
                    self.__crossPointInfo.append([pos_begin, 1, (self.__crossPos[-1])+1])
                    self.__priceEdge.append(self.__midPrice.getContent()[self.__crossPointInfo[-1][0]])
                    self.__ratio1.append(abs(float(self.__priceEdge[-1]) / self.__priceEdge[-2] - 1) * 1000)
                    self.__ratio2.append(float(sum(self.__ratio1) / self.__ratio1.__len__()))
                    if self.__ratio2.__len__() > 5:
                        self.__emaRatio.append(self.__emaRatio[-1] + 2 / 6 * (self.__ratio2[-1] - self.__emaRatio[-1]))
                    elif 1 < self.__ratio2.__len__() <= 5:
                        self.__emaRatio.append(self.__emaRatio[-1] + 2 / self.__ratio2.__len__() *
                                               (self.__ratio2[-1] - self.__emaRatio[-1]))
                    else:
                        self.__emaRatio.append(self.__ratio2[0])
                elif self.__directionDiff[-1] == -1:
                    price_top = max(self.__midPrice.getContent()[(self.__crossPos[-2] + 2):(self.__crossPos[-1] + 2)])
                    pos_begin = self.__midPrice.getContent()[(self.__crossPos[-2] + 2):(
                        self.__crossPos[-1] + 2)].index(price_top) + self.__crossPos[-2] + 2
                    self.__crossPointInfo.append([pos_begin, -1, (self.__crossPos[-1])+1])
                    self.__priceEdge.append(self.__midPrice.getContent()[self.__crossPointInfo[-1][0]])
                    self.__ratio1.append(abs(float(self.__priceEdge[-1]) / self.__priceEdge[-2] - 1) * 1000)
                    self.__ratio2.append(float(sum(self.__ratio1) / self.__ratio1.__len__()))
                    if self.__ratio2.__len__() > 5:
                        self.__emaRatio.append(self.__emaRatio[-1] + 2 / 6 * (self.__ratio2[-1] - self.__emaRatio[-1]))
                    elif 1 < self.__ratio2.__len__() <= 5:
                        self.__emaRatio.append(self.__emaRatio[-1] + 2 / self.__ratio2.__len__() *
                                               (self.__ratio2[-1] - self.__emaRatio[-1]))
                    else:
                        self.__emaRatio.append(self.__ratio2[0])

        if len(self.__midPrice.getContent()) <= 1:
            ratio_change = 0
            speed_change = 0
            self.__aveAmplitude.append(0)
            self.addData([ratio_change, speed_change, self.__aveAmplitude[-1]], self.__data.getLastTimeStamp())
        elif len(self.__crossPointInfo) == 0:
            ratio_change = self.__midPrice.getContent()[-1] / self.__midPrice.getContent()[0] - 1
            speed_change = ratio_change / (len(self.__midPrice.getContent()) - 1)
            self.__aveAmplitude.append(0)
            self.addData([ratio_change, speed_change, self.__aveAmplitude[-1]], self.__data.getLastTimeStamp())
        else:
            if self.__midPrice.getContent().__len__() == self.__boardCrossPosition[-1] + 2:
                self.__aveAmplitude.append(self.__emaRatio[-1])
            else:
                self.__aveAmplitude.append(self.__aveAmplitude[-1])
            if len(self.__midPrice.getContent()) == self.__crossPointInfo[len(self.__crossPointInfo) - 1][-1] + 1:
                ratio_change = self.__midPrice.getContent()[-1] / self.__midPrice.getContent()[
                    self.__crossPointInfo[len(self.__crossPointInfo) - 2][0]] - 1
                speed_change = ratio_change / (len(self.__midPrice.getContent()) - self.__crossPointInfo[len(
                    self.__crossPointInfo) - 2][0] - 1)
                self.addData([ratio_change, speed_change, self.__aveAmplitude[-1]], self.__data.getLastTimeStamp())
            else:
                ratio_change = self.__midPrice.getContent()[-1] / self.__midPrice.getContent()[
                    self.__crossPointInfo[len(self.__crossPointInfo) - 1][0]] - 1
                speed_change = ratio_change / (len(self.__midPrice.getContent()) - self.__crossPointInfo[len(
                    self.__crossPointInfo) - 1][0] - 1)
                self.addData([ratio_change, speed_change, self.__aveAmplitude[-1]], self.__data.getLastTimeStamp())

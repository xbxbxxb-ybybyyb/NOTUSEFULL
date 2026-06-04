# -*- coding: utf-8 -*-
"""
Created on Tue Aug  8 21:23:23 2017

@author: 006547
"""
from System.Factor import Factor


class ExtremePoint(Factor):  # 非因子类，利用率较高的中间变量
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
        factorManagement.registerFactor(self, para)
        self.__direction = []
        self.__extremePointInfo = []  # [[方向， 界点价格， 界点时间戳， 界点涨跌幅， 产生界点位置价格， 产生界点位置时间戳， 产生界点位置涨跌幅], ...]
        self.__lastExtremePointInfo = []  # 当前正在形成中的界点信息[方向， 极值价格， 极值时间戳， 极值到上一个界点涨跌幅， 当前位置价格， 当前位置时间戳，
        # 当前位置到上一个产生界点位置涨跌幅]
        self.__updateStatus = 0

    def calculate(self):
        self.__direction.append(self.__emaMidPriceFast.getLastContent() - self.__emaMidPriceSlow.getLastContent())
        if len(self.__direction) >= 2:
            if self.__direction[-1] * self.__direction[-2] <= 0 and self.__direction[-1] != 0:
                self.__updateStatus = 1
                if self.__direction[-1] > 0:
                    tempDirection = 1
                else:
                    tempDirection = -1
                self.__lastExtremePointInfo[0] = -tempDirection  # 第一个界点信息中方向是不对的
                self.__extremePointInfo.append(self.__lastExtremePointInfo)
                self.__lastExtremePointInfo = [tempDirection, self.__midPrice.getLastContent(),
                                               self.__midPrice.getLastTimeStamp(),
                                               self.__midPrice.getLastContent() / self.__extremePointInfo[-1][1] - 1,
                                               self.__midPrice.getLastContent(), self.__midPrice.getLastTimeStamp(),
                                               self.__midPrice.getLastContent() / self.__extremePointInfo[-1][4] - 1]
                self.addData(self.__lastExtremePointInfo[:], self.__data.getLastTimeStamp())

            else:
                if (self.__midPrice.getLastContent() - self.__lastExtremePointInfo[1]) * \
                        self.__lastExtremePointInfo[0] > 0:
                    self.__lastExtremePointInfo[1] = self.__midPrice.getLastContent()
                    self.__lastExtremePointInfo[2] = self.__midPrice.getLastTimeStamp()

                self.__lastExtremePointInfo[4] = self.__midPrice.getLastContent()
                self.__lastExtremePointInfo[5] = self.__midPrice.getLastTimeStamp()
                if len(self.__extremePointInfo) >= 1:
                    self.__lastExtremePointInfo[6] = \
                        self.__midPrice.getLastContent() / self.__extremePointInfo[-1][4] - 1
                if len(self.__extremePointInfo) >= 1:
                    self.__lastExtremePointInfo[3] = self.__lastExtremePointInfo[1] / self.__extremePointInfo[-1][1] - 1
                self.addData(self.__lastExtremePointInfo[:], self.__data.getLastTimeStamp())
                self.__updateStatus = 0
        elif len(self.__direction) == 1:
            self.__updateStatus = 0
            self.__lastExtremePointInfo = [-1, self.__midPrice.getLastContent(), self.__midPrice.getLastTimeStamp(), 0.,
                                           self.__midPrice.getLastContent(), self.__midPrice.getLastTimeStamp(), 0.]
            self.addData(self.__lastExtremePointInfo[:], self.__data.getLastTimeStamp())

    def getExtremePointInfo(self):
        return self.__extremePointInfo

    def getUpdateStatus(self):
        return self.__updateStatus

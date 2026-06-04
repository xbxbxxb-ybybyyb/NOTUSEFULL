"""
@author: 006688

计算指数的界点信息
"""
from System.Factor import Factor


class IndexExtremePoint(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        # 因子参数
        self.__paraFastLag = para['paraFastLag']
        self.__paraSlowLag = para['paraSlowLag']

        self.__data = self.getFactorUnderlyingData(self.getIndexFactorUnderlying()[0])
        paraEmaIndexPrice = {"name": "emaIndexPrice", "className": "Ema",
                             "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                             "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                             "paraLag": self.__paraFastLag,
                             "paraOriginalData": {"name": "indexPrice", "className": "IndexPrice",
                                                  "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                  "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__emaIndexPriceFast = self.getFactorData(paraEmaIndexPrice)
        paraEmaIndexPrice = {"name": "emaIndexPrice", "className": "Ema",
                             "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                             "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                             "paraLag": self.__paraSlowLag,
                             "paraOriginalData": {"name": "indexPrice", "className": "IndexPrice",
                                                  "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                  "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__emaIndexPriceSlow = self.getFactorData(paraEmaIndexPrice)
        self.__indexPrice = self.getFactorData({"name": "indexPrice", "className": "IndexPrice",
                                                "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        factorManagement.registerFactor(self, para)
        self.__direction = []
        self.__extremePointInfo = []  # [[方向， 界点价格， 界点时间戳， 界点涨跌幅， 产生界点位置价格， 产生界点位置时间戳， 产生界点位置涨跌幅], ...]
        self.__lastExtremePointInfo = []  # 当前正在形成中的界点信息[方向， 极值价格， 极值时间戳， 极值到上一个界点涨跌幅， 当前位置价格， 当前位置时间戳，
        # 当前位置到上一个产生界点位置涨跌幅]
        self.__updateStatus = 0

    def calculate(self):
        self.__direction.append(self.__emaIndexPriceFast.getLastContent() - self.__emaIndexPriceSlow.getLastContent())
        if len(self.__direction) >= 2:
            if self.__direction[-1] * self.__direction[-2] <= 0 and self.__direction[-1] != 0:
                self.__updateStatus = 1
                if self.__direction[-1] > 0:
                    tempDirection = 1
                else:
                    tempDirection = -1
                self.__lastExtremePointInfo[0] = -tempDirection  # 第一个界点信息中方向是不对的
                self.__extremePointInfo.append(self.__lastExtremePointInfo)
                self.__lastExtremePointInfo = [tempDirection, self.__indexPrice.getLastContent(),
                                               self.__indexPrice.getLastTimeStamp(),
                                               self.__indexPrice.getLastContent() / self.__extremePointInfo[-1][1] - 1,
                                               self.__indexPrice.getLastContent(), self.__indexPrice.getLastTimeStamp(),
                                               self.__indexPrice.getLastContent() / self.__extremePointInfo[-1][4] - 1]
                self.addData(self.__lastExtremePointInfo[:], self.__data.getLastTimeStamp())

            else:
                if (self.__indexPrice.getLastContent() - self.__lastExtremePointInfo[1]) * \
                        self.__lastExtremePointInfo[0] > 0:
                    self.__lastExtremePointInfo[1] = self.__indexPrice.getLastContent()
                    self.__lastExtremePointInfo[2] = self.__indexPrice.getLastTimeStamp()

                self.__lastExtremePointInfo[4] = self.__indexPrice.getLastContent()
                self.__lastExtremePointInfo[5] = self.__indexPrice.getLastTimeStamp()
                if len(self.__extremePointInfo) >= 1:
                    self.__lastExtremePointInfo[6] = \
                        self.__indexPrice.getLastContent() / self.__extremePointInfo[-1][4] - 1
                if len(self.__extremePointInfo) >= 1:
                    self.__lastExtremePointInfo[3] = self.__lastExtremePointInfo[1] / self.__extremePointInfo[-1][1] - 1
                self.addData(self.__lastExtremePointInfo[:], self.__data.getLastTimeStamp())
                self.__updateStatus = 0
        elif len(self.__direction) == 1:
            self.__updateStatus = 0
            self.__lastExtremePointInfo = [-1, self.__indexPrice.getLastContent(), self.__indexPrice.getLastTimeStamp(), 0.,
                                           self.__indexPrice.getLastContent(), self.__indexPrice.getLastTimeStamp(), 0.]
            self.addData(self.__lastExtremePointInfo[:], self.__data.getLastTimeStamp())

    def getExtremePointInfo(self):
        return self.__extremePointInfo

    def getUpdateStatus(self):
        return self.__updateStatus

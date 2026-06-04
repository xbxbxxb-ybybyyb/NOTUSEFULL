"""
@author: 006688

当前波段序号记为0，依据界点，往前的波段依次计为第1、2、...波，指定波段的序号，给出对应波段的放量倍数
放量倍数定义为该波段秒均成交量/开盘到该波段结束时的秒均成交量
波段序号参数为list形式，可以指定多个波段，例如[1, 2, 4, 5]
"""

from System.Factor import Factor


class LastNVolumeMagnification(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraLastN = para['paraLastN']
        self.__paraFastLag = para['paraFastLag']
        self.__paraSlowLag = para['paraSlowLag']

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__extremePoint = self.getFactorData({"name": "extremePoint", "className": "ExtremePoint",
                                                  "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                  "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                                  "paraFastLag": self.__paraFastLag, "paraSlowLag": self.__paraSlowLag})
        self.__extremePointInfo = self.__extremePoint.getExtremePointInfo()
        factorManagement.registerFactor(self, para)
        self.__accVolume = []  # 储存新产生界点处的累计成交量
        self.__VolumeMagnification = []  # 依次储存每个波段的放量倍数

    def calculate(self):
        factorValue = [0] * len(self.__paraLastN)
        if self.__extremePoint.getUpdateStatus() == 1:  # 每确定一个新的界点，计算最新一个波段的放量倍数
            PointIndex = self.__data.getTimeStamp().index(self.__extremePointInfo[-1][2])  # 最近界点时间戳序号
            self.__accVolume.append(self.__data.getContent()[PointIndex].totalVolume)  # 保存最近界点时刻的累计成交量
            if len(self.__extremePointInfo) >= 2:
                startTime = self.__extremePointInfo[-2][2]  # 最近一波开始时间
                endTime = self.__extremePointInfo[-1][2]  # 最近一波结束时间
                IntervalTime = self.getTimeLength(startTime, endTime)
                TotalTime = self.getTimeLength(self.__data.getTimeStamp()[0], endTime)
                IntervalVolume = self.__accVolume[-1] - self.__accVolume[-2]
                TotalVolume = self.__accVolume[-1] - self.__data.getContent()[0].totalVolume
                if TotalVolume == 0 or TotalTime == 0 or IntervalTime == 0:
                    self.__VolumeMagnification.append(0)
                else:
                    self.__VolumeMagnification.append((IntervalVolume / IntervalTime) / (TotalVolume / TotalTime))
            for i in range(self.__paraLastN.__len__()):
                if self.__paraLastN[i] <= len(self.__VolumeMagnification):
                    factorValue[i] = self.__VolumeMagnification[-self.__paraLastN[i]]
            self.addData(factorValue, self.__data.getLastTimeStamp())
        else:
            if len(self.getContent()) == 0:
                self.addData(factorValue, self.__data.getLastTimeStamp())
            else:
                self.addData(self.getLastContent(), self.__data.getLastTimeStamp())

    def getVolumeMagnification(self):
        return self.__VolumeMagnification

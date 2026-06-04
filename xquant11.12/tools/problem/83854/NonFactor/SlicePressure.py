"""
@author: 006688

计算盘口挂单买卖压力
"""

from System.Factor import Factor
import math


class SlicePressure(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraNumOrderMax = para['paraNumOrderMax']  # 比较盘口档位数
        self.__paraNumOrderMin = para['paraNumOrderMin']  # 比较盘口档位数

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__aveOrderVolume = self.getFactorData({"name": "aveOrderVolume", "className": "AveOrderVolume",
                                                    "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                    "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                                    "paraNumOrderMax": self.__paraNumOrderMax,
                                                    "paraNumOrderMin": self.__paraNumOrderMin})
        factorManagement.registerFactor(self, para)

    def calculate(self):
        aveVolumeBid = self.__aveOrderVolume.getLastContent()[0]  # N档买盘的平均挂单量
        aveVolumeAsk = self.__aveOrderVolume.getLastContent()[1]  # N档卖盘的平均挂单量
        if aveVolumeBid == 0 or aveVolumeAsk == 0:
            self.addData(0, self.__data.getLastTimeStamp())
        else:
            self.addData(math.log(aveVolumeBid) - math.log(aveVolumeAsk), self.__data.getLastTimeStamp())

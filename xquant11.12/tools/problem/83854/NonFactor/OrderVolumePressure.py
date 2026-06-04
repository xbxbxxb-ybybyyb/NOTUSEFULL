"""
@author: 006688

计算盘口挂单买卖压力
"""

from System.Factor import Factor
import math


class OrderVolumePressure(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraNumOrderMax = para['paraNumOrderMax']  # 比较盘口档位数
        self.__paraNumOrderMin = para['paraNumOrderMin']  # 比较盘口档位数
        self.__weightDecay = para["weightDecay"]

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__aveOrderVolumeWeighted = self.getFactorData({"name": "aveOrderVolumeWeighted", "className": "AveOrderVolumeWeighted",
                                                    "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                    "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                                    "paraNumOrderMax": self.__paraNumOrderMax,
                                                    "paraNumOrderMin": self.__paraNumOrderMin,
                                                    "weightDecay": self.__weightDecay})
        factorManagement.registerFactor(self, para)

    def calculate(self):
        aveVolumeBid = self.__aveOrderVolumeWeighted.getLastContent()[0]  # N档买盘的平均挂单量
        aveVolumeAsk = self.__aveOrderVolumeWeighted.getLastContent()[1]  # N档卖盘的平均挂单量
        if aveVolumeBid == 0 or aveVolumeAsk == 0:
            self.addData(0, self.__data.getLastTimeStamp())
        else:
            self.addData(math.log(aveVolumeAsk) - math.log(aveVolumeBid), self.__data.getLastTimeStamp())

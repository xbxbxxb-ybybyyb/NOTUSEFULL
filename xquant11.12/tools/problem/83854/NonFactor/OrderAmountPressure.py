"""
@author: 006688

计算盘口挂单买卖压力
"""

from System.Factor import Factor
import math


class OrderAmountPressure(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraNumOrderMax = para['paraNumOrderMax']  # 比较盘口档位数
        self.__paraNumOrderMin = para['paraNumOrderMin']  # 比较盘口档位数
        self.__weightDecay = para["weightDecay"]

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__aveOrderAmountWeighted = self.getFactorData({"name": "aveOrderAmountWeighted", "className": "AveOrderAmountWeighted",
                                                    "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                    "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                                    "paraNumOrderMax": self.__paraNumOrderMax,
                                                    "paraNumOrderMin": self.__paraNumOrderMin,
                                                    "weightDecay": self.__weightDecay})
        factorManagement.registerFactor(self, para)

    def calculate(self):
        aveAmountBid = self.__aveOrderAmountWeighted.getLastContent()[0]  # N档买盘的平均挂单量
        aveAmountAsk = self.__aveOrderAmountWeighted.getLastContent()[1]  # N档卖盘的平均挂单量
        if aveAmountBid == 0 and aveAmountAsk == 0:
            self.addData(0, self.__data.getLastTimeStamp())
        else:
            self.addData((aveAmountBid - aveAmountAsk) / (aveAmountBid + aveAmountAsk), self.__data.getLastTimeStamp())

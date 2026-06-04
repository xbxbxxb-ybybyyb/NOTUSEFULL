"""
@author: 006688

计算盘口挂单买卖压力的EMA
"""

from System.Factor import Factor


class FactorEmaOrderVolumePressure(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraNumOrderMax = para['paraNumOrderMax']  # 比较盘口档位数
        self.__paraNumOrderMin = para['paraNumOrderMin']  # 比较盘口档位数
        self.__paraEmaOrderVolumePressureLag = para['paraEmaOrderVolumePressureLag']  # EMA参数
        self.__weightDecay = para['weightDecay']

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        paraEmaOrderVolumePressure = {"name": "emaOrderVolumePressure", "className": "Ema",
                                "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                "paraLag": self.__paraEmaOrderVolumePressureLag,
                                "paraOriginalData": {"name": "orderVolumePressure", "className": "OrderVolumePressure",
                                                     "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                     "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                                     "paraNumOrderMax": self.__paraNumOrderMax,
                                                     "paraNumOrderMin": self.__paraNumOrderMin,
                                                     "weightDecay": self.__weightDecay}}
        self.__emaOrderVolumePressure = self.getFactorData(paraEmaOrderVolumePressure)
        factorManagement.registerFactor(self, para)

    def calculate(self):
        self.addData(self.__emaOrderVolumePressure.getLastContent(), self.__data.getLastTimeStamp())

"""
@author: 006688

根据买卖压力的EMA计算买卖压力的比较
"""

from System.Factor import Factor
import math


class FactorOrderPressureModified2(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraOrderPressureLag = para['paraOrderPressureLag']

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        paraEmaOrderPressure = {"name": "emaOrderPressure", "className": "Ema",
                                "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                "paraLag": self.__paraOrderPressureLag,
                                "paraOriginalData": {"name": "orderEvaluate2", "className": "OrderEvaluate2",
                                                     "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                     "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__emaOrderPressure = self.getFactorData(paraEmaOrderPressure)  # 取OrderEvaluate中计算的买卖压的EMA
        factorManagement.registerFactor(self, para)
        self.__emaOrderPressureBuy = []
        self.__emaOrderPressureSell = []
        self.__eps = 1e-5

    def calculate(self):
        PressureBuy = self.__emaOrderPressure.getLastContent()[0]
        PressureSell = self.__emaOrderPressure.getLastContent()[1]
        if PressureBuy < 0 or PressureSell < 0:
            FactorValue = 0.0
        else:
            FactorValue = math.log(PressureBuy + self.__eps) - math.log(PressureSell + self.__eps)
        self.__emaOrderPressureBuy.append(PressureBuy)
        self.__emaOrderPressureSell.append(PressureSell)
        self.addData(FactorValue, self.__data.getLastTimeStamp())

    def getEmaOrderPressureBuy(self):
        return self.__emaOrderPressureBuy

    def getEmaOrderPressureSell(self):
        return self.__emaOrderPressureSell
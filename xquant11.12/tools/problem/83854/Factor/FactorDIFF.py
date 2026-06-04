"""
@author: 006688

计算中间价序列的DIFF值(即快慢均线的差值)
"""
from System.Factor import Factor


class FactorDIFF(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)

        self.__paraFastLag = para['paraFastLag']
        self.__paraSlowLag = para['paraSlowLag']

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

        factorManagement.registerFactor(self, para)

    def calculate(self):
        DIFF = self.__emaMidPriceFast.getLastContent() - self.__emaMidPriceSlow.getLastContent()
        self.addData(DIFF, self.__emaMidPriceFast.getLastTimeStamp())

"""
@author: 013050

成交额
"""
from System.Factor import Factor


class Amount(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        factorManagement.registerFactor(self, para)

    def calculate(self):
        self.addData(self.__data.getLastContent().amount, self.__data.getLastTimeStamp())

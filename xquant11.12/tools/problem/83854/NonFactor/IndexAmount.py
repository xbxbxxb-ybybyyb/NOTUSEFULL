"""
@author: 006688

指数成交额
"""
from System.Factor import Factor


class IndexAmount(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)

        self.__data = self.getFactorUnderlyingData(self.getIndexFactorUnderlying()[0])
        factorManagement.registerFactor(self, para)

    def calculate(self):
        self.addData(self.__data.getLastContent().amount, self.__data.getLastTimeStamp())

"""
@author: 006688

指数价格
"""
from System.Factor import Factor


class IndexPrice(Factor):  # 非因子类，利用率较高的中间变量
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)

        self.__data = self.getFactorUnderlyingData(self.getIndexFactorUnderlying()[0])
        factorManagement.registerFactor(self, para)

    def calculate(self):
        self.addData(self.__data.getLastContent().lastPrice, self.__data.getLastTimeStamp())

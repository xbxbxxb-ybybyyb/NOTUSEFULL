"""
@author: 006688
计算从开盘到当前时点的平均成交价（即对应于分时图中的黄色均价线）
@revised by 006566  2018/7/24 -- 在计算均线时，可以忽略开盘前的一段时间
2018/7/26 -- 修正了AvePrice为0的bug - 如为0，则以中间价代替
"""

from System.Factor import Factor


class AvePrice(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__midPrice = self.getFactorData({"name": "midPrice", "className": "MidPrice",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        self.__totalAmount = 0
        self.__totalVolume = 0
        factorManagement.registerFactor(self, para)

    def calculate(self):
        # totalAmount = self.__data.getLastContent().totalAmount
        # totalVolume = self.__data.getLastContent().totalVolume
        # self.addData(totalAmount / totalVolume, self.__data.getLastTimeStamp())
        self.__totalAmount += self.__data.getLastContent().amount
        self.__totalVolume += self.__data.getLastContent().volume
        if self.__totalVolume > 0:
            avePrice = self.__totalAmount / self.__totalVolume
        else:
            avePrice = self.__midPrice.getLastContent()
        self.addData(avePrice, self.__data.getLastTimeStamp())

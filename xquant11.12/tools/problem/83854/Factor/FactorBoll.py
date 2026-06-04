"""
@author: 011673
@revise: 006688

计算中间价序列的Bolling带
输出结果为当前价格在Bolling带中的相对位置，0表示下轨，1表示上轨
同时提供了取Bolling带上、中、下轨价格的接口
1、计算中轨MA=前N个切片的中间价均线
2、计算标准差MD=前N个切片中间价与MA的标准差
3、计算上轨、下轨
UP=MB+宽度*MD
DN=MB-宽度*MD
4、相对位置=（中间价-下轨值）/（上轨值-下轨值）
"""
from System.Factor import Factor
import numpy as np


class FactorBoll(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraBollLag = para["paraBollLag"]
        self.__paraWidth = para["paraWidth"]  # 布林带的宽度，即几倍的标准差

        self.__midPrice = self.getFactorData({"name": "midPrice", "className": "MidPrice",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()})

        self.__bollMid = []
        self.__bollUp = []
        self.__bollDown = []
        factorManagement.registerFactor(self, para)

    def calculate(self):
        midPrice = self.__midPrice.getContent()
        lastMidPrice = self.__midPrice.getLastContent()
        if len(midPrice) <= self.__paraBollLag:
            priceList = midPrice
        else:
            priceList = midPrice[-self.__paraBollLag:]
        is_not_valid = False
        for p in priceList:
            if p <= 0.01:
                is_not_valid = True
                break

        if is_not_valid:
            if len(self.getContent()) == 0:
                BollPosition = 0.0
            else:
                BollPosition = self.getLastContent()
        else:
            # 中轨
            lastMA = np.mean(priceList)
            self.__bollMid.append(lastMA)
            MAList = self.__bollMid[-len(priceList):]
            # 标准差
            MD = np.std(np.array(priceList) - np.array(MAList))
            # 上下轨
            BollUp = lastMA + self.__paraWidth * MD
            BollDown = lastMA - self.__paraWidth * MD
            # 相对位置
            if BollUp == BollDown:
                BollPosition = 0.5
            else:
                BollPosition = (lastMidPrice - BollDown) / (BollUp - BollDown)
            self.__bollUp.append(BollUp)
            self.__bollDown.append(BollDown)
        self.addData(BollPosition, self.__midPrice.getLastTimeStamp())

    def getBollMid(self):
        return self.__bollMid

    def getBollUp(self):
        return self.__bollUp

    def getBollDown(self):
        return self.__bollDown

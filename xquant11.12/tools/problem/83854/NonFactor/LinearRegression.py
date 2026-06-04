# -*- coding: utf-8 -*-
"""
Created on Fri Aug 18 14:15:47 2017

@author: 006547
"""
from System.Factor import Factor
import numpy as np


class LinearRegression(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        # 因子参数
        self.__returnLag = para["returnLag"]
        self.__factorLag = para["factorLag"]
        self.__factorNum = para["factorNum"]
        self.__paraOriginalData = para["paraOriginalData"]
        # 因子计算会用到的中间变量,取数据时候要注意会不会出现取出的因子还没有计算出值
        # 如果需要实例化因子作为中间变量，则name不要以factor开头，否则会输出到最终的结果中
        # 如果需要实例化因子或者非因子，需要考虑注册因子的先后顺序，即factorManagement.registerFactor(self)
        self.__midPrice = self.getFactorData({"name": "midPrice", "className": "MidPrice",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        self.__originalData = self.getFactorData(self.__paraOriginalData)
        factorManagement.registerFactor(self, para)

    def calculate(self):
        factorValue = 0
        if self.__originalData.getContent().__len__() >= (self.__returnLag + self.__factorLag):
            y = np.array(self.__midPrice.getContent()[-self.__factorLag:]) / np.array(self.__midPrice.getContent()[-(self.__factorLag+self.__returnLag):-self.__returnLag]) - 1
            y = y[self.__factorNum-1:]

            x = np.array(self.__originalData.getContent()[-(self.__factorLag+self.__returnLag-self.__factorNum+1):-self.__returnLag])
            if self.__factorNum > 1:
                for i in range(self.__factorNum-1):
                    x = np.vstack((x, np.array(self.__originalData.getContent()[-(self.__factorLag+self.__returnLag-self.__factorNum+1+i+1):-self.__returnLag-i-1])))
            x = np.vstack((np.repeat(1, x.shape[1]), x))
            y = np.matrix(y).T
            x = np.matrix(x).T
            try:
                beta = (x.T*x).I*x.T*y
            except Exception:
                beta = np.matrix(np.repeat(0, x.shape[1])).T

            f = np.array(self.__originalData.getContent()[-self.__factorNum:])
            f = np.hstack(([1], f[-np.arange(1, self.__factorNum+1)]))
            factorValue = f*beta
            factorValue = factorValue[0, 0]

        self.addData(factorValue, self.__originalData.getLastTimeStamp())

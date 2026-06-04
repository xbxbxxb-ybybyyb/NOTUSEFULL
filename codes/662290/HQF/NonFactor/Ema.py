# -*- coding: utf-8 -*-
"""
Created on Fri Aug 18 14:15:47 2017

@author: 006547
"""
from System.Factor import Factor


class Ema(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        # 因子参数
        self.__paraLag = para["paraLag"]  # 切片数为lag
        self.__paraOriginalData = para["paraOriginalData"]
        # 因子计算会用到的中间变量,取数据时候要注意会不会出现取出的因子还没有计算出值
        # 如果需要实例化因子作为中间变量，则name不要以factor开头，否则会输出到最终的结果中
        # 如果需要实例化因子或者非因子，需要考虑注册因子的先后顺序，即factorManagement.registerFactor(self)
        self.__originalData = self.getFactorData(self.__paraOriginalData)
        factorManagement.registerFactor(self, para)

    def calculate(self):
        factorValue = 0
        if len(self.getContent()) == 0:
            factorValue = self.__originalData.getLastContent()
        else:
            if isinstance(self.__originalData.getLastContent(), list):
                lastEma = []
                if self.__paraLag is None or self.__originalData.getContent().__len__() <= self.__paraLag:
                    for i in range(self.__originalData.getLastContent().__len__()):
                        lastEma.append(self.getLastContent()[i] + 2 / (len(self.getTimeStamp()) + 1) * (
                            self.__originalData.getLastContent()[i] - self.getLastContent()[i]))
                    factorValue = lastEma[:]
                else:
                    for i in range(self.__originalData.getLastContent().__len__()):
                        lastEma.append(self.getLastContent()[i] + 2 / (self.__paraLag + 1) * (
                            self.__originalData.getLastContent()[i] - self.getLastContent()[i]))
                        factorValue = lastEma[:]
            else:
                if self.__paraLag is None or self.__originalData.getContent().__len__() <= self.__paraLag:
                    factorValue = self.getLastContent() + 2 / (len(self.getTimeStamp()) + 1) * (
                        self.__originalData.getLastContent() - self.getLastContent())
                else:
                    factorValue = self.getLastContent() + 2 / (self.__paraLag + 1) * (
                        self.__originalData.getLastContent() - self.getLastContent())
        self.addData(factorValue, self.__originalData.getLastTimeStamp())

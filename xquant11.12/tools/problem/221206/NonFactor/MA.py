"""
@author: 006688

计算给定时间序列的移动平均值（MA）
"""
from System.Factor import Factor
import numpy as np


class MA(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        # 因子参数
        self.__paraLag = para["paraLag"]
        self.__paraOriginalData = para["paraOriginalData"]

        self.__originalData = self.getFactorData(self.__paraOriginalData)
        factorManagement.registerFactor(self, para)

    def calculate(self):
        dataList = np.array(self.__originalData.getContent())
        if self.__paraLag is None or dataList.__len__() <= self.__paraLag:
            factorValue = np.mean(dataList)
        else:
            factorValue = np.mean(dataList[-self.__paraLag:])
        self.addData(factorValue, self.__originalData.getLastTimeStamp())

# Updated on 2018/7/16 修正bug & 新增对跨日并行化运算的支持

# -*- coding: utf-8 -*-
from System.FactorManagement import FactorManagement
from System.TagManagement import TagManagement


class ExecuteStrategy:
    def __init__(self, strategy, tradingUnderlyingCode):
        # 建立因子管理模块用于储存数据、因子以及分配切片给因子进行计算
        self.__factorManagement = FactorManagement(tradingUnderlyingCode, strategy.getFactorUnderlyingCode())
        # 实例化需要计算的因子和非因子
        for i in range(len(strategy.getParaFactor())):
            self.getFactorManagement().getFactorData(strategy.getParaFactor()[i])
        # 实例化标签管理模块，每一个切片来后都会在标签管理模块中实例化一个标签，里面可以储存及计算所有想要的东西
        self.__tagManagement = TagManagement(strategy.getParaTag(), self.__factorManagement)
        self.__factorName = []
        # 这里必须排序以保证factorname顺序一致
        for para in strategy.getParaFactor():
            if para["save"] == True:
                self.__factorName.append(para["name"])

    def onMarketData(self, sliceData):
        self.__factorManagement.calculate(sliceData)
        self.__tagManagement.calculate(sliceData)

    def getOutput(self):
        # 返回因子、非因子、标签和时间戳
        # factor = self.__factorManagement.getLastFactors()
        factor = self.__factorManagement.getFactorsNeedSave()
        names = self.__factorManagement.getFactorNameNeedSave()
        timestamp = self.__tagManagement.getLastTimeStamp()
        tag = self.__tagManagement.getLastTag()
        return factor, names, timestamp, tag

    def getFactorManagement(self):
        return self.__factorManagement

    def getFactorName(self):
        return self.__factorName

    def setPreDayticks(self, value):
        self.__factorManagement.setPreDayTicks(value)

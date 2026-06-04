# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 13:06:55 2017
# Updated on 2018/7/16 by 010022 -- 改造以支持取跨日数据+并行化运算

@author: 006547
"""
from System.DataCollector import DataCollector


class FactorManagement:
    def __init__(self, TradingUnderlyingCode, FactorUnderlyingCode):
        self.__tradingUnderlyingCode = TradingUnderlyingCode
        self.__factorUnderlyingCode = FactorUnderlyingCode
        self.__dataCollector = DataCollector(TradingUnderlyingCode, FactorUnderlyingCode)
        self.__factor = {}  # 因子列表，key是ClassName, value是因子的[para, factor]
        self.__factorKeys = None  # 排序后的list, 直到所有factor初始化后再生成
        self.__nonFactor = {}  # 非因子列表
        self.__factorsNeedSave = []  #
        self.__factorNamesNeedSave = []
        self.__pre_day_ticks = None
        dictCodeToFactorKey = list(set(TradingUnderlyingCode + FactorUnderlyingCode))

        self.__dictCodeToFactor = {dictCodeToFactorKey[0]: []}
        if len(dictCodeToFactorKey) > 1:
            for i in range(1, len(dictCodeToFactorKey)):
                self.__dictCodeToFactor.update({dictCodeToFactorKey[i]: []})
                # self.__dictCodeToFactor的类型是字典，key是股票代码（例如'600110.SH），对应的value的类型是list
                # list的内容是牵涉到这只股票的因子或非因子

    # registerFactor方法在每个因子初始化的时候会调用
    # 在ExecuteStrategy的初始化阶段会第一次将Main的setParaFactor列出的因子和非因子全部实例化一遍
    # 除了在Main的setParaFactor中列出因子和非因子之外，在因子计算的过程中也可以再根据需求实例化/注册因子
    def registerFactor(self, factor, para):
        if factor.getClassName()[0:6] == "Factor":
            if not factor.getClassName() in self.__factor.keys():
                self.__factor.update({factor.getClassName(): []})
                # 如果本因子的名称（类名）不在self.__factor（因子列表）中，那么就将key更新（注册）进来
            self.__factor[factor.getClassName()].append([para, factor])
            if ("save" in para) and (para["save"] == 'True'):
                self.__factorsNeedSave.append(factor)
                self.__factorNamesNeedSave.append(para["name"])

            # 注意如果因子名称（类名）已经在列表中，也可能有不同para（参数），再将新的[para, factor]注册进来
            dictKey = []
            if len(factor.getIndexTradingUnderlying()) > 0:
                for i in range(len(factor.getIndexTradingUnderlying())):
                    dictKey = list(set(dictKey + [self.__tradingUnderlyingCode[factor.getIndexTradingUnderlying()[i]]]))
            if len(factor.getIndexFactorUnderlying()) > 0:
                for i in range(len(factor.getIndexFactorUnderlying())):
                    dictKey = list(set(dictKey + [self.__factorUnderlyingCode[factor.getIndexFactorUnderlying()[i]]]))
            if len(dictKey) > 0:
                for i in range(len(dictKey)):
                    self.__dictCodeToFactor[dictKey[i]].append(factor)
        else:
            if not factor.getClassName() in self.__nonFactor.keys():
                self.__nonFactor.update({factor.getClassName(): []})
                # 如果本非因子的名称不在self.__factor（非因子列表）中，那么就更新（注册）进来
            self.__nonFactor[factor.getClassName()].append([para, factor])
            if ("save" in para) and (para["save"] == 'True'):
                self.__factorsNeedSave.append(factor)
                self.__factorNamesNeedSave.append(para["name"])

            dictKey = []
            if len(factor.getIndexTradingUnderlying()) > 0:
                for i in range(len(factor.getIndexTradingUnderlying())):
                    dictKey = list(set(dictKey + [self.__tradingUnderlyingCode[factor.getIndexTradingUnderlying()[i]]]))
            if len(factor.getIndexFactorUnderlying()) > 0:
                for i in range(len(factor.getIndexFactorUnderlying())):
                    dictKey = list(set(dictKey + [self.__factorUnderlyingCode[factor.getIndexFactorUnderlying()[i]]]))
            if len(dictKey) > 0:
                for i in range(len(dictKey)):
                    self.__dictCodeToFactor[dictKey[i]].append(factor)

    def calculate(self, sliceData):
        self.__dataCollector.addSliceData(sliceData)
        if len(self.__dictCodeToFactor[sliceData.code]) > 0:
            for i in range(len(self.__dictCodeToFactor[sliceData.code])):
                self.__dictCodeToFactor[sliceData.code][i].calculate()

    def getDataCollector(self):
        return self.__dataCollector

    def getFactor(self):
        return self.__factor

    def getNonFactor(self):
        return self.__nonFactor

    def getFactorData(self, para):
        className = para["className"]
        if className[0:6] == "Factor":  # 如果因子类名className以Factor开头
            if className not in self.__factor.keys():  # 若本因子不在self.__factor的key列表中（未被注册）
                exec("from " + className + " import " + className)
                exec(className + "(para, self)")  # 那么就按para实例化并注册这个因子，这里的self是factorManagement
                return self.getFactorData(para)  # 返回本方法，则会再调用一次，这次此因子已被注册，则会进入下面的else语句段中
            else:
                for i in range(self.__factor[className].__len__()):  # 相同className的因子可能有不止一组参数，以下逐个循环
                    tempDeepCopy1 = self.__factor[className][i][
                        0].copy()  # self.__factor[className][i][0]是para，[1]是factorData
                    tempDeepCopy2 = para.copy()
                    del tempDeepCopy1["name"]
                    del tempDeepCopy2["name"]
                    if "save" in tempDeepCopy1:
                        del tempDeepCopy1["save"]
                    if "save" in tempDeepCopy2:
                        del tempDeepCopy2["save"]
                    if tempDeepCopy1 == tempDeepCopy2:
                        # 如果是中间变量，则因子实例名（para中的name）不以factor开头，不会输出到最终结果中
                        # 如最初某因子是以中间变量为目的注册的，但后续引用时想输出结果，在para的name中以factor开头即可
                        if self.__factor[className][i][0]["name"][0:6] != "factor" and para["name"][0:6] == "factor":
                            self.__factor[className][i][0]["name"] = para["name"]
                        return self.__factor[className][i][1]  # 返回factorData
                exec("from " + className + " import " + className)
                exec(className + "(para, self)")
                return self.getFactorData(para)
        else:  # 如果因子类名className不以Factor开头，那么就是nonFactor
            if className not in self.__nonFactor.keys():
                exec("from " + className + " import " + className)
                exec(className + "(para, self)")
                return self.getFactorData(para)
            else:
                for i in range(self.__nonFactor[className].__len__()):
                    tempDeepCopy1 = self.__nonFactor[className][i][0].copy()
                    tempDeepCopy2 = para.copy()
                    del tempDeepCopy1["name"]
                    del tempDeepCopy2["name"]
                    if "save" in tempDeepCopy1:
                        del tempDeepCopy1["save"]
                    if "save" in tempDeepCopy2:
                        del tempDeepCopy2["save"]
                    if tempDeepCopy1 == tempDeepCopy2:
                        return self.__nonFactor[className][i][1]
                exec("from " + className + " import " + className)
                exec(className + "(para, self)")
                return self.getFactorData(para)

    def getTradingUnderlyingCode(self):
        return self.__tradingUnderlyingCode

    def getFactorUnderlyingCode(self):
        return self.__factorUnderlyingCode

    def getFactorsNeedSave(self):
        FactorsSave = []
        for content in self.__factorsNeedSave:
            FactorsSave.append(content.getLastContent())
        return FactorsSave

    def getFactorNameNeedSave(self):
        return self.__factorNamesNeedSave

    def getLastFactors(self):
        if not self.__factorKeys:
            # 如果这个方法被调用了，说明所有factor已经初始化了，所以在这生成排序后的因子名
            self.__factorKeys = sorted(self.__factor.keys())
        lastFactors = []
        for iFactorKeys in self.__factorKeys:
            for iPara in range(self.__factor[iFactorKeys].__len__()):
                if self.__factor[iFactorKeys][iPara][0]["name"][0:6] == "factor":
                    lastFactors.append(self.__factor[iFactorKeys][iPara][1].getLastContent())
        return lastFactors

    def setPreDayTicks(self, pre_day_ticks):
        self.__pre_day_ticks = pre_day_ticks

    def getPreDayTicks(self):
        return self.__pre_day_ticks

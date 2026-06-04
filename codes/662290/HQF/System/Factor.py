# -*- coding: utf-8 -*-
"""
Created on Mon Aug  7 18:46:11 2017

@author: 006547
"""
import datetime
import time


class Factor:  # 基类
    def __init__(self, para, factorManagement):
        self.__lastContent = 0
        self.__lastTimeStamp = []
        self.__content = []
        self.__timeStamp = []
        self.__secondContentFillPrior = []
        self.__secondContentFillZero = []
        self.__secondTimeStamp = []
        self.__name = para["name"]
        self.__className = para["className"]
        self.__factorManagement = factorManagement
        self.__indexTradingUnderlying = para['indexTradingUnderlying']
        self.__indexFactorUnderlying = para['indexFactorUnderlying']

        # 因子获取数据和其他因子值的接口
        self.__tradingUnderlyingData = self.__factorManagement.getDataCollector().getTradingUnderlyingData()
        self.__factorUnderlyingData = self.__factorManagement.getDataCollector().getFactorUnderlyingData()

    def getFactorData(self, para):
        factor = self.__factorManagement.getFactorData(para)
        return factor

    def getTradingUnderlyingData(self, index):
        return self.__tradingUnderlyingData[index]

    def getFactorUnderlyingData(self, index):
        return self.__factorUnderlyingData[index]

    def getIndexTradingUnderlying(self):
        return self.__indexTradingUnderlying

    def getIndexFactorUnderlying(self):
        return self.__indexFactorUnderlying

    def addData(self, contentAdded, timeStampAdded):
        self.__content.append(contentAdded)
        self.__timeStamp.append(timeStampAdded)

        if len(self.__timeStamp) >= 2:
            timeSpread = int(self.__timeStamp[-1] - self.__timeStamp[-2])
            if datetime.datetime.fromtimestamp(self.__timeStamp[-2]).hour < 13 <= \
                    datetime.datetime.fromtimestamp(self.__timeStamp[-1]).hour:
                timeSpread = 1
            if timeSpread >= 2:
                for i in range(timeSpread - 1):
                    self.__secondContentFillPrior.append(self.__content[-2])
                    if type(self.__content[-2]) == list:
                        tempZeros = []
                        for j in range(len(self.__content[-2])):
                            tempZeros.append(0.)
                    else:
                        tempZeros = 0.
                    self.__secondContentFillZero.append(tempZeros)
                    self.__secondTimeStamp.append(self.__timeStamp[-2] + 1.0 + i)
            self.__secondContentFillPrior.append(self.__content[-1])
            self.__secondContentFillZero.append(self.__content[-1])
            self.__secondTimeStamp.append(self.__timeStamp[-1])
        elif len(self.__timeStamp) == 1:
            self.__secondContentFillPrior.append(self.__content[0])
            self.__secondContentFillZero.append(self.__content[0])
            self.__secondTimeStamp.append(self.__timeStamp[0])
        if len(self.__content) >= 1:
            self.__lastContent = self.__content[-1]
        else:
            self.__lastContent = []
        if len(self.__timeStamp) >= 1:
            self.__lastTimeStamp = self.__timeStamp[-1]
        else:
            self.__lastTimeStamp = []

    def getContent(self):
        return self.__content

    def getTimeStamp(self):
        return self.__timeStamp

    def getSecondContentFillPrior(self):
        return self.__secondContentFillPrior

    def getSecondContentFillZero(self):
        return self.__secondContentFillZero

    def getSecondTimeStamp(self):
        return self.__secondTimeStamp

    def getName(self):
        return self.__name

    def getClassName(self):
        return self.__className

    def getLastContent(self):
        return self.__lastContent

    def getLastTimeStamp(self):
        return self.__lastTimeStamp

    def getPriorSecondContent(self, paraPriorSecond):
        returnValue = []
        if len(self.__secondTimeStamp) > paraPriorSecond:
            returnValue = [self.__secondTimeStamp[-paraPriorSecond - 1],
                           self.__secondContentFillPrior[-paraPriorSecond - 1]]
        return returnValue

    def getPriorTickContent(self, paraPriorTick):
        returnValue = []
        if len(self.__timeStamp) > paraPriorTick:
            returnValue = [self.__timeStamp[-paraPriorTick - 1], self.__content[-paraPriorTick - 1]]
        return returnValue

    @staticmethod
    # 计算日内两个时间戳之间的间隔（秒）
    def getTimeLength(startTime, endTime):
        if time.localtime(endTime).tm_hour >= 13 and time.localtime(startTime).tm_hour < 12:
            returnValue = endTime - startTime - 5400  # 考虑午间休盘
        else:
            returnValue = endTime - startTime
        return returnValue

    # 提取指定区间中的因子数据，所取数据区间前闭后开
    # startLag和endLag参数均为相对于当前切片前推的时间间隔，且取值为非正数
    # frequency为startTime和endTime参数的时间单位，可以为"s"或者"min"
    # 例如，startLag=-120,endLag=-60,frequency="s",则取当前时刻前120s至前60s（不含）的因子数据
    def getIntervalContent(self, startLag, endLag, frequency):
        returnValue = []
        if frequency == "min":
            startLag = startLag * 60
            endLag = endLag * 60
        for i in range(len(self.__timeStamp)-1, -1, -1):
            if -startLag >= self.getTimeLength(self.__timeStamp[i], self.__timeStamp[-1]) > -endLag:
                returnValue.insert(0, self.__content[i])
            elif self.getTimeLength(self.__timeStamp[i], self.__timeStamp[-1]) > -startLag:
                break
        return returnValue
        
    def getPreDayTicks(self):
        return self.__factorManagement.getPreDayTicks()
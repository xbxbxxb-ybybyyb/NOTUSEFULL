# -*- coding: utf-8 -*-
"""
Created on Mon Aug  7 19:24:22 2017

@author: 006547
"""
import datetime


class Data:
    def __init__(self):
        self.__lastContent = []
        self.__lastTimeStamp = []
        self.__content = []
        self.__timeStamp = []
        self.__secondContentFillPrior = []
        self.__secondContentFillZero = []
        self.__secondTimeStamp = []

    def addData(self, contentAdded, timeStampAdded):
        self.__content.append(contentAdded)
        self.__timeStamp.append(timeStampAdded)

        if len(self.__timeStamp) >= 2:
            timeSpread = int(self.__timeStamp[-1] - self.__timeStamp[-2])
            if datetime.datetime.fromtimestamp(self.__timeStamp[-2]).hour < 13 <= datetime.datetime.fromtimestamp(
                    self.__timeStamp[-1]).hour:
                timeSpread = 1
            if timeSpread >= 2:
                for i in range(timeSpread - 1):
                    self.__secondContentFillPrior.append(self.__content[-2])
                    self.__secondContentFillZero.append(0.0)
                    self.__secondTimeStamp.append(self.__timeStamp[-2] + 1.0)
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

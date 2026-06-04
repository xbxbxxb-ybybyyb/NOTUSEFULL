#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/4/1 21:24


class TaskMeta:
    def __init__(self,
                 library,
                 code,
                 dataSource,
                 startDate, endDate,
                 daily, minute, tick, tran, order,
                 overwrite,
                 monitor,
                 hbase,
                 saveFile, savePath,
                 saveCheck, saveCheckPath,
                 updateMissing
                 ):

        self.__library = library
        self.__code = code
        self.__dataSource = dataSource
        self.__startDate = startDate
        self.__endDate = endDate
        self.__daily = daily
        self.__minute = minute
        self.__tick = tick
        self.__tran = tran
        self.__order = order
        self.__overwrite = overwrite
        self.__monitor = monitor
        self.__hbase = hbase
        self.__saveFile = saveFile
        self.__savePath = savePath
        self.__saveCheck = saveCheck
        self.__saveCheckPath = saveCheckPath
        self.__updateMissing = updateMissing

    def getLibrary(self):
        return self.__library

    def getCode(self):
        return self.__code

    def getDataSource(self):
        return self.__dataSource

    def getStartDate(self):
        return self.__startDate

    def getEndDate(self):
        return self.__endDate

    def getDaily(self):
        return self.__daily

    def getMinute(self):
        return self.__minute

    def getTick(self):
        return self.__tick

    def getTran(self):
        return self.__tran

    def getOrder(self):
        return self.__order

    def getOverwrite(self):
        return self.__overwrite

    def getMonitor(self):
        return self.__monitor

    def getHbase(self):
        return self.__hbase

    def getSaveFile(self):
        return self.__saveFile

    def getSavePath(self):
        return self.__savePath

    def getSaveCheck(self):
        return self.__saveCheck

    def getSaveCheckPath(self):
        return self.__saveCheckPath

    def getUpdateMissing(self):
        return self.__updateMissing

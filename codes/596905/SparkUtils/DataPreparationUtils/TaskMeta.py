class TaskMeta:
    def __init__(self,
                 marketDataLibrary,
                 code,
                 startDate, endDate,
                 daily, minute, tick,
                 mockTick, mockFreq,
                 overwrite,
                 monitor,
                 hbase,
                 saveFile, savePath,
                 env):

        self.__marketDataLibrary = marketDataLibrary
        self.__code = code
        self.__startDate = startDate
        self.__endDate = endDate
        self.__daily = daily
        self.__minute = minute
        self.__tick = tick
        self.__mockTick = mockTick
        self.__mockFreq = mockFreq
        self.__overwrite = overwrite
        self.__monitor = monitor
        self.__hbase = hbase
        self.__saveFile = saveFile
        self.__savePath = savePath
        self.__env = env

    def getMarketDataLibrary(self):
        return self.__marketDataLibrary

    def getCode(self):
        return self.__code

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

    def getMockTick(self):
        return self.__mockTick

    def getMockFreq(self):
        return self.__mockFreq

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

    def getEnv(self):
        return self.__env

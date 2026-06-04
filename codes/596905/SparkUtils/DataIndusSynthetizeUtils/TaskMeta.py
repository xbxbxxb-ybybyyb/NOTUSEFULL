class TaskMeta:
    def __init__(self,
                 marketDataLibrary,
                 indusCode,
                 startDate, endDate,
                 daily, minute, tick,
                 overwrite,
                 hbase,
                 saveFile, savePath,
                 env):

        self.__marketDataLibrary = marketDataLibrary
        self.__indusCode = indusCode
        self.__startDate = startDate
        self.__endDate = endDate
        self.__daily = daily
        self.__minute = minute
        self.__tick = tick
        self.__overwrite = overwrite
        self.__hbase = hbase
        self.__saveFile = saveFile
        self.__savePath = savePath
        self.__env = env

    def getMarketDataLibrary(self):
        return self.__marketDataLibrary

    def getIndusCode(self):
        return self.__indusCode

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

    def getOverwrite(self):
        return self.__overwrite

    def getHbase(self):
        return self.__hbase

    def getSaveFile(self):
        return self.__saveFile

    def getSavePath(self):
        return self.__savePath

    def getEnv(self):
        return self.__env

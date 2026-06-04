class TaskMeta:
    def __init__(self,marketDataLibrary, hdfsPath, stock, dateList, hbase, env):

        self.__marketDataLibrary = marketDataLibrary
        self.__hdfsPath = hdfsPath
        self.__stock = stock
        self.__dateList = dateList
        self.__hbase = hbase
        self.__env = env

    def getMarketDataLibrary(self):
        return self.__marketDataLibrary

    def getHdfsPath(self):
        return self.__hdfsPath

    def getStock(self):
        return self.__stock

    def getDateList(self):
        return self.__dateList

    def getHbase(self):
        return self.__hbase

    def getEnv(self):
        return self.__env

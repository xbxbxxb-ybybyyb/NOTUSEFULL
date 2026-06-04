class SparkTaskMeta:
    def __init__(self, marketDataLibrary, factorLibrary, assetType, underlyingAssetType, factorConfig, startDate,
                 endDate, stockSetTS, logFilePath, taskID):
        self.__marketDataLibrary = marketDataLibrary
        self.__factorLibrary = factorLibrary
        self.__assetType = assetType
        self.__underlyingAssetType = underlyingAssetType
        self.__factorConfig = factorConfig
        self.__startDate = startDate
        self.__endDate = endDate
        self.__stockSetTS = stockSetTS
        self.__logFilePath = logFilePath
        self.__taskID = taskID

    def getMarketDataLibrary(self):
        return self.__marketDataLibrary

    def getOutputLibrary(self):
        return self.__factorLibrary

    def getAssetType(self):
        return self.__assetType

    def getUnderlyingAssetType(self):
        return self.__underlyingAssetType

    def getStartDate(self):
        return self.__startDate

    def getEndDate(self):
        return self.__endDate

    def getFactorConfig(self):
        return self.__factorConfig

    def getStockSetTS(self):
        return self.__stockSetTS

    def getLogFilePath(self):
        return self.__logFilePath

    def getTaskID(self):
        return self.__taskID

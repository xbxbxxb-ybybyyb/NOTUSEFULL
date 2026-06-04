class SparkTaskMeta:
    def __init__(self, marketDataLibrary, tickLibrary, tranOrderLibrary, l2pTickLibrary, l2pTranOrderLibrary,
                 infLibrary, tickCleanMode, tickFactorLibrary, l2pTickFactorLibrary, minuteFactorLibrary, assetType,
                 underlyingAssetType, factorConfig, startDate, endDate, stockSetTS, stockSetL2P, logFilePath, taskID):
        self.__marketDataLibrary = marketDataLibrary
        self.__tickLibrary = tickLibrary
        self.__tranOrderLibrary = tranOrderLibrary
        self.__l2pTickLibrary = l2pTickLibrary
        self.__l2pTranOrderLibrary = l2pTranOrderLibrary
        self.__infLibrary = infLibrary
        self.__tickCleanMode = tickCleanMode
        self.__tickFactorLibrary = tickFactorLibrary
        self.__l2pTickFactorLibrary = l2pTickFactorLibrary
        self.__minuteFactorLibrary = minuteFactorLibrary
        self.__assetType = assetType
        self.__underlyingAssetType = underlyingAssetType
        self.__factorConfig = factorConfig
        self.__startDate = startDate
        self.__endDate = endDate
        self.__stockSetTS = stockSetTS
        self.__stockSetL2P = stockSetL2P
        self.__logFilePath = logFilePath
        self.__taskID = taskID

    @property
    def marketDataLibrary(self):
        return self.__marketDataLibrary

    @property
    def tickLibrary(self):
        return self.__tickLibrary

    @property
    def tranOrderLibrary(self):
        return self.__tranOrderLibrary

    @property
    def l2pTickLibrary(self):
        return self.__l2pTickLibrary

    @property
    def l2pTranOrderLibrary(self):
        return self.__l2pTranOrderLibrary

    @property
    def infLibrary(self):
        return self.__infLibrary

    @property
    def tickCleanMode(self):
        return self.__tickCleanMode

    @property
    def tickOutputLibrary(self):
        return self.__tickFactorLibrary

    @property
    def l2pTickOutputLibrary(self):
        return self.__l2pTickFactorLibrary

    @property
    def minuteOutputLibrary(self):
        return self.__minuteFactorLibrary

    @property
    def assetType(self):
        return self.__assetType

    @property
    def underlyingAssetType(self):
        return self.__underlyingAssetType

    @property
    def startDate(self):
        return self.__startDate

    @property
    def endDate(self):
        return self.__endDate

    @property
    def factorConfig(self):
        return self.__factorConfig

    @property
    def stockSetTS(self):
        return self.__stockSetTS

    @property
    def stockSetL2P(self):
        return self.__stockSetL2P

    @property
    def logFilePath(self):
        return self.__logFilePath

    @property
    def taskID(self):
        return self.__taskID

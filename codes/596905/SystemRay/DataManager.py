from System.COLUMN_CONFIG import TICK_COLUMN_NAMES1, TICK_COLUMN_NAMES2, MINUTE_COLUMN_NAMES, DAILY_COLUMN_NAMES


class DataManager:
    """
    Load data via HFData dynamically
    """

    def __init__(self, configAnalyzer):
        self.__configAnalyzer = configAnalyzer

        self.__stockSetAll = None
        self.__indexSet = None
        self.__allTradingDayDict = None
        self.__invalidTradingDayDict = None
        self.__tickDataDict1 = None
        self.__tickDataDict2 = None
        self.__minuteDataDict = None
        self.__dailyDataDict = None
        self.__dailyDataDictOriginal = None
        self.__tickDataDict1SplitAdjusted = None
        self.__tickDataDict2SplitAdjusted = None
        self.__minuteDataDictSplitAdjusted = None
        self.__dailyDataDictSplitAdjusted = None

    def setStockSetAll(self, stockSetAll):
        self.__stockSetAll = stockSetAll

    def setIndexSet(self, indexSet):
        self.__indexSet = indexSet

    def setTickDataDict(self, tickDataDictTuple):
        (self.__tickDataDict1, self.__tickDataDict2,
         self.__tickDataDict1SplitAdjusted, self.__tickDataDict2SplitAdjusted) = tickDataDictTuple

    def setMinuteDataDict(self, minuteDataDictTuple):
        self.__minuteDataDict, self.__minuteDataDictSplitAdjusted = minuteDataDictTuple

    def setDailyDataDict(self, dailyDataDictTuple):
        self.__dailyDataDict, self.__dailyDataDictSplitAdjusted = dailyDataDictTuple

    def setAllTradingDayDict(self, allTradingDayDict):
        self.__allTradingDayDict = allTradingDayDict

    def setInvalidTradingDayDict(self, invalidTradingDayDict):
        self.__invalidTradingDayDict = invalidTradingDayDict

    def reshapeData(self):
        for stock, tickData in self.__tickDataDict1.items():
            if tickData.shape[0] == 0:
                self.__tickDataDict1[stock] = tickData.reshape(-1, len(TICK_COLUMN_NAMES1))
        for stock, tickData in self.__tickDataDict2.items():
            if tickData.shape[0] == 0:
                self.__tickDataDict2[stock] = tickData.reshape(-1, len(TICK_COLUMN_NAMES2))

        if self.__tickDataDict1SplitAdjusted is not None:
            for stock, tickData in self.__tickDataDict1SplitAdjusted.items():
                if tickData.shape[0] == 0:
                    self.__tickDataDict1SplitAdjusted[stock] = tickData.reshape(-1, len(TICK_COLUMN_NAMES1))
            for stock, tickData in self.__tickDataDict2SplitAdjusted.items():
                if tickData.shape[0] == 0:
                    self.__tickDataDict2SplitAdjusted[stock] = tickData.reshape(-1, len(TICK_COLUMN_NAMES2))

        for stock, minuteData in self.__minuteDataDict.items():
            if minuteData.shape[0] == 0:
                self.__minuteDataDict[stock] = minuteData.reshape(-1, len(MINUTE_COLUMN_NAMES))

        if self.__minuteDataDictSplitAdjusted is not None:
            for stock, minuteData in self.__minuteDataDictSplitAdjusted.items():
                if minuteData.shape[0] == 0:
                    self.__minuteDataDictSplitAdjusted[stock] = minuteData.reshape(-1, len(MINUTE_COLUMN_NAMES))

        for stock, dailyData in self.__dailyDataDict.items():
            if dailyData.shape[0] == 0:
                self.__dailyDataDict[stock] = dailyData.reshape(-1, len(DAILY_COLUMN_NAMES))

        if self.__dailyDataDictSplitAdjusted is not None:
            for stock, dailyData in self.__dailyDataDict.items():
                if dailyData.shape[0] == 0:
                    self.__dailyDataDict[stock] = dailyData.reshape(-1, len(DAILY_COLUMN_NAMES))

    def getTickData(self, stockList, splitAdjusted):
        """
        For DataBroadcaster
        """
        if splitAdjusted:
            return ({stock: self.__tickDataDict1SplitAdjusted[stock] for stock in stockList},
                    {stock: self.__tickDataDict2SplitAdjusted[stock]
                     for stock in stockList if stock in self.__stockSetAll})
        else:
            return ({stock: self.__tickDataDict1[stock] for stock in stockList},
                    {stock: self.__tickDataDict2[stock] for stock in stockList if stock in self.__stockSetAll})

    def getMinuteData(self, stockList, splitAdjusted):
        """
        For DataBroadcaster
        """
        if splitAdjusted:
            return {stock: self.__minuteDataDictSplitAdjusted[stock] for stock in stockList}
        else:
            return {stock: self.__minuteDataDict[stock] for stock in stockList}

    def getDailyData(self, stockList, splitAdjusted):
        """
        For DataBroadcaster
        """
        if splitAdjusted:
            return {stock: self.__dailyDataDictSplitAdjusted[stock] for stock in stockList}
        else:
            return {stock: self.__dailyDataDict[stock] for stock in stockList}

    def getIndexSet(self):
        """
        For DataBroadcaster
        """
        return self.__indexSet

    def getSplitAdjustedNeeded(self):
        """
        For DataBroadcaster
        """
        return self.__configAnalyzer.getDataRequirements()["splitAdjustedNeeded"]

    def getAllTradingDayList(self, stock):
        """
        For DataBroadcaster
        """
        allTradingDayList = list(self.__allTradingDayDict[stock])
        allTradingDayList.sort()

        return allTradingDayList

    def getStockList(self, stock, date, stockGroup):
        """
        For FactorManager
        """
        return self.__configAnalyzer.getStockList(stock, date, stockGroup)

    def getIndustryCode(self, stock, date, industryGroup):
        """
        For FactorManager
        """
        return self.__configAnalyzer.getIndustryCode(stock, date, industryGroup)

    def getValidTradingDayList(self, stock, sDate, eDate):
        """
        For Calculation Scheduler & SparkLauncher
        """
        validTradingDaySet = self.__configAnalyzer.getValidTradingDaySet(stock, sDate, eDate)
        validTradingDayList = list(validTradingDaySet - self.__invalidTradingDayDict[stock])
        validTradingDayList.sort()

        return validTradingDayList

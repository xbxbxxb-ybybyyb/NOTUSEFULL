import gc
import datetime as dt
import numpy as np
import pandas as pd
from Constants.INDEX_LIST import INDEX_LIST
from System.TradingDay import getTradingDay, getNDaysOff
from System.COLUMN_CONFIG import (TICK_COLUMN_NAMES1, TICK_COLUMN_NAMES2, TRANSACTION_COLUMN_NAMES, ORDER_COLUMN_NAMES,
                                  MINUTE_COLUMN_NAMES, DAILY_COLUMN_NAMES, TICK_COLUMN_INDEX_DICT1,
                                  TRANSACTION_COLUMN_INDEX_DICT, ORDER_COLUMN_INDEX_DICT)
from System.COLUMN_CONFIG import (INDEX_TICK_COLUMN_NAMES, INDEX_MINUTE_COLUMN_NAMES, INDEX_DAILY_COLUMN_NAMES,
                                  INDEX_TICK_COLUMN_INDEX_DICT)
from System.COLUMN_CONFIG import (CB_TICK_COLUMN_NAMES1, CB_TICK_COLUMN_NAMES2, CB_TRANSACTION_COLUMN_NAMES,
                                  CB_ORDER_COLUMN_NAMES, CB_MINUTE_COLUMN_NAMES, CB_DAILY_COLUMN_NAMES,
                                  CB_TICK_COLUMN_INDEX_DICT1, CB_TRANSACTION_COLUMN_INDEX_DICT,
                                  CB_ORDER_COLUMN_INDEX_DICT)
from HFDataLoader.HFData import HFData


class CBDataManager:
    """
    Load data via HFData dynamically
    """

    def __init__(self, libraryName, tickLibrary, tranOrderLibrary, l2pTickLibrary, l2pTranOrderLibrary, tickCleanMode, assetType,
                 underlyingAssetType, startDate, endDate, stockSetTS, stockSetCS, stockSetAll, stockSetL2P,
                 configAnalyzer):
        self.__PRICE_COLUMN_NAMES_1 = ["PreviousClose", "LastPrice", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "AvgBidPrice", "AvgOfferPrice"]
        self.__PRICE_COLUMN_NAMES_2 = ["BidPrice", "AskPrice"]
        self.__PRICE_COLUMN_NAME_3 = "Transactions"
        self.__PRICE_COLUMN_NAME_3_2 = "Orders"
        self.__PRICE_COLUMN_NAME_3_3 = "Cancellations"
        self.__PRICE_COLUMN_NAMES_4 = ["OpenPrice", "HighPrice", "LowPrice", "ClosePrice"]
        self.__PRICE_COLUMN_NAMES_5 = ["PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "ClosePrice"]

        self.__library = libraryName
        self.__tickLibrary = tickLibrary
        self.__tranOrderLibrary = tranOrderLibrary
        self.__l2pTickLibrary = l2pTickLibrary
        self.__l2pTranOrderLibrary = l2pTranOrderLibrary
        self.__tickCleanMode = tickCleanMode
        self.__assetType = assetType
        self.__underlyingAssetType = underlyingAssetType
        self.__startDate = startDate
        self.__endDate = endDate
        self.__stockSetTS = stockSetTS
        self.__stockSetCS = stockSetCS
        self.__stockSetAll = stockSetAll
        self.__stockSetL2P = stockSetL2P
        self.__configAnalyzer = configAnalyzer

        self.__tickColumnNames1 = CB_TICK_COLUMN_NAMES1
        self.__tickColumnNames2 = CB_TICK_COLUMN_NAMES2
        self.__transactionColumnNames = CB_TRANSACTION_COLUMN_NAMES
        self.__orderColumnNames = CB_ORDER_COLUMN_NAMES
        self.__minuteColumnNames = CB_MINUTE_COLUMN_NAMES
        self.__dailyColumnNames = CB_DAILY_COLUMN_NAMES
        self.__tickColumnIndexDict1 = CB_TICK_COLUMN_INDEX_DICT1
        self.__transactionColumnIndexDict = CB_TRANSACTION_COLUMN_INDEX_DICT
        self.__orderColumnIndexDict = CB_ORDER_COLUMN_INDEX_DICT

        self.__tickColumnNames1UA = TICK_COLUMN_NAMES1
        self.__tickColumnNames2UA = TICK_COLUMN_NAMES2
        self.__transactionColumnNamesUA = TRANSACTION_COLUMN_NAMES
        self.__orderColumnNamesUA = ORDER_COLUMN_NAMES
        self.__minuteColumnNamesUA = MINUTE_COLUMN_NAMES
        self.__dailyColumnNamesUA = DAILY_COLUMN_NAMES
        self.__tickColumnIndexDict1UA = TICK_COLUMN_INDEX_DICT1
        self.__transactionColumnIndexDictUA = TRANSACTION_COLUMN_INDEX_DICT
        self.__orderColumnIndexDictUA = ORDER_COLUMN_INDEX_DICT
        self.__priceColumnIndex3UA = TRANSACTION_COLUMN_INDEX_DICT["Price"]
        self.__priceColumnIndex3_2UA = ORDER_COLUMN_INDEX_DICT["Price"]

        dataRequirements = self.__configAnalyzer.getDataRequirements()
        self.__historicalTickDataLength = dataRequirements["maxTickLength"]
        self.__historicalMinuteDataLength = dataRequirements["maxMinuteLength"]
        self.__historicalDailyDataLength = dataRequirements["maxDailyLength"]
        self.__historicalTickDataLengthCS = dataRequirements["maxTickLengthCS"]
        self.__historicalMinuteDataLengthCS = dataRequirements["maxMinuteLengthCS"]
        self.__historicalDailyDataLengthCS = dataRequirements["maxDailyLengthCS"]
        self.__historicalTickDataLengthIndex = dataRequirements["maxTickLengthIndex"]
        self.__historicalMinuteDataLengthIndex = dataRequirements["maxMinuteLengthIndex"]
        self.__historicalDailyDataLengthIndex = dataRequirements["maxDailyLengthIndex"]
        self.__historicalTickDataLengthUA = dataRequirements["maxTickLengthUA"]
        self.__historicalMinuteDataLengthUA = dataRequirements["maxMinuteLengthUA"]
        self.__historicalDailyDataLengthUA = dataRequirements["maxDailyLengthUA"]
        self.__dataType = dataRequirements["dataType"]
        self.__dataTypeCS = dataRequirements["dataTypeCS"]
        self.__dataTypeIndex = dataRequirements["dataTypeIndex"]
        self.__dataTypeUA = dataRequirements["dataTypeUA"]
        self.__indexGroup = dataRequirements["indexGroup"]
        self.__splitAdjustedNeeded = dataRequirements["splitAdjustedNeeded"]
        self.__isUseUnderlyingAsset = dataRequirements["isUseUnderlyingAsset"]

        self.__invalidTradingDayDict = {}
        self.__invalidTradingDayDictUA = {}
        self.__adjFactorDict = {}
        self.__tickDataDict1 = {}
        self.__tickDataDict2 = {}
        self.__earlyDataMorningDict = {}
        self.__earlyDataAfternoonDict = {}
        self.__minuteDataDict = {}
        self.__dailyDataDict = {}
        self.__tickDataDict1SplitAdjusted = {}
        self.__tickDataDict2SplitAdjusted = {}
        self.__earlyDataMorningDictSplitAdjusted = {}
        self.__earlyDataAfternoonDictSplitAdjusted = {}
        self.__minuteDataDictSplitAdjusted = {}
        self.__dailyDataDictSplitAdjusted = {}

        self.__loadHFData()

    def __loadHFData(self):
        self.__loadStockHFData()
        self.__loadIndexHFData()
        self.__loadUAHFData()

    def __loadStockHFData(self):
        self.__HFDataDict = {stock: HFData(self.__library, stock, tick_library=self.__tickLibrary, tran_order_library=self.__tranOrderLibrary, tick_clean_mode=self.__tickCleanMode) for stock in self.__stockSetAll}
        self.__HFDataDictForL2P = {stock: HFData(self.__library, stock, tick_library=self.__l2pTickLibrary, tran_order_library=self.__l2pTranOrderLibrary, tick_clean_mode=self.__tickCleanMode) for stock in self.__stockSetAll}

    def __loadIndexHFData(self):
        self.__indexSet = set()  # 宽基指数代码 + 行业指数代码
        for index in self.__indexGroup:
            if index in INDEX_LIST:
                self.__indexSet.add(index)
            else:
                for date in getTradingDay(self.__startDate, self.__endDate):
                    for stock in self.__stockSetTS:
                        targetIndustry = self.__configAnalyzer.getIndustryCode(stock, date, index)
                        if targetIndustry is not None:
                            self.__indexSet.add(targetIndustry)
        self.__HFDataDictForIndex = {index: HFData(self.__library, index, tick_library=self.__tickLibrary, tran_order_library=self.__tranOrderLibrary) for index in self.__indexSet}

    def __loadUAHFData(self):
        self.__UASet = set()
        for date in getTradingDay(self.__startDate, self.__endDate):
            for stock in self.__stockSetTS:
                underlyingAsset = self.__configAnalyzer.getUnderlyingAsset(stock, date)
                if underlyingAsset is not None:
                    self.__UASet.add(underlyingAsset)
        self.__HFDataDictForUA = {ua: HFData(self.__library, ua, tick_library=self.__tickLibrary, tran_order_library=self.__tranOrderLibrary) for ua in self.__UASet}

    def loadData(self):
        """
        For Calculation Scheduler & SparkLauncher
        """
        self.__invalidTradingDayDict = {}

        self.__loadDailyData()
        self.__loadMinuteData()
        self.__loadTickDataFirstTime()

        self.__loadIndexDataFirstTime()

        if self.__isUseUnderlyingAsset:
            self.__loadUADailyData()
            self.__loadUAMinuteData()
            self.__loadUATickDataFirstTime()

        if self.__splitAdjustedNeeded:
            self.__loadSplitAdjustedDataFirstTime()

        self.__convertDataFrameIntoNdArray()

    def getTickData(self, stockList, splitAdjusted):
        """
        For DataBroadcaster
        """
        if splitAdjusted:
            return ({stock: self.__tickDataDict1SplitAdjusted[stock]
                     for stock in stockList if stock in self.__tickDataDict1SplitAdjusted},
                    {stock: self.__tickDataDict2SplitAdjusted[stock]
                     for stock in stockList if stock in self.__tickDataDict2SplitAdjusted})
        else:
            return ({stock: self.__tickDataDict1[stock] for stock in stockList if stock in self.__tickDataDict1},
                    {stock: self.__tickDataDict2[stock] for stock in stockList if stock in self.__tickDataDict2})

    def getEarlyDataMorning(self, stockList, splitAdjusted):
        """
        For DataBroadcaster
        """
        if splitAdjusted:
            return {stock: self.__earlyDataMorningDictSplitAdjusted[stock] for stock in stockList if stock in self.__earlyDataMorningDictSplitAdjusted}
        else:
            return {stock: self.__earlyDataMorningDict[stock] for stock in stockList if stock in self.__earlyDataMorningDict}

    def getEarlyDataAfternoon(self, stockList, splitAdjusted):
        """
        For DataBroadcaster
        """
        if splitAdjusted:
            return {stock: self.__earlyDataAfternoonDictSplitAdjusted[stock] for stock in stockList if stock in self.__earlyDataAfternoonDictSplitAdjusted}
        else:
            return {stock: self.__earlyDataAfternoonDict[stock] for stock in stockList if stock in self.__earlyDataAfternoonDict}

    def getMinuteData(self, stockList, splitAdjusted):
        """
        For DataBroadcaster
        """
        if splitAdjusted:
            return {stock: self.__minuteDataDictSplitAdjusted[stock]
                    for stock in stockList if stock in self.__minuteDataDictSplitAdjusted}
        else:
            return {stock: self.__minuteDataDict[stock] for stock in stockList if stock in self.__minuteDataDict}

    def getDailyData(self, stockList, splitAdjusted):
        """
        For DataBroadcaster
        """
        if splitAdjusted:
            return {stock: self.__dailyDataDictSplitAdjusted[stock]
                    for stock in stockList if stock in self.__dailyDataDictSplitAdjusted}
        else:
            return {stock: self.__dailyDataDict[stock] for stock in stockList if stock in self.__dailyDataDict}

    def getIndexSet(self):
        """
        For DataBroadcaster
        """
        return self.__indexSet

    def getUASet(self):
        """
        For DataBroadcaster
        """
        return self.__UASet

    def getSplitAdjustedNeeded(self):
        """
        For DataBroadcaster
        """
        return self.__splitAdjustedNeeded

    def getAllTradingDayList(self):
        """
        For DataBroadcaster
        """
        dayOffset = max(
            self.__historicalTickDataLength,
            self.__historicalTickDataLengthCS,
            self.__historicalTickDataLengthIndex,
            self.__historicalTickDataLengthUA,
            self.__historicalMinuteDataLength,
            self.__historicalMinuteDataLengthCS,
            self.__historicalMinuteDataLengthIndex,
            self.__historicalMinuteDataLengthUA,
            self.__historicalDailyDataLength,
            self.__historicalDailyDataLengthCS,
            self.__historicalDailyDataLengthIndex,
            self.__historicalDailyDataLengthUA,
        )
        allTradingDayList = getTradingDay(getNDaysOff(self.__startDate, dayOffset), self.__endDate)

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

    def getUnderlyingAsset(self, stock, date):
        """
        For FactorManager
        """
        return self.__configAnalyzer.getUnderlyingAsset(stock, date)

    def getValidTradingDayList(self, stock, sDate, eDate):
        """
        For Calculation Scheduler & SparkLauncher
        """
        validTradingDaySet = self.__configAnalyzer.getValidTradingDaySet(stock, sDate, eDate)
        validTradingDayList = list(validTradingDaySet - self.__invalidTradingDayDict[stock])
        validTradingDayList.sort()

        return validTradingDayList

    def updateTickData(self, date):
        """
        For Calculation Scheduler & SparkLauncher
        """
        self.__updateTickData(date)
        self.__updateIndexTickData(date)
        self.__updateUATickData(date)

        gc.collect()

    def __loadDailyData(self):
        startDate = getNDaysOff(
            self.__startDate,
            max(self.__historicalDailyDataLength,
                self.__historicalMinuteDataLength,
                self.__historicalTickDataLength,
                self.__historicalDailyDataLengthCS,
                self.__historicalMinuteDataLengthCS,
                self.__historicalTickDataLengthCS)
        )
        allTradingDayList = getTradingDay(startDate, self.__endDate)

        for stock in self.__stockSetAll:
            data = self.__HFDataDict[stock].get_daily_data(startDate, self.__endDate).astype(np.float64)

            data = data.reindex(allTradingDayList)
            data["Date"] = allTradingDayList

            data.index.name = None
            data = data.sort_values("Date")
            data = data[self.__dailyColumnNames]

            invalidTradingDaySet = set(data[data["TradeStatus"] != 1].index)

            self.__invalidTradingDayDict[stock] = invalidTradingDaySet
            self.__dailyDataDict[stock] = data.astype(np.float64)

    def __loadMinuteData(self):
        for stock in self.__stockSetAll:
            # 播放+截面 播放 截面
            # 实时+历史 历史
            if stock in self.__stockSetTS and stock in self.__stockSetCS:
                startDate = getNDaysOff(self.__startDate, max(self.__historicalMinuteDataLength, self.__historicalMinuteDataLengthCS))
                endDate = self.__startDate if "Minute" in self.__dataType or "Minute" in self.__dataTypeCS else getNDaysOff(self.__startDate, 1)
            elif stock in self.__stockSetTS and stock not in self.__stockSetCS:
                startDate = getNDaysOff(self.__startDate, self.__historicalMinuteDataLength)
                endDate = self.__startDate if "Minute" in self.__dataType else getNDaysOff(self.__startDate, 1)
            elif stock not in self.__stockSetTS and stock in self.__stockSetCS:
                startDate = getNDaysOff(self.__startDate, self.__historicalMinuteDataLengthCS)
                endDate = self.__startDate if "Minute" in self.__dataTypeCS else getNDaysOff(self.__startDate, 1)
            else:  # 同时不需要播放和截面
                raise Exception(f"Unexpected case when loading tick data first time: {stock}")

            if startDate > endDate:  # 不需要Minute数据
                self.__minuteDataDict[stock] = pd.DataFrame(columns=self.__minuteColumnNames, dtype=np.float64)
            else:  # 需要Minute数据
                self.__minuteDataDict[stock] = self.__preprocessMinuteData(stock, startDate, endDate)

    def __loadTickDataFirstTime(self):
        for stock in self.__stockSetAll:
            # 播放+截面 播放 截面
            # 实时+历史 历史
            if stock in self.__stockSetTS and stock in self.__stockSetCS:
                startDate = getNDaysOff(self.__startDate, max(self.__historicalTickDataLength, self.__historicalTickDataLengthCS))
                endDate = self.__startDate if "Tick" in self.__dataType or "Tick" in self.__dataTypeCS else getNDaysOff(self.__startDate, 1)
            elif stock in self.__stockSetTS and stock not in self.__stockSetCS:
                startDate = getNDaysOff(self.__startDate, self.__historicalTickDataLength)
                endDate = self.__startDate if "Tick" in self.__dataType else getNDaysOff(self.__startDate, 1)
            elif stock not in self.__stockSetTS and stock in self.__stockSetCS:
                startDate = getNDaysOff(self.__startDate, self.__historicalTickDataLengthCS)
                endDate = self.__startDate if "Tick" in self.__dataTypeCS else getNDaysOff(self.__startDate, 1)
            else:  # 同时不需要播放和截面
                raise Exception(f"Unexpected case when loading tick data first time: {stock}")

            if startDate > endDate:  # 不需要Tick数据
                self.__tickDataDict1[stock] = pd.DataFrame(columns=self.__tickColumnNames1, dtype=np.float64)
                self.__tickDataDict2[stock] = pd.DataFrame(columns=self.__tickColumnNames2)
            else:  # 需要Tick数据
                self.__tickDataDict1[stock], self.__tickDataDict2[stock], self.__earlyDataMorningDict[stock], self.__earlyDataAfternoonDict[stock] = self.__preprocessTickData(stock, startDate, endDate)

    def __loadIndexDataFirstTime(self):
        for index in self.__indexSet:
            startDate = getNDaysOff(self.__startDate, self.__historicalDailyDataLengthIndex)
            endDate = self.__endDate
            if startDate > endDate:
                self.__dailyDataDict[index] = pd.DataFrame(columns=INDEX_DAILY_COLUMN_NAMES, dtype=np.float64)
            else:
                self.__dailyDataDict[index] = self.__preprocessIndexDailyData(index, startDate, endDate)

            startDate = getNDaysOff(self.__startDate, self.__historicalMinuteDataLengthIndex)
            endDate = self.__endDate if "Minute" in self.__dataTypeIndex else getNDaysOff(self.__endDate, 1)
            if startDate > endDate:
                self.__minuteDataDict[index] = pd.DataFrame(columns=INDEX_MINUTE_COLUMN_NAMES, dtype=np.float64)
            else:
                self.__minuteDataDict[index] = self.__preprocessIndexMinuteData(index, startDate, endDate)

            startDate = getNDaysOff(self.__startDate, self.__historicalTickDataLengthIndex)
            endDate = self.__startDate if "Tick" in self.__dataTypeIndex else getNDaysOff(self.__startDate, 1)
            if startDate > endDate:
                self.__tickDataDict1[index] = pd.DataFrame(columns=INDEX_TICK_COLUMN_NAMES, dtype=np.float64)
            else:
                self.__tickDataDict1[index] = self.__preprocessIndexTickData(index, startDate, endDate)

    def __loadUADailyData(self):
        startDate = getNDaysOff(
            self.__startDate,
            max(self.__historicalDailyDataLengthUA,
                self.__historicalMinuteDataLengthUA,
                self.__historicalTickDataLengthUA)
        )
        allTradingDayList = getTradingDay(startDate, self.__endDate)

        for ua in self.__UASet:
            data = self.__HFDataDictForUA[ua].get_daily_data(startDate, self.__endDate).astype(np.float64)

            data = data.reindex(allTradingDayList)
            data["Date"] = allTradingDayList

            data.index.name = None
            data = data.sort_values("Date")
            data = data[self.__dailyColumnNamesUA]

            invalidTradingDaySet = set(data[data["TradeStatus"] != 1].index)

            self.__invalidTradingDayDictUA[ua] = invalidTradingDaySet
            self.__dailyDataDict[ua] = data.astype(np.float64)

            if self.__splitAdjustedNeeded:
                self.__adjFactorDict[ua] = data["AdjFactor"].astype(np.float64)
                self.__dailyDataDictSplitAdjusted[ua] = data.astype(np.float64)

    def __loadUAMinuteData(self):
        for ua in self.__UASet:
            startDate = getNDaysOff(self.__startDate, self.__historicalMinuteDataLengthUA)
            endDate = self.__startDate if "Minute" in self.__dataTypeUA else getNDaysOff(self.__startDate, 1)

            if startDate > endDate:  # 不需要Minute数据
                self.__minuteDataDict[ua] = pd.DataFrame(columns=self.__minuteColumnNamesUA, dtype=np.float64)
            else:  # 需要Minute数据
                self.__minuteDataDict[ua] = self.__preprocessMinuteData(ua, startDate, endDate)

            if self.__splitAdjustedNeeded:
                self.__minuteDataDictSplitAdjusted[ua] = self.__minuteDataDict[ua].copy()

    def __loadUATickDataFirstTime(self):
        for ua in self.__UASet:
            startDate = getNDaysOff(self.__startDate, self.__historicalTickDataLengthUA)
            endDate = self.__startDate if "Tick" in self.__dataTypeUA else getNDaysOff(self.__startDate, 1)

            if startDate > endDate:  # 不需要Tick数据
                self.__tickDataDict1[ua] = pd.DataFrame(columns=self.__tickColumnNames1UA, dtype=np.float64)
                self.__tickDataDict2[ua] = pd.DataFrame(columns=self.__tickColumnNames2UA)
                if self.__splitAdjustedNeeded:
                    self.__tickDataDict1SplitAdjusted[ua] = pd.DataFrame(columns=self.__tickColumnNames1UA, dtype=np.float64)
                    self.__tickDataDict2SplitAdjusted[ua] = pd.DataFrame(columns=self.__tickColumnNames2UA)
            else:  # 需要Tick数据
                self.__tickDataDict1[ua], self.__tickDataDict2[ua] = self.__preprocessUATickData(ua, startDate, endDate)
                if self.__splitAdjustedNeeded:
                    self.__tickDataDict1SplitAdjusted[ua], self.__tickDataDict2SplitAdjusted[ua] = self.__preprocessUATickData(ua, startDate, endDate)

    def __loadSplitAdjustedDataFirstTime(self):
        for stock, tickData in self.__tickDataDict1SplitAdjusted.items():
            tickData.loc[:, self.__PRICE_COLUMN_NAMES_1] = tickData.loc[:, self.__PRICE_COLUMN_NAMES_1].multiply(
                self.__adjFactorDict[stock].reindex(tickData.index),
                axis=0
            )

        for stock, tickData in self.__tickDataDict2SplitAdjusted.items():
            if stock not in self.__UASet:
                raise Exception(f"Unexpected symbol: {stock}")

            for date in tickData.index.unique().tolist():
                for priceColumnName in self.__PRICE_COLUMN_NAMES_2:
                    for priceData in tickData.loc[[date], priceColumnName]:
                        if priceData is not None:
                            priceData *= self.__adjFactorDict[stock][date]
                for transactionData in tickData.loc[[date], self.__PRICE_COLUMN_NAME_3]:
                    if transactionData is not None:
                        transactionData[:, self.__priceColumnIndex3UA] *= self.__adjFactorDict[stock][date]
                for cancellationData in tickData.loc[[date], self.__PRICE_COLUMN_NAME_3_3]:
                    if cancellationData is not None:
                        cancellationData[:, self.__priceColumnIndex3UA] *= self.__adjFactorDict[stock][date]
                for orderData in tickData.loc[[date], self.__PRICE_COLUMN_NAME_3_2]:
                    if orderData is not None:
                        orderData[:, self.__priceColumnIndex3_2UA] *= self.__adjFactorDict[stock][date]

        for stock, minuteData in self.__minuteDataDictSplitAdjusted.items():
            minuteData.loc[:, self.__PRICE_COLUMN_NAMES_4] = minuteData.loc[:, self.__PRICE_COLUMN_NAMES_4].multiply(
                self.__adjFactorDict[stock].reindex(minuteData.index),
                axis=0
            )

        for stock, dailyData in self.__dailyDataDictSplitAdjusted.items():
            dailyData.loc[:, self.__PRICE_COLUMN_NAMES_5] = dailyData.loc[:, self.__PRICE_COLUMN_NAMES_5].multiply(
                self.__adjFactorDict[stock].reindex(dailyData.index),
                axis=0
            )

    def __convertDataFrameIntoNdArray(self):
        self.__tickDataDict1 = {stock: tickData.values for stock, tickData in self.__tickDataDict1.items()}
        self.__tickDataDict2 = {stock: tickData.values for stock, tickData in self.__tickDataDict2.items()}
        self.__minuteDataDict = {stock: minuteData.values for stock, minuteData in self.__minuteDataDict.items()}
        self.__dailyDataDict = {stock: dailyData.values for stock, dailyData in self.__dailyDataDict.items()}

        if self.__splitAdjustedNeeded:
            self.__tickDataDict1SplitAdjusted = {
                stock: tickData.values for stock, tickData in self.__tickDataDict1SplitAdjusted.items()
            }
            self.__tickDataDict2SplitAdjusted = {
                stock: tickData.values for stock, tickData in self.__tickDataDict2SplitAdjusted.items()
            }
            self.__minuteDataDictSplitAdjusted = {
                stock: minuteData.values for stock, minuteData in self.__minuteDataDictSplitAdjusted.items()
            }
            self.__dailyDataDictSplitAdjusted = {
                stock: dailyData.values for stock, dailyData in self.__dailyDataDictSplitAdjusted.items()
            }

    def __updateTickData(self, date):
        for stock in self.__stockSetAll:
            if stock in self.__stockSetTS and stock in self.__stockSetCS:
                updateDate = date if "Tick" in self.__dataType or "Tick" in self.__dataTypeCS else getNDaysOff(date, 1)
                realStartDate = getNDaysOff(date, max(self.__historicalTickDataLength, self.__historicalTickDataLengthCS))
            elif stock in self.__stockSetTS and stock not in self.__stockSetCS:
                updateDate = date if "Tick" in self.__dataType else getNDaysOff(date, 1)
                realStartDate = getNDaysOff(date, self.__historicalTickDataLength)
            elif stock not in self.__stockSetTS and stock in self.__stockSetCS:
                updateDate = date if "Tick" in self.__dataTypeCS else getNDaysOff(date, 1)
                realStartDate = getNDaysOff(date, self.__historicalTickDataLengthCS)
            else:
                raise Exception(f"Unexpected case when loading tick data first time: {stock}")

            if realStartDate > updateDate:
                continue

            data1, data2, earlyDataMorning, earlyDataAfternoon = self.__preprocessTickData(stock, updateDate, updateDate)

            previousData1 = self.__tickDataDict1[stock]
            mask = previousData1[:, self.__tickColumnIndexDict1["Date"]] >= realStartDate
            previousData1 = previousData1[mask, :]
            self.__tickDataDict1[stock] = np.concatenate((previousData1, data1.values), axis=0)

            previousData2 = self.__tickDataDict2[stock]
            previousData2 = previousData2[mask, :]
            self.__tickDataDict2[stock] = np.concatenate((previousData2, data2.values), axis=0)

            self.__earlyDataMorningDict[stock][date] = earlyDataMorning[date]
            self.__earlyDataAfternoonDict[stock][date] = earlyDataAfternoon[date]

    def __updateIndexTickData(self, date):
        updateDate = date if "Tick" in self.__dataTypeIndex else getNDaysOff(date, 1)
        realStartDate = getNDaysOff(date, self.__historicalTickDataLengthIndex)

        if realStartDate > updateDate:
            return

        for index in self.__indexSet:
            data = self.__preprocessIndexTickData(index, updateDate, updateDate)

            previousData = self.__tickDataDict1[index]
            mask = previousData[:, INDEX_TICK_COLUMN_INDEX_DICT["Date"]] >= realStartDate
            previousData = previousData[mask, :]

            self.__tickDataDict1[index] = np.concatenate((previousData, data.values), axis=0)

    def __updateUATickData(self, date):
        updateDate = date if "Tick" in self.__dataTypeUA else getNDaysOff(date, 1)
        realStartDate = getNDaysOff(date, self.__historicalTickDataLengthUA)

        if realStartDate > updateDate:
            return

        for ua in self.__UASet:
            data1, data2 = self.__preprocessUATickData(ua, updateDate, updateDate)

            previousData1 = self.__tickDataDict1[ua]
            mask = previousData1[:, self.__tickColumnIndexDict1UA["Date"]] >= realStartDate
            previousData1 = previousData1[mask, :]
            self.__tickDataDict1[ua] = np.concatenate((previousData1, data1.values), axis=0)

            previousData2 = self.__tickDataDict2[ua]
            previousData2 = previousData2[mask, :]
            self.__tickDataDict2[ua] = np.concatenate((previousData2, data2.values), axis=0)

            if self.__splitAdjustedNeeded:
                data1, data2 = self.__preprocessUATickData(ua, updateDate, updateDate)

                data1.loc[:, self.__PRICE_COLUMN_NAMES_1] = data1.loc[:, self.__PRICE_COLUMN_NAMES_1].multiply(
                    self.__adjFactorDict[ua].reindex(data1.index),
                    axis=0
                )

                previousData1 = self.__tickDataDict1SplitAdjusted[ua]
                previousData1 = previousData1[mask, :]
                self.__tickDataDict1SplitAdjusted[ua] = np.concatenate((previousData1, data1.values), axis=0)

                for priceColumnName in self.__PRICE_COLUMN_NAMES_2:
                    for priceData in data2.loc[[date], priceColumnName]:
                        if priceData is not None:
                            priceData *= self.__adjFactorDict[ua][date]
                for transactionData in data2.loc[[date], self.__PRICE_COLUMN_NAME_3]:
                    if transactionData is not None:
                        transactionData[:, self.__priceColumnIndex3UA] *= self.__adjFactorDict[ua][date]
                for cancellationData in data2.loc[[date], self.__PRICE_COLUMN_NAME_3_3]:
                    if cancellationData is not None:
                        cancellationData[:, self.__priceColumnIndex3UA] *= self.__adjFactorDict[ua][date]
                for orderData in data2.loc[[date], self.__PRICE_COLUMN_NAME_3_2]:
                    if orderData is not None:
                        orderData[:, self.__priceColumnIndex3_2UA] *= self.__adjFactorDict[ua][date]

                previousData2 = self.__tickDataDict2SplitAdjusted[ua]
                previousData2 = previousData2[mask, :]
                self.__tickDataDict2SplitAdjusted[ua] = np.concatenate((previousData2, data2.values), axis=0)

    def __preprocessMinuteData(self, stock, startDate, endDate):
        data = self.__HFDataDict[stock].get_minute_data(startDate, endDate).astype(np.float64)
        data = data.drop(self.__invalidTradingDayDict[stock], errors="ignore")

        tradingDayList = getTradingDay(startDate, endDate)
        fillData = self.__getFillMinuteData(self.__invalidTradingDayDict[stock].intersection(tradingDayList),
                                            self.__minuteColumnNames)
        data = pd.concat([data, fillData], axis=0)

        data = data.loc[:, self.__minuteColumnNames].astype(np.float64)

        data["Timestamp"] += 60

        data.index.name = None
        data = data.sort_values("Timestamp")

        return data

    def __preprocessTickData(self, stock, startDate, endDate):
        transaction = self.__preprocessTransactionData(stock, startDate, endDate, False)
        order = self.__preprocessOrderData(stock, startDate, endDate, False)

        originalData = self.__HFDataDict[stock].get_tick_data(startDate, endDate)
        originalData["IsL2P"] = False
        originalData["TargetTimestamp"] = originalData["Timestamp"]
        originalData = originalData.astype({columnName: np.float64 for columnName in self.__tickColumnNames1})
        originalData = originalData.drop(self.__invalidTradingDayDict[stock], errors="ignore")
        self.__checkTransactionAndOrder(stock, originalData, transaction, order, self.__transactionColumnIndexDict, self.__orderColumnIndexDict)
        self.__appendTransactionAndOrder(originalData, transaction, order, self.__transactionColumnIndexDict, self.__orderColumnIndexDict)
        earlyDataMorning = self.__getEarlyDataMorning(originalData, transaction, order, self.__transactionColumnIndexDict, self.__orderColumnIndexDict)
        earlyDataAfternoon = self.__getEarlyDataAfternoon(originalData, transaction, order, self.__transactionColumnIndexDict, self.__orderColumnIndexDict)

        tradingDayList = getTradingDay(startDate, endDate)
        fillData = self.__getFillTickData(self.__invalidTradingDayDict[stock].intersection(tradingDayList),
                                          self.__tickColumnNames1, self.__tickColumnNames2)
        fillData["IsL2P"] = False
        fillData["TargetTimestamp"] = fillData["Timestamp"]
        originalData1 = pd.concat([originalData[self.__tickColumnNames1], fillData[self.__tickColumnNames1]], axis=0)
        originalData2 = pd.concat([originalData[self.__tickColumnNames2], fillData[self.__tickColumnNames2]], axis=0)
        originalData = pd.concat([originalData1, originalData2], axis=1)

        originalData.index.name = None

        if stock in self.__stockSetL2P:
            transaction = self.__preprocessTransactionData(stock, startDate, endDate, True)
            order = self.__preprocessOrderData(stock, startDate, endDate, True)

            l2pData = self.__HFDataDictForL2P[stock].get_tick_data(startDate, endDate)
            l2pData["TargetTimestamp"] = l2pData["Timestamp"]
            l2pData["TargetTimestamp"] -= 3
            l2pData["IsL2P"] = True
            l2pData = l2pData.astype({columnName: np.float64 for columnName in self.__tickColumnNames1})
            l2pData = l2pData[l2pData["IsMock"] == 0]
            l2pData = l2pData.drop(self.__invalidTradingDayDict[stock], errors="ignore")

            self.__checkTransactionAndOrder(stock, l2pData, transaction, order, self.__transactionColumnIndexDict, self.__orderColumnIndexDict)
            self.__appendTransactionAndOrder(l2pData, transaction, order, self.__transactionColumnIndexDict, self.__orderColumnIndexDict)

            l2pData.index.name = None
        else:
            l2pData = pd.DataFrame(columns=self.__tickColumnNames1 + self.__tickColumnNames2)

        data1 = pd.concat([originalData[self.__tickColumnNames1], l2pData[self.__tickColumnNames1]], axis=0)
        data2 = pd.concat([originalData[self.__tickColumnNames2], l2pData[self.__tickColumnNames2]], axis=0)
        data = pd.concat([data1, data2], axis=1).sort_values(["TargetTimestamp", "IsL2P"], ascending=[True, True])

        return data[self.__tickColumnNames1].astype(np.float64), data[self.__tickColumnNames2], earlyDataMorning, earlyDataAfternoon

    def __preprocessTransactionData(self, stock, startDate, endDate, isL2P):
        if isL2P:
            data = self.__HFDataDictForL2P[stock].get_transaction_data(startDate, endDate).astype(
                {columnName: np.float64 for columnName in self.__transactionColumnNames}
            )
        else:
            data = self.__HFDataDict[stock].get_transaction_data(startDate, endDate).astype(
                {columnName: np.float64 for columnName in self.__transactionColumnNames}
            )
        data = data.drop(self.__invalidTradingDayDict[stock], errors="ignore")

        return data[self.__transactionColumnNames].values

    def __preprocessOrderData(self, stock, startDate, endDate, isL2P):
        if isL2P:
            data = self.__HFDataDictForL2P[stock].get_order_data(startDate, endDate).astype(
                {columnName: np.float64 for columnName in self.__orderColumnNames}
            )
        else:
            data = self.__HFDataDict[stock].get_order_data(startDate, endDate).astype(
                {columnName: np.float64 for columnName in self.__orderColumnNames}
            )
        data = data.drop(self.__invalidTradingDayDict[stock], errors="ignore")

        return data[self.__orderColumnNames].values

    @staticmethod
    def __checkTransactionAndOrder(stock, tick, transaction, order, transactionColumnIndexDict, orderColumnIndexDict):
        tickDates = tick["Date"].unique()

        dates, counts = np.unique(transaction[:, transactionColumnIndexDict["Date"]], return_counts=True)
        counts = pd.Series(counts, index=dates).reindex(tickDates).fillna(0)
        if (tick["TEIndex"] - counts > 0).any():
            missingDates = tick.loc[tick["TEIndex"] - counts > 0, "Date"].unique().tolist()
            raise Exception(f"{stock}'s transactions missing on {missingDates}")

        dates, counts = np.unique(order[:, orderColumnIndexDict["Date"]], return_counts=True)
        counts = pd.Series(counts, index=dates).reindex(tickDates).fillna(0)
        if (tick["OEIndex"] - counts > 0).any():
            missingDates = tick.loc[tick["OEIndex"] - counts > 0, "Date"].unique().tolist()
            raise Exception(f"{stock}'s orders missing on {missingDates}")

    @staticmethod
    def __appendTransactionAndOrder(tick, transaction, order, transactionColumnIndexDict, orderColumnIndexDict):
        tickDates = tick["Date"].unique()

        dates, counts = np.unique(transaction[:, transactionColumnIndexDict["Date"]], return_counts=True)
        indices = np.hstack((0, np.cumsum(counts)[:-1])) if counts.shape[0] > 0 else counts
        indices = pd.Series(indices, index=dates).reindex(tickDates).fillna(method="ffill").fillna(0)
        tsIndex = (tick["TSIndex"] + indices).values
        teIndex = (tick["TEIndex"] + indices).values
        transactionList = []
        cancellationList = []
        for i in range(tick.shape[0]):
            transactionAllTmp = transaction[tsIndex[i]:teIndex[i], :]
            transactionTmp = transactionAllTmp[transactionAllTmp[:, transactionColumnIndexDict["TradeType"]] == 0, :]
            cancellationTmp = transactionAllTmp[transactionAllTmp[:, transactionColumnIndexDict["TradeType"]] == 1, :]
            if transactionTmp.shape[0] == 0:
                transactionTmp = None
            if cancellationTmp.shape[0] == 0:
                cancellationTmp = None
            transactionList.append(transactionTmp)
            cancellationList.append(cancellationTmp)
        tick["Transactions"] = transactionList
        tick["Cancellations"] = cancellationList

        dates, counts = np.unique(order[:, orderColumnIndexDict["Date"]], return_counts=True)
        indices = np.hstack((0, np.cumsum(counts)[:-1])) if counts.shape[0] > 0 else counts
        indices = pd.Series(indices, index=dates).reindex(tickDates).fillna(method="ffill").fillna(0)
        osIndex = (tick["OSIndex"] + indices).values
        oeIndex = (tick["OEIndex"] + indices).values
        tick["Orders"] = [order[osIndex[i]:oeIndex[i], :] if oeIndex[i] > osIndex[i] else None for i in range(tick.shape[0])]

    @staticmethod
    def __getEarlyDataMorning(tick, transaction, order, transactionColumnIndexDict, orderColumnIndexDict):
        earlyData = {date: {"Transactions": None, "Cancellations": None, "Orders": None} for date in tick["Date"].unique()}

        tick = tick[(tick["Time"] >= 93015000) & (tick["Time"] <= 120000000)]
        tick = tick.drop_duplicates("Date")
        tickDates = tick["Date"].unique()

        dates, counts = np.unique(transaction[:, transactionColumnIndexDict["Date"]], return_counts=True)
        indices = np.hstack((0, np.cumsum(counts)[:-1])) if counts.shape[0] > 0 else counts
        indices = pd.Series(indices, index=dates).reindex(tickDates).fillna(method="ffill").fillna(0)
        tsIndex = tick["TSIndex"] + indices
        for date in tickDates:
            transactionAllTmp = transaction[int(indices[date]):int(tsIndex[date]), :]
            transactionTmp = transactionAllTmp[transactionAllTmp[:, transactionColumnIndexDict["TradeType"]] == 0, :]
            cancellationTmp = transactionAllTmp[transactionAllTmp[:, transactionColumnIndexDict["TradeType"]] == 1, :]
            if transactionTmp.shape[0] > 0:
                earlyData[date]["Transactions"] = transactionTmp.copy()
            if cancellationTmp.shape[0] > 0:
                earlyData[date]["Cancellations"] = cancellationTmp.copy()

        dates, counts = np.unique(order[:, orderColumnIndexDict["Date"]], return_counts=True)
        indices = np.hstack((0, np.cumsum(counts)[:-1])) if counts.shape[0] > 0 else counts
        indices = pd.Series(indices, index=dates).reindex(tickDates).fillna(method="ffill").fillna(0)
        osIndex = tick["OSIndex"] + indices
        for date in tickDates:
            orderTmp = order[int(indices[date]):int(osIndex[date]), :]
            if orderTmp.shape[0] > 0:
                earlyData[date]["Orders"] = orderTmp.copy()

        return earlyData

    @staticmethod
    def __getEarlyDataAfternoon(tick, transaction, order, transactionColumnIndexDict, orderColumnIndexDict):
        earlyData = {date: {"Transactions": None, "Cancellations": None, "Orders": None} for date in tick["Date"].unique()}

        tickMorning = tick[(tick["Time"] >= 93015000) & (tick["Time"] <= 120000000)]
        tickAfternoon = tick[tick["Time"] > 120000000]

        tickMorning = tickMorning.drop_duplicates("Date", keep="last")
        tickAfternoon = tickAfternoon.drop_duplicates("Date")

        tickMorning = tickMorning.reindex(tickAfternoon.index).fillna(0)

        tickDates = tickAfternoon["Date"].unique()

        dates, counts = np.unique(transaction[:, transactionColumnIndexDict["Date"]], return_counts=True)
        indices = np.hstack((0, np.cumsum(counts)[:-1])) if counts.shape[0] > 0 else counts
        indices = pd.Series(indices, index=dates).reindex(tickDates).fillna(method="ffill").fillna(0)
        tsIndex = tickMorning["TEIndex"] + indices
        teIndex = tickAfternoon["TSIndex"] + indices
        for date in tickDates:
            transactionAllTmp = transaction[int(tsIndex[date]):int(teIndex[date]), :]
            transactionTmp = transactionAllTmp[transactionAllTmp[:, transactionColumnIndexDict["TradeType"]] == 0, :]
            cancellationTmp = transactionAllTmp[transactionAllTmp[:, transactionColumnIndexDict["TradeType"]] == 1, :]
            earlyData[date]["Transactions"] = None if transactionTmp.shape[0] == 0 else transactionTmp.copy()
            earlyData[date]["Cancellations"] = None if cancellationTmp.shape[0] == 0 else cancellationTmp.copy()

        dates, counts = np.unique(order[:, orderColumnIndexDict["Date"]], return_counts=True)
        indices = np.hstack((0, np.cumsum(counts)[:-1])) if counts.shape[0] > 0 else counts
        indices = pd.Series(indices, index=dates).reindex(tickDates).fillna(method="ffill").fillna(0)
        osIndex = tickMorning["OEIndex"] + indices
        oeIndex = tickAfternoon["OSIndex"] + indices
        for date in tickDates:
            orderTmp = order[int(osIndex[date]):int(oeIndex[date]), :]
            earlyData[date]["Orders"] = None if orderTmp.shape[0] == 0 else orderTmp.copy()

        return earlyData

    def __preprocessIndexDailyData(self, stock, startDate, endDate):
        data = self.__HFDataDictForIndex[stock].get_daily_data(startDate, endDate)
        data = data.loc[:, INDEX_DAILY_COLUMN_NAMES].astype(np.float64)

        data.index.name = None
        data = data.sort_values("Date")

        return data

    def __preprocessIndexMinuteData(self, stock, startDate, endDate):
        data = self.__HFDataDictForIndex[stock].get_minute_data(startDate, endDate)
        data = data.loc[:, INDEX_MINUTE_COLUMN_NAMES].astype(np.float64)

        data["Timestamp"] += 60

        data.index.name = None
        data = data.sort_values("Timestamp")

        return data

    def __preprocessIndexTickData(self, stock, startDate, endDate):
        data = self.__HFDataDictForIndex[stock].get_tick_data(startDate, endDate)
        data = data.loc[:, INDEX_TICK_COLUMN_NAMES].astype(np.float64)

        data.index.name = None
        data = data.sort_values("Timestamp")

        return data

    def __preprocessUAMinuteData(self, stock, startDate, endDate):
        data = self.__HFDataDictForUA[stock].get_minute_data(startDate, endDate).astype(np.float64)
        data = data.drop(self.__invalidTradingDayDictUA[stock], errors="ignore")

        tradingDayList = getTradingDay(startDate, endDate)
        fillData = self.__getFillMinuteData(self.__invalidTradingDayDictUA[stock].intersection(tradingDayList),
                                            self.__minuteColumnNamesUA)
        data = pd.concat([data, fillData], axis=0)

        data = data.loc[:, self.__minuteColumnNamesUA].astype(np.float64)

        data["Timestamp"] += 60

        data.index.name = None
        data = data.sort_values("Timestamp")

        return data

    def __preprocessUATickData(self, stock, startDate, endDate):
        data = self.__HFDataDictForUA[stock].get_tick_data(startDate, endDate).astype(
            {columnName: np.float64 for columnName in self.__tickColumnNames1UA}
        )
        data = data.drop(self.__invalidTradingDayDictUA[stock], errors="ignore")

        transaction = self.__preprocessTransactionDataUA(stock, startDate, endDate)
        order = self.__preprocessOrderDataUA(stock, startDate, endDate)
        self.__checkTransactionAndOrder(stock, data, transaction, order, self.__transactionColumnIndexDictUA, self.__orderColumnIndexDictUA)
        self.__appendTransactionAndOrder(data, transaction, order, self.__transactionColumnIndexDictUA, self.__orderColumnIndexDictUA)

        tradingDayList = getTradingDay(startDate, endDate)
        fillData = self.__getFillTickData(self.__invalidTradingDayDictUA[stock].intersection(tradingDayList),
                                          self.__tickColumnNames1UA, self.__tickColumnNames2UA)
        data1 = pd.concat([data[self.__tickColumnNames1UA], fillData[self.__tickColumnNames1UA]], axis=0)
        data2 = pd.concat([data[self.__tickColumnNames2UA], fillData[self.__tickColumnNames2UA]], axis=0)
        data = pd.concat([data1, data2], axis=1)

        data.index.name = None
        data = data.sort_values("Timestamp")

        return data[self.__tickColumnNames1UA].astype(np.float64), data[self.__tickColumnNames2UA]

    def __preprocessTransactionDataUA(self, stock, startDate, endDate):
        data = self.__HFDataDictForUA[stock].get_transaction_data(startDate, endDate).astype(
            {columnName: np.float64 for columnName in self.__transactionColumnNamesUA}
        )
        data = data.drop(self.__invalidTradingDayDictUA[stock], errors="ignore")

        return data[self.__transactionColumnNamesUA].values

    def __preprocessOrderDataUA(self, stock, startDate, endDate):
        if stock.endswith("SH"):
            return np.zeros(shape=(0, len(self.__orderColumnNamesUA)))

        data = self.__HFDataDictForUA[stock].get_order_data(startDate, endDate).astype(
            {columnName: np.float64 for columnName in self.__orderColumnNamesUA}
        )
        data = data.drop(self.__invalidTradingDayDictUA[stock], errors="ignore")

        return data[self.__orderColumnNamesUA].values

    @staticmethod
    def __getFillMinuteData(invalidTradingDaySet, minuteColumnNames):
        invalidTradingDayList = list(invalidTradingDaySet)
        invalidTradingDayListStr = list(map(str, invalidTradingDayList))

        startDatetimeList = [dt.datetime.strptime(dateStr + "0930", "%Y%m%d%H%M")
                             for dateStr in invalidTradingDayListStr]
        datetimeList = []
        for startDatetime in startDatetimeList:
            datetimeList.extend(
                [startDatetime + dt.timedelta(minutes=i) for i in range(120)]
                + [startDatetime + dt.timedelta(minutes=210) + dt.timedelta(minutes=i) for i in range(120)]
            )

        dateList = np.repeat(invalidTradingDayList, 240)
        timeList = [int(v.strftime("%H%M%S%f")[:-3]) for v in datetimeList]
        timestampList = [v.timestamp() for v in datetimeList]

        fillMinuteData = pd.DataFrame(index=dateList, columns=minuteColumnNames)
        fillMinuteData["Date"] = dateList
        fillMinuteData["Time"] = timeList
        fillMinuteData["Timestamp"] = timestampList

        return fillMinuteData

    @staticmethod
    def __getFillTickData(invalidTradingDaySet, tickColumnNames1, tickColumnNames2):
        invalidTradingDayList = list(invalidTradingDaySet)
        invalidTradingDayListStr = list(map(str, invalidTradingDayList))

        startDatetimeList = [dt.datetime.strptime(dateStr + "093012", "%Y%m%d%H%M%S")
                             for dateStr in invalidTradingDayListStr]
        datetimeList = []
        for startDatetime in startDatetimeList:
            datetimeList.extend(
                [startDatetime + dt.timedelta(seconds=3 * i) for i in range(2396)]
                + [startDatetime + dt.timedelta(seconds=12603) + dt.timedelta(seconds=3 * i) for i in range(2335)]
            )

        dateList = np.repeat(invalidTradingDayList, 4731)
        timeList = [int(v.strftime("%H%M%S%f")[:-3]) for v in datetimeList]
        timestampList = [v.timestamp() for v in datetimeList]

        fillTickData = pd.DataFrame(index=dateList, columns=tickColumnNames1 + tickColumnNames2)
        fillTickData["Date"] = dateList
        fillTickData["Time"] = timeList
        fillTickData["Timestamp"] = timestampList
        fillTickData.loc[:, tickColumnNames2] = None

        return fillTickData

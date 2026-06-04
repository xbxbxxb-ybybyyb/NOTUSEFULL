import gc
import datetime as dt
import numpy as np
import pandas as pd
from Constants.INDEX_LIST import INDEX_LIST
from System.TradingDay import getTradingDay, getNDaysOff
from System.COLUMN_CONFIG import (TICK_COLUMN_NAMES1, TICK_COLUMN_NAMES2, MINUTE_COLUMN_NAMES, DAILY_COLUMN_NAMES,
                                  TICK_COLUMN_INDEX_DICT1, TRANSACTION_COLUMN_INDEX_DICT)
from System.COLUMN_CONFIG import (INDEX_TICK_COLUMN_NAMES, INDEX_MINUTE_COLUMN_NAMES, INDEX_DAILY_COLUMN_NAMES,
                                  INDEX_TICK_COLUMN_INDEX_DICT)
from IndexNonFactor.Config import INF_NONFACTOR_VALUE_COLUMNS
from HFDataLoader.HFData import HFData


class StockDataManagerAfternoon:
    """
    Load data via HFData dynamically
    """

    def __init__(self, libraryName, infLibrary, assetType, underlyingAssetType, startDate, endDate, stockSetTS,
                 stockSetAll, configAnalyzer):
        self.__PRICE_COLUMN_NAMES_1 = ["PreviousClose", "LastPrice", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice",
                                       "MinPrice"]
        self.__PRICE_COLUMN_NAMES_2 = ["BidPrice", "AskPrice"]
        self.__PRICE_COLUMN_NAME_3 = "Transactions"
        self.__PRICE_COLUMN_NAMES_4 = ["OpenPrice", "HighPrice", "LowPrice", "ClosePrice"]
        self.__PRICE_COLUMN_NAMES_5 = ["PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "ClosePrice"]

        self.__library = libraryName
        self.__infLibrary = infLibrary
        self.__assetType = assetType
        self.__underlyingAssetType = underlyingAssetType
        self.__startDate = startDate
        self.__endDate = endDate
        self.__stockSetTS = stockSetTS
        self.__stockSetAll = stockSetAll
        self.__configAnalyzer = configAnalyzer

        self.__tickColumnNames1 = TICK_COLUMN_NAMES1
        self.__tickColumnNames2 = TICK_COLUMN_NAMES2
        self.__minuteColumnNames = MINUTE_COLUMN_NAMES
        self.__dailyColumnNames = DAILY_COLUMN_NAMES
        self.__tickColumnIndexDict1 = TICK_COLUMN_INDEX_DICT1
        self.__transactionColumnIndexDict = TRANSACTION_COLUMN_INDEX_DICT
        self.__priceColumnIndex3 = TRANSACTION_COLUMN_INDEX_DICT["Price"]

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
        self.__historicalTickDataLengthINF = dataRequirements["maxTickLengthINF"]
        self.__dataType = dataRequirements["dataType"]
        self.__dataTypeCS = dataRequirements["dataTypeCS"]
        self.__dataTypeIndex = dataRequirements["dataTypeIndex"]
        self.__indexGroup = dataRequirements["indexGroup"]
        self.__infGroup = dataRequirements["infGroup"]
        self.__splitAdjustedNeeded = dataRequirements["splitAdjustedNeeded"]

        self.__invalidTradingDayDict = {}
        self.__adjFactorDict = {}
        self.__tickDataDict1 = {}
        self.__tickDataDict2 = {}
        self.__tickDataDict3 = {}
        self.__minuteDataDict = {}
        self.__dailyDataDict = {}
        self.__tickDataDict1SplitAdjusted = {}
        self.__tickDataDict2SplitAdjusted = {}
        self.__minuteDataDictSplitAdjusted = {}
        self.__dailyDataDictSplitAdjusted = {}

        self.__HFDataDict = {stock: HFData(libraryName, stock) for stock in stockSetAll}

        self.__indexSet = set()
        for index in self.__indexGroup:
            if index in INDEX_LIST:
                self.__indexSet.add(index)
            else:
                for date in getTradingDay(startDate, endDate):
                    for stock in self.__stockSetTS:
                        targetIndustry = configAnalyzer.getIndustryCode(stock, date, index)
                        if targetIndustry is not None:
                            self.__indexSet.add(targetIndustry)
        self.__HFDataDictForIndex = {index: HFData(libraryName, index) for index in self.__indexSet}

        self.__infGroup = {k + "_INF": v for k, v in self.__infGroup.items()}
        self.__infColumnDict1 = {}
        self.__infColumnDict2 = {}
        for inf, columnNames in self.__infGroup.items():
            self.__infColumnDict1[inf] = (
                    [columnName for columnName in columnNames if columnName in INF_NONFACTOR_VALUE_COLUMNS]
                    + ["Timestamp", "Date", "Time", "IsMock"]
            )
            self.__infColumnDict2[inf] = [
                columnName for columnName in columnNames if columnName not in INF_NONFACTOR_VALUE_COLUMNS
            ]
        self.__infIndexColumnDict1 = {inf: {k: v for v, k in enumerate(columnNames)}
                                      for inf, columnNames in self.__infColumnDict1.items()}
        self.__infIndexColumnDict2 = {inf: {k: v for v, k in enumerate(columnNames)}
                                      for inf, columnNames in self.__infColumnDict2.items()}
        self.__infSet = set()
        self.__infMap = {}
        for inf in self.__infGroup:
            if inf.rstrip("_INF") in INDEX_LIST:
                self.__infSet.add(inf)
                self.__infMap[inf] = inf
            else:
                for date in getTradingDay(getNDaysOff(startDate, self.__historicalTickDataLengthINF), endDate):
                    for stock in self.__stockSetTS:
                        targetIndustry = configAnalyzer.getIndustryCode(stock, date, inf.rstrip("_INF"))
                        if targetIndustry is not None:
                            targetIndustry += "_INF"
                            self.__infSet.add(targetIndustry)
                            self.__infMap[targetIndustry] = inf
        self.__HFDataDictForINF = {inf: HFData(libraryName, inf.rstrip("_INF"), inf_lib=infLibrary)
                                   for inf in self.__infSet}
        self.__infStockListDict = {}
        self.__infSpecialGroup = None

    def loadData(self):
        """
        For Calculation Scheduler & SparkLauncher
        """
        self.__invalidTradingDayDict = {}

        self.__loadDailyData()
        self.__loadMinuteData()
        self.__loadTickDataFirstTime()

        self.__loadIndexDataFirstTime()
        self.__loadINFDataFirstTime()

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

    def getExtraTickData(self):
        """
        For DataBroadcaster
        """
        return self.__tickDataDict3

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

    def getINFSpecialGroup(self):
        """
        For DataBroadcaster
        """
        return self.__infSpecialGroup

    def getINFSet(self):
        """
        For DataBroadcaster
        """
        return self.__infSet

    def getINFMap(self):
        """
        For DataBroadcaster
        """
        return self.__infMap

    def getINFColumnIndexDict1(self):
        """
        For DataBroadcaster
        """
        return self.__infIndexColumnDict1

    def getINFColumnIndexDict2(self):
        """
        For DataBroadcaster
        """
        return self.__infIndexColumnDict2

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
            self.__historicalMinuteDataLength,
            self.__historicalMinuteDataLengthCS,
            self.__historicalMinuteDataLengthIndex,
            self.__historicalDailyDataLength,
            self.__historicalDailyDataLengthCS,
            self.__historicalDailyDataLengthIndex,
            self.__historicalTickDataLengthINF,
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

    def getINFStockListDict(self, stock, date):
        """
        For FactorManager
        """
        return self.__infStockListDict[stock][date]

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
        self.__updateINFTickData(date)

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
        allTradingDaySet = set(getTradingDay(startDate, self.__endDate))

        for stock in self.__stockSetAll:
            data = self.__HFDataDict[stock].get_daily_data(startDate, self.__endDate).astype(np.float64)

            data = data.reindex(allTradingDaySet).sort_index()
            data["Date"] = data.index.tolist()

            data.index.name = None
            data = data.sort_values("Date")
            data = data[self.__dailyColumnNames]

            invalidTradingDaySet = set(data[data["TradeStatus"] != 1].index)

            self.__invalidTradingDayDict[stock] = invalidTradingDaySet
            self.__dailyDataDict[stock] = data.astype(np.float64)
            if self.__splitAdjustedNeeded:
                self.__adjFactorDict[stock] = data["AdjFactor"].astype(np.float64)
                self.__dailyDataDictSplitAdjusted[stock] = data.astype(np.float64)

    def __loadMinuteData(self):
        for stock in self.__stockSetAll:
            if stock in self.__stockSetTS:
                historicalMinuteDataLengthAll = max(self.__historicalMinuteDataLength,
                                                    self.__historicalMinuteDataLengthCS)
                if "Minute" in self.__dataTypeCS or "Minute" in self.__dataType:
                    startDate = getNDaysOff(self.__startDate, historicalMinuteDataLengthAll)
                    endDate = self.__endDate
                    self.__minuteDataDict[stock] = self.__preprocessMinuteData(stock, startDate, endDate)
                else:
                    if historicalMinuteDataLengthAll > 0:
                        startDate = getNDaysOff(self.__startDate, historicalMinuteDataLengthAll)
                        endDate = getNDaysOff(self.__endDate, 1)
                        self.__minuteDataDict[stock] = self.__preprocessMinuteData(stock, startDate, endDate)
                    else:
                        self.__minuteDataDict[stock] = pd.DataFrame(columns=self.__minuteColumnNames)
            else:
                if "Minute" in self.__dataTypeCS:
                    startDate = getNDaysOff(self.__startDate, self.__historicalMinuteDataLengthCS)
                    endDate = self.__endDate
                    self.__minuteDataDict[stock] = self.__preprocessMinuteData(stock, startDate, endDate)
                else:
                    if self.__historicalMinuteDataLengthCS > 0:
                        startDate = getNDaysOff(self.__startDate, self.__historicalMinuteDataLengthCS)
                        endDate = getNDaysOff(self.__endDate, 1)
                        self.__minuteDataDict[stock] = self.__preprocessMinuteData(stock, startDate, endDate)
                    else:
                        self.__minuteDataDict[stock] = pd.DataFrame(columns=self.__minuteColumnNames)

            if self.__splitAdjustedNeeded:
                self.__minuteDataDictSplitAdjusted[stock] = self.__minuteDataDict[stock].copy()

    def __loadTickDataFirstTime(self):
        for stock in self.__stockSetAll:
            if stock in self.__stockSetTS:
                startDate = getNDaysOff(
                    self.__startDate,
                    max(self.__historicalTickDataLength, self.__historicalTickDataLengthCS)
                )
                endDate = self.__startDate
            else:
                if "Tick" in self.__dataTypeCS:
                    startDate = getNDaysOff(self.__startDate, self.__historicalTickDataLengthCS)
                    endDate = self.__startDate
                else:
                    if self.__historicalTickDataLengthCS > 0:
                        startDate = getNDaysOff(self.__startDate, self.__historicalTickDataLengthCS)
                        endDate = getNDaysOff(self.__startDate, 1)
                    else:
                        self.__tickDataDict1[stock] = pd.DataFrame(columns=self.__tickColumnNames1, dtype=np.float64)
                        self.__tickDataDict2[stock] = pd.DataFrame(columns=self.__tickColumnNames2)

                        if self.__splitAdjustedNeeded:
                            self.__tickDataDict1SplitAdjusted[stock] = pd.DataFrame(
                                columns=self.__tickColumnNames1, dtype=np.float64
                            )
                            self.__tickDataDict2SplitAdjusted[stock] = pd.DataFrame(columns=self.__tickColumnNames2)

                        continue

            self.__tickDataDict1[stock], self.__tickDataDict2[stock] = self.__preprocessTickData(
                stock, startDate, endDate
            )

            if self.__splitAdjustedNeeded:
                (self.__tickDataDict1SplitAdjusted[stock],
                 self.__tickDataDict2SplitAdjusted[stock]) = self.__preprocessTickData(
                    stock, startDate, endDate
                )

    def __loadIndexDataFirstTime(self):
        for index in self.__indexSet:
            if self.__historicalDailyDataLengthIndex > 0:
                startDate = getNDaysOff(self.__startDate, self.__historicalDailyDataLengthIndex)
                endDate = self.__endDate
                self.__dailyDataDict[index] = self.__preprocessIndexDailyData(index, startDate, endDate)
            else:
                self.__dailyDataDict[index] = pd.DataFrame(columns=INDEX_TICK_COLUMN_NAMES, dtype=np.float64)

            if self.__historicalMinuteDataLengthIndex > 0:
                startDate = getNDaysOff(self.__startDate, self.__historicalMinuteDataLengthIndex)
                if "Minute" in self.__dataTypeIndex:
                    endDate = self.__endDate
                else:
                    endDate = getNDaysOff(self.__endDate, 1)
                self.__minuteDataDict[index] = self.__preprocessIndexMinuteData(index, startDate, endDate)
            else:
                if "Minute" in self.__dataTypeIndex:
                    startDate = self.__startDate
                    endDate = self.__endDate
                    self.__minuteDataDict[index] = self.__preprocessIndexMinuteData(index, startDate, endDate)
                else:
                    self.__minuteDataDict[index] = pd.DataFrame(columns=INDEX_MINUTE_COLUMN_NAMES, dtype=np.float64)

            if self.__historicalTickDataLengthIndex > 0:
                startDate = getNDaysOff(self.__startDate, self.__historicalTickDataLengthIndex)
                if "Tick" in self.__dataTypeIndex:
                    endDate = self.__startDate
                else:
                    endDate = getNDaysOff(self.__startDate, 1)
                self.__tickDataDict1[index] = self.__preprocessIndexTickData(index, startDate, endDate)
            else:
                if "Tick" in self.__dataTypeIndex:
                    startDate = self.__startDate
                    endDate = self.__startDate
                    self.__tickDataDict1[index] = self.__preprocessIndexTickData(index, startDate, endDate)
                else:
                    self.__tickDataDict1[index] = pd.DataFrame(columns=INDEX_TICK_COLUMN_NAMES, dtype=np.float64)

    def __loadINFDataFirstTime(self):
        if self.__historicalTickDataLengthINF > 0:
            startDate = getNDaysOff(self.__startDate, self.__historicalTickDataLengthINF)
            endDate = self.__startDate
        else:
            startDate = self.__startDate
            endDate = self.__startDate

        for inf in self.__infSet:
            infColumnNames1 = self.__infColumnDict1[self.__infMap[inf]]
            infColumnNames2 = self.__infColumnDict2[self.__infMap[inf]]

            self.__dailyDataDict[inf] = pd.DataFrame(columns=infColumnNames1, dtype=np.float64)
            self.__minuteDataDict[inf] = pd.DataFrame(columns=infColumnNames1, dtype=np.float64)

            self.__tickDataDict1[inf], self.__tickDataDict2[inf] = self.__preprocessINFTickData(
                inf, startDate, endDate, infColumnNames1, infColumnNames2
            )

        self.__infSpecialGroup = set()
        for inf in self.__infGroup:
            for stock in self.__stockSetTS:
                targetIndustryList = []
                for date in getTradingDay(startDate, endDate):
                    targetIndustry = self.__configAnalyzer.getIndustryCode(stock, date, inf.rstrip("_INF"))
                    targetIndustry = targetIndustry if targetIndustry is None else targetIndustry + "_INF"
                    targetIndustryList.append(targetIndustry)

                if sum([targetIndustry is not None for targetIndustry in targetIndustryList]) == 0:
                    continue

                if len(set(targetIndustryList)) > 1:
                    tickData1List = []
                    tickData2List = []
                    for i, date in enumerate(getTradingDay(startDate, endDate)):
                        targetIndustry = targetIndustryList[i]
                        if targetIndustry is None:
                            continue

                        tickData1 = self.__tickDataDict1[targetIndustry].loc[date]
                        tickData2 = self.__tickDataDict2[targetIndustry].loc[date]
                        tickData1List.append(tickData1)
                        tickData2List.append(tickData2)
                    self.__tickDataDict1["{}_{}".format(inf, stock)] = pd.concat(tickData1List)
                    self.__tickDataDict2["{}_{}".format(inf, stock)] = pd.concat(tickData2List)
                    self.__minuteDataDict["{}_{}".format(inf, stock)] = pd.DataFrame(
                        columns=self.__infColumnDict1[inf], dtype=np.float64
                    )
                    self.__dailyDataDict["{}_{}".format(inf, stock)] = pd.DataFrame(
                        columns=self.__infColumnDict1[inf], dtype=np.float64
                    )
                    self.__infSpecialGroup.add("{}_{}".format(inf, stock))

        for inf in self.__infGroup:
            self.__tickDataDict3[inf] = {}
            infColumnNames = self.__infColumnDict2[inf]
            for stock in self.__stockSetTS:
                for date in getTradingDay(startDate, endDate):
                    targetIndustry = self.__configAnalyzer.getIndustryCode(stock, date, inf.rstrip("_INF"))
                    if targetIndustry is not None:
                        break
                else:
                    continue

                self.__tickDataDict3[inf][stock] = {}
                for infColumnName in infColumnNames:
                    infArrayList = []
                    for date in getTradingDay(startDate, endDate):
                        targetIndustry = self.__configAnalyzer.getIndustryCode(stock, date, inf.rstrip("_INF"))
                        if targetIndustry is None:
                            continue
                        targetIndustry += "_INF"

                        stockIndex = self.__infStockListDict[targetIndustry][date].index(stock)
                        infArray = np.array(self.__tickDataDict2[targetIndustry].loc[date, infColumnName].tolist())
                        infArrayList.append(infArray[:, stockIndex])

                    self.__tickDataDict3[inf][stock][infColumnName] = np.concatenate(infArrayList)

    def __loadSplitAdjustedDataFirstTime(self):
        for stock, tickData in self.__tickDataDict1SplitAdjusted.items():
            tickData.loc[:, self.__PRICE_COLUMN_NAMES_1] = tickData.loc[:, self.__PRICE_COLUMN_NAMES_1].multiply(
                self.__adjFactorDict[stock].reindex(tickData.index),
                axis=0
            )

        for stock, tickData in self.__tickDataDict2SplitAdjusted.items():
            if stock in self.__stockSetAll:
                priceColumnIndex3 = self.__priceColumnIndex3
            else:
                raise Exception("Unexpected symbol: {]".format(stock))

            for date, tickDataSingleDay in tickData.groupby(level=0):
                for priceColumnName in self.__PRICE_COLUMN_NAMES_2:
                    for priceData in tickData.loc[date, priceColumnName]:
                        if priceData is not None:
                            priceData *= self.__adjFactorDict[stock][date]
                for transactionData in tickData.loc[date, self.__PRICE_COLUMN_NAME_3]:
                    if transactionData is not None:
                        transactionData[:, priceColumnIndex3] *= self.__adjFactorDict[stock][date]

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
            if stock in self.__stockSetTS:
                startDate = date
                endDate = date
                realStartDate = getNDaysOff(
                    date,
                    max(self.__historicalTickDataLength, self.__historicalTickDataLengthCS)
                )
            else:
                if "Tick" in self.__dataTypeCS:
                    startDate = date
                    endDate = date
                    realStartDate = getNDaysOff(date, self.__historicalTickDataLengthCS)
                else:
                    if self.__historicalTickDataLengthCS > 0:
                        startDate = getNDaysOff(date, 1)
                        endDate = getNDaysOff(date, 1)
                        realStartDate = getNDaysOff(date, self.__historicalTickDataLengthCS)
                    else:
                        continue

            data1, data2 = self.__preprocessTickData(stock, startDate, endDate)

            previousData1 = self.__tickDataDict1[stock]
            mask = previousData1[:, self.__tickColumnIndexDict1["Date"]] >= realStartDate
            previousData1 = previousData1[mask, :]
            self.__tickDataDict1[stock] = np.concatenate((previousData1, data1.values), axis=0)

            previousData2 = self.__tickDataDict2[stock]
            previousData2 = previousData2[mask, :]
            self.__tickDataDict2[stock] = np.concatenate((previousData2, data2.values), axis=0)

            if self.__splitAdjustedNeeded:
                data1, data2 = self.__preprocessTickData(stock, startDate, endDate)

                data1.loc[:, self.__PRICE_COLUMN_NAMES_1] = data1.loc[:, self.__PRICE_COLUMN_NAMES_1].multiply(
                    self.__adjFactorDict[stock].reindex(data1.index),
                    axis=0
                )

                previousData1 = self.__tickDataDict1SplitAdjusted[stock]
                previousData1 = previousData1[mask, :]
                self.__tickDataDict1SplitAdjusted[stock] = np.concatenate((previousData1, data1.values), axis=0)

                for priceColumnName in self.__PRICE_COLUMN_NAMES_2:
                    for priceData in data2.loc[date, priceColumnName]:
                        if priceData is not None:
                            priceData *= self.__adjFactorDict[stock][date]
                for transactionData in data2.loc[date, self.__PRICE_COLUMN_NAME_3]:
                    if transactionData is not None:
                        transactionData[:, self.__priceColumnIndex3] *= self.__adjFactorDict[stock][date]

                previousData2 = self.__tickDataDict2SplitAdjusted[stock]
                previousData2 = previousData2[mask, :]
                self.__tickDataDict2SplitAdjusted[stock] = np.concatenate((previousData2, data2.values), axis=0)

    def __updateIndexTickData(self, date):
        if "Tick" in self.__dataTypeIndex:
            startDate = date
            endDate = date
            realStartDate = getNDaysOff(date, self.__historicalTickDataLengthIndex)
        elif self.__historicalTickDataLengthIndex > 0:
            startDate = getNDaysOff(date, 1)
            endDate = getNDaysOff(date, 1)
            realStartDate = getNDaysOff(date, self.__historicalTickDataLengthIndex)
        else:
            return

        for index in self.__indexSet:
            data = self.__preprocessIndexTickData(index, startDate, endDate)

            previousData = self.__tickDataDict1[index]
            mask = previousData[:, INDEX_TICK_COLUMN_INDEX_DICT["Date"]] >= realStartDate
            previousData = previousData[mask, :]

            self.__tickDataDict1[index] = np.concatenate((previousData, data.values), axis=0)

    def __updateINFTickData(self, date):
        startDate = date
        endDate = date
        realStartDate = getNDaysOff(date, self.__historicalTickDataLengthINF)

        for inf in self.__infSet:
            infColumnNames1 = self.__infColumnDict1[self.__infMap[inf]]
            infColumnNames2 = self.__infColumnDict2[self.__infMap[inf]]
            data1, data2 = self.__preprocessINFTickData(inf, startDate, endDate, infColumnNames1, infColumnNames2)

            previousData1 = self.__tickDataDict1[inf]
            mask = previousData1[:, self.__infIndexColumnDict1[self.__infMap[inf]]["Date"]] >= realStartDate
            previousData1 = previousData1[mask, :]
            self.__tickDataDict1[inf] = np.concatenate((previousData1, data1.values), axis=0)

            previousData2 = self.__tickDataDict2[inf]
            previousData2 = previousData2[mask, :]
            self.__tickDataDict2[inf] = np.concatenate((previousData2, data2.values), axis=0)

        for symbol in self.__infSpecialGroup:
            self.__tickDataDict1.pop(symbol)
            self.__tickDataDict2.pop(symbol)
            self.__minuteDataDict.pop(symbol)
            self.__dailyDataDict.pop(symbol)

        self.__infSpecialGroup = set()
        for inf in self.__infGroup:
            for stock in self.__stockSetTS:
                targetIndustryList = []
                for date in getTradingDay(realStartDate, endDate):
                    targetIndustry = self.__configAnalyzer.getIndustryCode(stock, date, inf.rstrip("_INF"))
                    targetIndustry = targetIndustry if targetIndustry is None else targetIndustry + "_INF"
                    targetIndustryList.append(targetIndustry)

                if sum([targetIndustry is not None for targetIndustry in targetIndustryList]) == 0:
                    continue

                if len(set(targetIndustryList)) > 1:
                    tickData1List = []
                    tickData2List = []
                    for i, date in enumerate(getTradingDay(realStartDate, endDate)):
                        targetIndustry = targetIndustryList[i]
                        if targetIndustry is None:
                            continue

                        tickData1 = self.__tickDataDict1[targetIndustry]
                        tickData2 = self.__tickDataDict2[targetIndustry]
                        mask = tickData1[:, self.__infIndexColumnDict1[inf]["Date"]] == date
                        tickData1 = tickData1[mask, :]
                        tickData2 = tickData2[mask, :]
                        tickData1List.append(tickData1)
                        tickData2List.append(tickData2)
                    self.__tickDataDict1["{}_{}".format(inf, stock)] = np.concatenate(tickData1List, axis=0)
                    self.__tickDataDict2["{}_{}".format(inf, stock)] = np.concatenate(tickData2List, axis=0)
                    self.__minuteDataDict["{}_{}".format(inf, stock)] = np.zeros((0, len(self.__infColumnDict1[inf])))
                    self.__dailyDataDict["{}_{}".format(inf, stock)] = np.zeros((0, len(self.__infColumnDict1[inf])))
                    self.__infSpecialGroup.add("{}_{}".format(inf, stock))

        for inf in self.__infGroup:
            self.__tickDataDict3[inf] = {}
            infColumnNames = self.__infColumnDict2[inf]
            for stock in self.__stockSetTS:
                for date in getTradingDay(startDate, endDate):
                    targetIndustry = self.__configAnalyzer.getIndustryCode(stock, date, inf.rstrip("_INF"))
                    if targetIndustry is not None:
                        break
                else:
                    continue

                self.__tickDataDict3[inf][stock] = {}
                for infColumnName in infColumnNames:
                    infArrayList = []
                    for date in getTradingDay(realStartDate, endDate):
                        targetIndustry = self.__configAnalyzer.getIndustryCode(stock, date, inf.rstrip("_INF"))
                        if targetIndustry is None:
                            continue
                        targetIndustry += "_INF"

                        stockIndex = self.__infStockListDict[targetIndustry][date].index(stock)
                        tickData1 = self.__tickDataDict1[targetIndustry]
                        tickData2 = self.__tickDataDict2[targetIndustry]
                        mask = tickData1[:, self.__infIndexColumnDict1[inf]["Date"]] == date
                        tickData2 = tickData2[mask, :]
                        columnIndex = self.__infIndexColumnDict2[inf][infColumnName]
                        infArray = np.array(tickData2[:, columnIndex].tolist())
                        infArrayList.append(infArray[:, stockIndex])

                    self.__tickDataDict3[inf][stock][infColumnName] = np.concatenate(infArrayList)

    def __preprocessMinuteData(self, stock, startDate, endDate):
        data = self.__HFDataDict[stock].get_minute_data(startDate, endDate).astype(np.float64)
        data = data.loc[data["Time"] >= 130000000]
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
        data = self.__HFDataDict[stock].get_tick_data(startDate, endDate).astype(
            {columnName: np.float64 for columnName in self.__tickColumnNames1}
        )
        data = data.loc[data["Time"] >= 130000000]
        data = data.drop(self.__invalidTradingDayDict[stock], errors="ignore")

        tradingDayList = getTradingDay(startDate, endDate)
        fillData = self.__getFillTickData(self.__invalidTradingDayDict[stock].intersection(tradingDayList),
                                          self.__tickColumnNames1, self.__tickColumnNames2)
        data1 = pd.concat([data[self.__tickColumnNames1], fillData[self.__tickColumnNames1]], axis=0)
        data2 = pd.concat([data[self.__tickColumnNames2], fillData[self.__tickColumnNames2]], axis=0)
        data = pd.concat([data1, data2], axis=1)

        data.index.name = None
        data = data.sort_values("Timestamp")

        return data[self.__tickColumnNames1].astype(np.float64), data[self.__tickColumnNames2]

    def __preprocessIndexDailyData(self, stock, startDate, endDate):
        data = self.__HFDataDictForIndex[stock].get_daily_data(startDate, endDate)
        data = data.loc[:, INDEX_DAILY_COLUMN_NAMES].astype(np.float64)

        data.index.name = None
        data = data.sort_values("Date")

        return data

    def __preprocessIndexMinuteData(self, stock, startDate, endDate):
        data = self.__HFDataDictForIndex[stock].get_minute_data(startDate, endDate)
        data = data.loc[:, INDEX_MINUTE_COLUMN_NAMES].astype(np.float64)
        data = data.loc[data["Time"] >= 130000000]

        data["Timestamp"] += 60

        data.index.name = None
        data = data.sort_values("Timestamp")

        return data

    def __preprocessIndexTickData(self, stock, startDate, endDate):
        data = self.__HFDataDictForIndex[stock].get_tick_data(startDate, endDate)
        data = data.loc[:, INDEX_TICK_COLUMN_NAMES].astype(np.float64)
        data = data.loc[data["Time"] >= 130000000]

        data.index.name = None
        data = data.sort_values("Timestamp")

        return data

    def __preprocessINFTickData(self, stock, startDate, endDate, infColumnNames1, infColumnNames2):
        infColumnNames = infColumnNames1 + infColumnNames2 + ["Symbols"]
        data = self.__HFDataDictForINF[stock].get_inf_tick_data(startDate, endDate, infColumnNames).astype(
            {columnName: np.float64 for columnName in infColumnNames1}
        )
        data = data.loc[data["Time"] >= 130000000]
        data.index.name = None
        data = data.sort_values("Timestamp")

        if stock not in self.__infStockListDict:
            self.__infStockListDict[stock] = {}
        for date, stockListSeries in data.groupby("Date")["Symbols"]:
            self.__infStockListDict[stock][int(date)] = stockListSeries.iloc[0]

        data = data.drop(columns="Symbols")

        data1 = data.loc[:, infColumnNames1]
        data2 = data.loc[:, infColumnNames2]

        return data1, data2

    @staticmethod
    def __getFillMinuteData(invalidTradingDaySet, minuteColumnNames):
        invalidTradingDayList = list(invalidTradingDaySet)
        invalidTradingDayListStr = list(map(str, invalidTradingDayList))

        startDatetimeList = [dt.datetime.strptime(dateStr + "1300", "%Y%m%d%H%M")
                             for dateStr in invalidTradingDayListStr]
        datetimeList = []
        for startDatetime in startDatetimeList:
            datetimeList.extend(
                [startDatetime + dt.timedelta(minutes=i) for i in range(120)]
            )

        dateList = np.repeat(invalidTradingDayList, 120)
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

        startDatetimeList = [dt.datetime.strptime(dateStr + "130015", "%Y%m%d%H%M%S")
                             for dateStr in invalidTradingDayListStr]
        datetimeList = []
        for startDatetime in startDatetimeList:
            datetimeList.extend(
                [startDatetime + dt.timedelta(seconds=3 * i) for i in range(2335)]
            )

        dateList = np.repeat(invalidTradingDayList, 2335)
        timeList = [int(v.strftime("%H%M%S%f")[:-3]) for v in datetimeList]
        timestampList = [v.timestamp() for v in datetimeList]

        fillTickData = pd.DataFrame(index=dateList, columns=tickColumnNames1 + tickColumnNames2)
        fillTickData["Date"] = dateList
        fillTickData["Time"] = timeList
        fillTickData["Timestamp"] = timestampList
        fillTickData.loc[:, tickColumnNames2] = None

        return fillTickData

import gc
import numpy as np
import pandas as pd
from Constants.INDEX_LIST import INDEX_LIST
from System.TradingDay import getTradingDay, getNDaysOff
from System.COLUMN_CONFIG import (TICK_COLUMN_NAMES1, TICK_COLUMN_NAMES2, MINUTE_COLUMN_NAMES, DAILY_COLUMN_NAMES,
                                  TICK_COLUMN_INDEX_DICT1, TRANSACTION_COLUMN_INDEX_DICT)
from System.COLUMN_CONFIG import (INDEX_TICK_COLUMN_NAMES, INDEX_MINUTE_COLUMN_NAMES, INDEX_DAILY_COLUMN_NAMES,
                                  INDEX_TICK_COLUMN_INDEX_DICT)
from System.COLUMN_CONFIG import (CB_TICK_COLUMN_NAMES1, CB_TICK_COLUMN_NAMES2, CB_MINUTE_COLUMN_NAMES,
                                  CB_DAILY_COLUMN_NAMES, CB_TICK_COLUMN_INDEX_DICT1, CB_TRANSACTION_COLUMN_INDEX_DICT)
from System.COLUMN_CONFIG import (ETF_TICK_COLUMN_NAMES1, ETF_TICK_COLUMN_NAMES2, ETF_MINUTE_COLUMN_NAMES,
                                  ETF_DAILY_COLUMN_NAMES, ETF_TICK_COLUMN_INDEX_DICT1,
                                  ETF_TRANSACTION_COLUMN_INDEX_DICT)
from HFDataLoader.HFData import HFData


class DataCollector:
    """
    Load data via HFData dynamically
    """

    def __init__(self, libraryName, startDate, endDate, stockSetTS, stockSetAll, configAnalyzer):
        self.__LIMIT_THRESHOLD = 2.0

        self.__PRICE_COLUMN_NAMES_1 = ["PreviousClose", "LastPrice", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice",
                                       "MinPrice"]
        self.__PRICE_COLUMN_NAMES_2 = ["BidPrice", "AskPrice"]
        self.__PRICE_COLUMN_NAME_3 = "Transactions"
        self.__PRICE_COLUMN_INDEX_3 = TRANSACTION_COLUMN_INDEX_DICT["Price"]
        self.__PRICE_COLUMN_NAMES_4 = ["OpenPrice", "HighPrice", "LowPrice", "ClosePrice"]
        self.__PRICE_COLUMN_NAMES_5 = ["PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "ClosePrice"]

        self.__library = libraryName
        self.__startDate = startDate
        self.__endDate = endDate
        self.__stockSetTS = stockSetTS
        self.__stockSetAll = stockSetAll
        self.__configAnalyzer = configAnalyzer

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
        self.__dataType = dataRequirements["dataType"]
        self.__dataTypeCS = dataRequirements["dataTypeCS"]
        self.__dataTypeIndex = dataRequirements["dataTypeIndex"]
        self.__indexGroup = dataRequirements["indexGroup"]
        self.__splitAdjustedNeeded = dataRequirements["splitAdjustedNeeded"]

        self.__allTradingDayDict = {}
        self.__invalidTradingDayDict = {}
        self.__adjFactorDict = {}
        self.__tickDataDict1 = {}
        self.__tickDataDict2 = {}
        self.__minuteDataDict = {}
        self.__dailyDataDict = {}
        self.__dailyDataDictOriginal = {}
        self.__tickDataDict1SplitAdjusted = {}
        self.__tickDataDict2SplitAdjusted = {}
        self.__minuteDataDictSplitAdjusted = {}
        self.__dailyDataDictSplitAdjusted = {}

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

    def loadData(self):
        self.__loadIndexDataFirstTime()
        self.__convertDataFrameIntoNdArray()

    def setAllTradingDayDict(self, allTradingDayDict):
        self.__allTradingDayDict.update(allTradingDayDict)

    def setInvalidTradingDayDict(self, invalidTradingDayDict):
        self.__invalidTradingDayDict.update(invalidTradingDayDict)

    def setAdjFactorDict(self, adjFactorDict):
        self.__adjFactorDict.update(adjFactorDict)

    def setTickDataDict(self, tickDataDict1, tickDataDict2, tickDataDict1SplitAdjusted, tickDataDict2SplitAdjusted):
        self.__tickDataDict1.update(tickDataDict1)
        self.__tickDataDict2.update(tickDataDict2)
        self.__tickDataDict1SplitAdjusted.update(tickDataDict1SplitAdjusted)
        self.__tickDataDict2SplitAdjusted.update(tickDataDict2SplitAdjusted)

    def setMinuteDataDict(self, minuteDataDict, minuteDataDictSplitAdjusted):
        self.__minuteDataDict.update(minuteDataDict)
        self.__minuteDataDictSplitAdjusted.update(minuteDataDictSplitAdjusted)

    def setDailyDataDict(self, dailyDataDictOriginal, dailyDataDict, dailyDataDictSplitAdjusted):
        self.__dailyDataDictOriginal.update(dailyDataDictOriginal)
        self.__dailyDataDict.update(dailyDataDict)
        self.__dailyDataDictSplitAdjusted.update(dailyDataDictSplitAdjusted)

    def getStockSetAll(self):
        return self.__stockSetAll

    def getIndexSet(self):
        return self.__indexSet

    def getTickDataDict(self):
        return (self.__tickDataDict1, self.__tickDataDict2,
                self.__tickDataDict2SplitAdjusted, self.__tickDataDict2SplitAdjusted)

    def getMinuteDataDict(self):
        return self.__minuteDataDict, self.__minuteDataDictSplitAdjusted

    def getDailyDataDict(self):
        return self.__dailyDataDict, self.__dailyDataDictSplitAdjusted

    def getAllTradingDayDict(self):
        return self.__allTradingDayDict

    def getInvalidTradingDayDict(self):
        return self.__invalidTradingDayDict

    def updateTickData(self, date, tickDataDict1, tickDataDict2, tickDataDict1SplitAdjusted,
                       tickDataDict2SplitAdjusted):
        self.__updateTickData(date, tickDataDict1, tickDataDict2, tickDataDict1SplitAdjusted,
                              tickDataDict2SplitAdjusted)

        gc.collect()

    def updateMinuteAndIndexTickData(self, date):
        self.__updateMinuteData(date)
        self.__updateIndexTickData(date)

        gc.collect()

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

    def __updateMinuteData(self, date):
        for stock in self.__stockSetAll:
            minuteData = self.__minuteDataDict[stock]
            mask1 = minuteData[:, MINUTE_COLUMN_INDEX_DICT["Date"]] < date
            mask2 = minuteData[:, MINUTE_COLUMN_INDEX_DICT["LimitStatus"]] == 1
            ixGrid = np.ix_(mask1 & mask2, MINUTE_COLUMN_INDEX_LIST_2)
            minuteData[ixGrid] = np.nan

    def __updateTickData(self, date, tickDataDict1, tickDataDict2, tickDataDict1SplitAdjusted,
                         tickDataDict2SplitAdjusted):
        for stock in self.__stockSetAll:
            if stock in self.__stockSetTS:
                realStartDate = getNDaysOff(
                    date,
                    max(self.__historicalTickDataLength, self.__historicalTickDataLengthCS)
                )
            else:
                if "Tick" in self.__dataTypeCS:
                    realStartDate = getNDaysOff(date, self.__historicalTickDataLengthCS)
                else:
                    if self.__historicalTickDataLengthCS > 0:
                        realStartDate = getNDaysOff(date, self.__historicalTickDataLengthCS)
                    else:
                        continue

            data1 = tickDataDict1[stock]
            data2 = tickDataDict2[stock]

            previousData1 = self.__tickDataDict1[stock]
            mask1 = previousData1[:, TICK_COLUMN_INDEX_DICT1["Date"]] >= realStartDate
            previousData1 = previousData1[mask1, :]
            mask2 = previousData1[:, TICK_COLUMN_INDEX_DICT1["LimitStatus"]] == 1
            ixGrid = np.ix_(mask2, TICK_COLUMN_INDEX_LIST_1_2)
            previousData1[ixGrid] = np.nan
            self.__tickDataDict1[stock] = np.concatenate((previousData1, data1.values), axis=0)

            previousData2 = self.__tickDataDict2[stock]
            previousData2 = previousData2[mask1, :]
            previousData2[mask2, :] = None
            self.__tickDataDict2[stock] = np.concatenate((previousData2, data2.values), axis=0)

            if self.__splitAdjustedNeeded:
                data1 = tickDataDict1SplitAdjusted[stock]
                data2 = tickDataDict2SplitAdjusted[stock]

                data1.loc[:, self.__PRICE_COLUMN_NAMES_1] = data1.loc[:, self.__PRICE_COLUMN_NAMES_1].multiply(
                    self.__adjFactorDict[stock].reindex(data1.index),
                    axis=0
                )

                previousData1 = self.__tickDataDict1SplitAdjusted[stock]
                previousData1 = previousData1[mask1, :]
                previousData1[ixGrid] = np.nan
                self.__tickDataDict1SplitAdjusted[stock] = np.concatenate((previousData1, data1.values), axis=0)

                for priceColumnName in self.__PRICE_COLUMN_NAMES_2:
                    for priceData in data2.loc[date, priceColumnName]:
                        if priceData is not None:
                            priceData *= self.__adjFactorDict[stock][date]
                for transactionData in data2.loc[date, self.__PRICE_COLUMN_NAME_3]:
                    if transactionData is not None:
                        transactionData[:, self.__PRICE_COLUMN_INDEX_3] *= self.__adjFactorDict[stock][date]

                previousData2 = self.__tickDataDict2SplitAdjusted[stock]
                previousData2 = previousData2[mask1, :]
                previousData2[mask2, :] = None
                self.__tickDataDict2SplitAdjusted[stock] = np.concatenate((previousData2, data2.values), axis=0)

    def __updateIndexTickData(self, date):
        for stock in self.__indexSet:
            data = self.__preprocessIndexTickData(stock, date, date)

            previousData = self.__tickDataDict1[stock]
            realStartDate = getNDaysOff(date, self.__historicalTickDataLengthIndex)
            mask = previousData[:, INDEX_TICK_COLUMN_INDEX_DICT["Date"]] >= realStartDate
            previousData = previousData[mask, :]

            self.__tickDataDict1[stock] = np.concatenate((previousData, data.values), axis=0)

    def __preprocessIndexDailyData(self, stock, startDate, endDate):
        data = self.__HFDataDictForIndex[stock].get_daily_data(startDate, endDate)
        data = data.loc[:, INDEX_DAILY_COLUMN_NAMES].astype(np.float64)

        data.index.name = None
        data = data.sort_values("Date")

        return data

    def __preprocessIndexMinuteData(self, stock, startDate, endDate):
        data = self.__HFDataDictForIndex[stock].get_minute_data(startDate, endDate)
        data = data.loc[:, INDEX_MINUTE_COLUMN_NAMES].astype(np.float64)

        mask = data["Time"] == 92500000
        data.loc[mask, "Timestamp"] += 300
        data.loc[~mask, "Timestamp"] += 60

        data.index.name = None
        data = data.sort_values("Timestamp")

        return data

    def __preprocessIndexTickData(self, stock, startDate, endDate):
        data = self.__HFDataDictForIndex[stock].get_tick_data(startDate, endDate)
        data = data.loc[:, INDEX_TICK_COLUMN_NAMES].astype(np.float64)

        data.index.name = None
        data = data.sort_values("Timestamp")

        return data

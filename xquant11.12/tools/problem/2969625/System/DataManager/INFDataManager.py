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
from HFDataLoader.HFData import HFData


class INFDataManager:
    """
    Load data via HFData dynamically
    """

    def __init__(self, libraryName, assetType, underlyingAssetType, startDate, endDate, stockSetTS, stockSetAll,
                 configAnalyzer):
        self.__PRICE_COLUMN_NAMES_1 = ["PreviousClose", "LastPrice", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice",
                                       "MinPrice"]
        self.__PRICE_COLUMN_NAMES_2 = ["BidPrice", "AskPrice"]
        self.__PRICE_COLUMN_NAME_3 = "Transactions"
        self.__PRICE_COLUMN_NAMES_4 = ["OpenPrice", "HighPrice", "LowPrice", "ClosePrice"]
        self.__PRICE_COLUMN_NAMES_5 = ["PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "ClosePrice"]

        self.__library = libraryName
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
        self.__dataType = dataRequirements["dataType"]
        self.__dataTypeCS = dataRequirements["dataTypeCS"]
        self.__dataTypeIndex = dataRequirements["dataTypeIndex"]
        self.__indexGroup = dataRequirements["indexGroup"]
        self.__splitAdjustedNeeded = dataRequirements["splitAdjustedNeeded"]

        self.__invalidTradingDayDict = {}
        self.__adjFactorDict = {}
        self.__preCloseDict = {}
        self.__tickDataDict1 = {}
        self.__tickDataDict2 = {}
        self.__minuteDataDict = {}
        self.__dailyDataDict = {}
        self.__tickDataDict1SplitAdjusted = {}
        self.__tickDataDict2SplitAdjusted = {}
        self.__minuteDataDictSplitAdjusted = {}
        self.__dailyDataDictSplitAdjusted = {}

        self.__HFDataDict = {stock: HFData(libraryName, stock) for stock in stockSetAll - stockSetTS}

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

        self.__UASet = set()

    def loadData(self):
        """
        For Calculation Scheduler & SparkLauncher
        """
        self.__invalidTradingDayDict = {}

        self.__loadDailyData()
        self.__loadMinuteData()
        self.__loadTickDataFirstTime()

        self.__loadIndexDataFirstTime()

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
        validTradingDaySet = self.__configAnalyzer.getIndexValidTradingDaySet(stock, sDate, eDate)
        validTradingDayList = list(validTradingDaySet)
        validTradingDayList.sort()

        return validTradingDayList

    def updateTickData(self, date):
        """
        For Calculation Scheduler & SparkLauncher
        """
        self.__updateTickData(date)
        self.__updateIndexTickData(date)

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

        for stock in self.__stockSetAll - self.__stockSetTS:
            data = self.__HFDataDict[stock].get_daily_data(startDate, self.__endDate).astype(np.float64)

            data = data.reindex(allTradingDaySet).sort_index()
            data["Date"] = data.index.tolist()

            data.index.name = None
            data = data.sort_values("Date")
            data = data[self.__dailyColumnNames]

            invalidTradingDaySet = allTradingDaySet - set(data[data["TradeStatus"] == 1].index)

            self.__invalidTradingDayDict[stock] = invalidTradingDaySet
            self.__preCloseDict[stock] = data["PreviousClose"].astype(np.float64).to_dict()
            self.__dailyDataDict[stock] = data.astype(np.float64)
            if self.__splitAdjustedNeeded:
                self.__adjFactorDict[stock] = data["AdjFactor"].astype(np.float64)
                self.__dailyDataDictSplitAdjusted[stock] = data.astype(np.float64)

        for stock in self.__stockSetTS:
            self.__dailyDataDict[stock] = pd.DataFrame(columns=self.__dailyColumnNames)

    def __loadMinuteData(self):
        for stock in self.__stockSetAll - self.__stockSetTS:
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

        for stock in self.__stockSetTS:
            self.__minuteDataDict[stock] = pd.DataFrame(columns=self.__minuteColumnNames)

    def __loadTickDataFirstTime(self):
        for stock in self.__stockSetAll - self.__stockSetTS:
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

        for stock in self.__stockSetTS:
            self.__tickDataDict1[stock] = self.__mockTickTimeData(self.__startDate, self.__endDate,
                                                                  self.__tickColumnNames1)

    def __loadIndexDataFirstTime(self):
        for index in self.__indexSet:
            if self.__historicalDailyDataLengthIndex > 0:
                startDate = getNDaysOff(self.__startDate, self.__historicalDailyDataLengthIndex)
                endDate = self.__endDate
                self.__dailyDataDict[index] = self.__preprocessIndexDailyData(index, startDate, endDate)
            else:
                self.__dailyDataDict[index] = pd.DataFrame(columns=INDEX_DAILY_COLUMN_NAMES, dtype=np.float64)

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

    def __loadSplitAdjustedDataFirstTime(self):
        for stock, tickData in self.__tickDataDict1SplitAdjusted.items():
            tickData.loc[:, self.__PRICE_COLUMN_NAMES_1] = tickData.loc[:, self.__PRICE_COLUMN_NAMES_1].multiply(
                self.__adjFactorDict[stock].reindex(tickData.index),
                axis=0
            )

        for stock, tickData in self.__tickDataDict2SplitAdjusted.items():
            if stock in self.__stockSetAll - self.__stockSetTS:
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
        for stock in self.__stockSetAll - self.__stockSetTS:
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
        data = self.__HFDataDict[stock].get_tick_data(startDate, endDate).astype(
            {columnName: np.float64 for columnName in self.__tickColumnNames1}
        )
        data = data.drop(self.__invalidTradingDayDict[stock], errors="ignore")

        tradingDayList = getTradingDay(startDate, endDate)
        fillData = self.__getFillTickData(self.__invalidTradingDayDict[stock].intersection(tradingDayList),
                                          self.__preCloseDict[stock], self.__tickColumnNames1, self.__tickColumnNames2)
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
    def __getFillTickData(invalidTradingDaySet, preCloseDict, tickColumnNames1, tickColumnNames2):
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
        preCloseList = np.repeat([preCloseDict[date] for date in invalidTradingDayList], 4731)
        timeList = [int(v.strftime("%H%M%S%f")[:-3]) for v in datetimeList]
        timestampList = [v.timestamp() for v in datetimeList]

        fillTickData = pd.DataFrame(index=dateList, columns=tickColumnNames1 + tickColumnNames2)
        fillTickData["Date"] = dateList
        fillTickData["Time"] = timeList
        fillTickData["Timestamp"] = timestampList
        fillTickData["PreviousClose"] = preCloseList
        fillTickData["IsMock"] = False
        fillTickData.loc[:, tickColumnNames2] = None

        return fillTickData

    @staticmethod
    def __mockTickTimeData(startDate, endDate, tickColumnNames):
        tradingDayList = list(getTradingDay(startDate, endDate))
        tradingDayListStr = list(map(str, tradingDayList))

        startDatetimeList = [dt.datetime.strptime(dateStr + "093015", "%Y%m%d%H%M%S") for dateStr in tradingDayListStr]
        datetimeList = []
        for startDatetime in startDatetimeList:
            datetimeList.extend(
                [startDatetime + dt.timedelta(seconds=i) for i in range(7185)]
                + [startDatetime + dt.timedelta(seconds=12600) + dt.timedelta(seconds=i) for i in range(7005)]
            )

        dateList = np.repeat(tradingDayList, 14190)
        timeList = [int(v.strftime("%H%M%S%f")[:-3]) for v in datetimeList]
        timestampList = [v.timestamp() for v in datetimeList]

        mockedTickData = pd.DataFrame(index=dateList, columns=tickColumnNames)
        mockedTickData["Date"] = dateList
        mockedTickData["Time"] = timeList
        mockedTickData["Timestamp"] = timestampList

        return mockedTickData

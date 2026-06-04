import datetime as dt
import numpy as np
import pandas as pd
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


class DataLoader:
    """
    Load data via HFData dynamically
    """

    def __init__(self, libraryName, startDate, endDate, stockSetTS, stockSetAll, configAnalyzer):
        self.__LIMIT_THRESHOLD = 0.95

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

        self.__HFDataDict = {stock: HFData(libraryName, stock) for stock in stockSetAll}

    def loadData(self):
        """
        For Calculation Scheduler & SparkLauncher
        """
        self.__invalidTradingDayDict = {}

        self.__loadDailyData()
        self.__loadMinuteData()
        self.__loadTickDataFirstTime()

        if self.__splitAdjustedNeeded:
            self.__loadSplitAdjustedDataFirstTime()

        self.__convertDataFrameIntoNdArray()

    def getAllTradingDayDict(self):
        return self.__allTradingDayDict

    def getInvalidTradingDayDict(self):
        return self.__invalidTradingDayDict

    def getAdjFactorDict(self):
        return self.__adjFactorDict

    def getTickDataDict(self):
        return (self.__tickDataDict1, self.__tickDataDict2,
                self.__tickDataDict1SplitAdjusted, self.__tickDataDict2SplitAdjusted)

    def getMinuteDataDict(self):
        return self.__minuteDataDict, self.__minuteDataDictSplitAdjusted

    def getDailyDataDict(self):
        return self.__dailyDataDictOriginal, self.__dailyDataDict, self.__dailyDataDictSplitAdjusted

    def updateTickData(self, date):
        self.__updateTickData(date)

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
            data = data[DAILY_COLUMN_NAMES]

            dataOriginal = data.copy()

            invalidTradingDaySet = set(data[data["TradeStatus"] != 1].index)
            data.loc[invalidTradingDaySet, DAILY_COLUMN_NAMES2] = np.nan

            self.__allTradingDayDict[stock] = allTradingDaySet
            self.__invalidTradingDayDict[stock] = invalidTradingDaySet
            self.__dailyDataDict[stock] = data.astype(np.float64)
            self.__dailyDataDictOriginal[stock] = dataOriginal.astype(np.float64)
            self.__adjFactorDict[stock] = dataOriginal["AdjFactor"].astype(np.float64)

    def __loadMinuteData(self):
        for stock in self.__stockSetAll:
            if stock in self.__stockSetTS:
                historicalMinuteDataLengthAll = max(self.__historicalMinuteDataLength,
                                                    self.__historicalMinuteDataLengthCS)
                if "Minute" in self.__dataTypeCS or "Minute" in self.__dataType:
                    startDate = getNDaysOff(self.__startDate, historicalMinuteDataLengthAll)
                    endDate = self.__endDate
                else:
                    if historicalMinuteDataLengthAll > 0:
                        startDate = getNDaysOff(self.__startDate, historicalMinuteDataLengthAll)
                        endDate = getNDaysOff(self.__endDate, 1)
                    else:
                        self.__minuteDataDict[stock] = pd.DataFrame(columns=MINUTE_COLUMN_NAMES)
                        continue
            else:
                if "Minute" in self.__dataTypeCS:
                    startDate = getNDaysOff(self.__startDate, self.__historicalMinuteDataLengthCS)
                    endDate = self.__endDate
                else:
                    if self.__historicalMinuteDataLengthCS > 0:
                        startDate = getNDaysOff(self.__startDate, self.__historicalMinuteDataLengthCS)
                        endDate = getNDaysOff(self.__endDate, 1)
                    else:
                        self.__minuteDataDict[stock] = pd.DataFrame(columns=MINUTE_COLUMN_NAMES)
                        continue

            self.__minuteDataDict[stock] = self.__preprocessMinuteData(stock, startDate, endDate, self.__startDate)

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
                        self.__tickDataDict1[stock] = pd.DataFrame(columns=TICK_COLUMN_NAMES1, dtype=np.float64)
                        self.__tickDataDict2[stock] = pd.DataFrame(columns=TICK_COLUMN_NAMES2)
                        continue

            self.__tickDataDict1[stock], self.__tickDataDict2[stock] = self.__preprocessTickData(
                stock, startDate, endDate, self.__startDate
            )

            if self.__splitAdjustedNeeded:
                (self.__tickDataDict1SplitAdjusted[stock],
                 self.__tickDataDict2SplitAdjusted[stock]) = self.__preprocessTickData(
                    stock, startDate, endDate, self.__startDate
                )

    def __loadSplitAdjustedDataFirstTime(self):
        self.__minuteDataDictSplitAdjusted = {k: v.copy() for k, v in self.__minuteDataDict.items()}
        self.__dailyDataDictSplitAdjusted = {k: v.copy() for k, v in self.__dailyDataDict.items()}

        for stock, tickData in self.__tickDataDict1SplitAdjusted.items():
            tickData.loc[:, self.__PRICE_COLUMN_NAMES_1] = tickData.loc[:, self.__PRICE_COLUMN_NAMES_1].multiply(
                self.__adjFactorDict[stock].reindex(tickData.index),
                axis=0
            )

        for stock, tickData in self.__tickDataDict2SplitAdjusted.items():
            for date, tickDataSingleDay in tickData.groupby(level=0):
                for priceColumnName in self.__PRICE_COLUMN_NAMES_2:
                    for priceData in tickData.loc[date, priceColumnName]:
                        if priceData is not None:
                            priceData *= self.__adjFactorDict[stock][date]
                for transactionData in tickData.loc[date, self.__PRICE_COLUMN_NAME_3]:
                    if transactionData is not None:
                        transactionData[:, self.__PRICE_COLUMN_INDEX_3] *= self.__adjFactorDict[stock][date]

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
            else:
                if "Tick" in self.__dataTypeCS:
                    startDate = date
                    endDate = date
                else:
                    if self.__historicalTickDataLengthCS > 0:
                        startDate = getNDaysOff(date, 1)
                        endDate = getNDaysOff(date, 1)
                    else:
                        continue

            data1, data2 = self.__preprocessTickData(stock, startDate, endDate, date)
            self.__tickDataDict1[stock] = data1.values
            self.__tickDataDict2[stock] = data2.values

            if self.__splitAdjustedNeeded:
                data1, data2 = self.__preprocessTickData(stock, startDate, endDate, date)
                self.__tickDataDict1SplitAdjusted[stock] = data1.values
                self.__tickDataDict2SplitAdjusted[stock] = data2.values

    def __preprocessMinuteData(self, stock, startDate, endDate, today):
        data = self.__HFDataDict[stock].get_minute_data(startDate, endDate).astype(np.float64)
        data = data.drop(self.__invalidTradingDayDict[stock], errors="ignore")

        data["MaxPrice"] = self.__dailyDataDictOriginal[stock].loc[data.index, "MaxPrice"]
        data["MinPrice"] = self.__dailyDataDictOriginal[stock].loc[data.index, "MinPrice"]
        data["PreviousClose"] = self.__dailyDataDictOriginal[stock].loc[data.index, "PreviousClose"]

        data["LimitStatus"] = 0
        mask1 = data["HighPrice"] >= (self.__LIMIT_THRESHOLD * data["MaxPrice"]
                                      + (1 - self.__LIMIT_THRESHOLD) * data["PreviousClose"])
        mask2 = data["LowPrice"] <= (self.__LIMIT_THRESHOLD * data["MinPrice"]
                                     + (1 - self.__LIMIT_THRESHOLD) * data["PreviousClose"])
        data.loc[mask1 | mask2, "LimitStatus"] = 1
        mask3 = data["Date"].astype(np.float64) < today
        data.loc[(mask1 | mask2) & mask3, MINUTE_COLUMN_NAMES2] = np.nan

        tradingDayList = getTradingDay(startDate, endDate)
        fillData = self.__getFillMinuteData(self.__invalidTradingDayDict[stock].intersection(tradingDayList))
        data = pd.concat([data, fillData], axis=0)

        mask = data["Time"] == 92500000
        data.loc[mask, "Timestamp"] += 300
        data.loc[~mask, "Timestamp"] += 60

        data = data[MINUTE_COLUMN_NAMES]
        data.index.name = None
        data = data.sort_values("Timestamp")

        return data.astype(np.float64)

    @staticmethod
    def __getFillMinuteData(invalidTradingDaySet):
        invalidTradingDayList = list(invalidTradingDaySet)
        invalidTradingDayListStr = list(map(str, invalidTradingDayList))

        startDatetimeList = [dt.datetime.strptime(dateStr + "0930", "%Y%m%d%H%M")
                             for dateStr in invalidTradingDayListStr]
        datetimeList = []
        for startDatetime in startDatetimeList:
            datetimeList.extend(
                [startDatetime - dt.timedelta(minutes=5)]
                + [startDatetime + dt.timedelta(minutes=i) for i in range(120)]
                + [startDatetime + dt.timedelta(minutes=210) + dt.timedelta(minutes=i) for i in range(120)]
            )

        dateList = np.repeat(invalidTradingDayList, 241)
        timeList = [int(v.strftime("%H%M%S%f")[:-3]) for v in datetimeList]
        timestampList = [v.timestamp() for v in datetimeList]

        fillMinuteData = pd.DataFrame(index=dateList, columns=MINUTE_COLUMN_NAMES)
        fillMinuteData["Date"] = dateList
        fillMinuteData["Time"] = timeList
        fillMinuteData["Timestamp"] = timestampList
        fillMinuteData["LimitStatus"] = 0

        return fillMinuteData

    def __preprocessTickData(self, stock, startDate, endDate, today):
        data = self.__HFDataDict[stock].get_tick_data(startDate, endDate).astype(
            {columnName: np.float64 for columnName in TICK_COLUMN_NAMES1 if columnName != "LimitStatus"}
        )
        data = data.drop(self.__invalidTradingDayDict[stock], errors="ignore")

        data["LimitStatus"] = 0
        mask1 = data["LastPrice"] >= (self.__LIMIT_THRESHOLD * data["MaxPrice"]
                                      + (1 - self.__LIMIT_THRESHOLD) * data["PreviousClose"])
        mask2 = data["LastPrice"] <= (self.__LIMIT_THRESHOLD * data["MinPrice"]
                                      + (1 - self.__LIMIT_THRESHOLD) * data["PreviousClose"])
        data.loc[mask1 | mask2, "LimitStatus"] = 1
        mask3 = data["Date"] < today
        data.loc[(mask1 | mask2) & mask3, TICK_COLUMN_NAMES1_2] = np.nan
        data.loc[(mask1 | mask2) & mask3, TICK_COLUMN_NAMES2] = None

        tradingDayList = getTradingDay(startDate, endDate)
        fillData = self.__getFillTickData(self.__invalidTradingDayDict[stock].intersection(tradingDayList))
        data1 = pd.concat([data[TICK_COLUMN_NAMES1], fillData[TICK_COLUMN_NAMES1]], axis=0)
        data2 = pd.concat([data[TICK_COLUMN_NAMES2], fillData[TICK_COLUMN_NAMES2]], axis=0)
        data = pd.concat([data1, data2], axis=1)

        data.index.name = None
        data = data.sort_values("Timestamp")

        return data[TICK_COLUMN_NAMES1].astype(np.float64), data[TICK_COLUMN_NAMES2]

    @staticmethod
    def __getFillTickData(invalidTradingDaySet):
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

        fillTickData = pd.DataFrame(index=dateList, columns=TICK_COLUMN_NAMES1 + TICK_COLUMN_NAMES2)
        fillTickData["Date"] = dateList
        fillTickData["Time"] = timeList
        fillTickData["Timestamp"] = timestampList
        fillTickData["LimitStatus"] = 0
        fillTickData.loc[:, TICK_COLUMN_NAMES2] = None

        return fillTickData

import datetime as dt
import numpy as np
from System.COLUMN_CONFIG import (CB_TICK_COLUMN_INDEX_DICT1, CB_TICK_COLUMN_INDEX_DICT2, CB_MINUTE_COLUMN_INDEX_DICT,
                                  CB_DAILY_COLUMN_INDEX_DICT)
from System.COLUMN_CONFIG import (INDEX_TICK_COLUMN_INDEX_DICT, INDEX_MINUTE_COLUMN_INDEX_DICT,
                                  INDEX_DAILY_COLUMN_INDEX_DICT)
from System.COLUMN_CONFIG import (TICK_COLUMN_INDEX_DICT1, TICK_COLUMN_INDEX_DICT2, MINUTE_COLUMN_INDEX_DICT,
                                  DAILY_COLUMN_INDEX_DICT)


class CBDataBroadcasterMinute:
    """
    Load all accessible data from the dataManager, generate indices for the loaded data,
    broadcast, i.e. update the indices, according to timestamps and provide available data for Factor
    """

    def __init__(self, symbol, stockSet, dataManager):
        self.__TICK_PLAY_LAG = 3
        self.__MINUTE_PLAY_LAG = 60

        self.__symbol = symbol
        self.__stockSet = stockSet
        self.__stockSet2 = stockSet - {symbol}
        self.__dataManager = dataManager
        self.__indexSet = self.__dataManager.getIndexSet()
        self.__UASet = self.__dataManager.getUASet()
        self.__stockUASet = self.__stockSet.union(self.__UASet)
        self.__stockUASet2 = self.__stockSet2.union(self.__UASet)
        self.__stockIndexUASet = self.__stockSet.union(self.__indexSet).union(self.__UASet)
        self.__stockIndexUASet2 = self.__stockSet2.union(self.__indexSet).union(self.__UASet)
        self.__splitAdjustedNeeded = self.__dataManager.getSplitAdjustedNeeded()
        self.__tradingDayList = self.__dataManager.getAllTradingDayList()

        self.__tickColumnIndexDict1 = CB_TICK_COLUMN_INDEX_DICT1
        self.__tickColumnIndexDict2 = CB_TICK_COLUMN_INDEX_DICT2
        self.__minuteColumnIndexDict = CB_MINUTE_COLUMN_INDEX_DICT
        self.__dailyColumnIndexDict = CB_DAILY_COLUMN_INDEX_DICT

        self.__tickColumnIndexDictIndex = INDEX_TICK_COLUMN_INDEX_DICT
        self.__minuteColumnIndexDictIndex = INDEX_MINUTE_COLUMN_INDEX_DICT
        self.__dailyColumnIndexDictIndex = INDEX_DAILY_COLUMN_INDEX_DICT

        self.__tickColumnIndexDict1UA = TICK_COLUMN_INDEX_DICT1
        self.__tickColumnIndexDict2UA = TICK_COLUMN_INDEX_DICT2
        self.__minuteColumnIndexDictUA = MINUTE_COLUMN_INDEX_DICT
        self.__dailyColumnIndexDictUA = DAILY_COLUMN_INDEX_DICT

        self.__tickData1 = None
        self.__tickData2 = None
        self.__minuteData = None
        self.__dailyData = None
        self.__tickData1SA = None
        self.__tickData2SA = None
        self.__minuteDataSA = None
        self.__dailyDataSA = None
        self.__tickTimestampDict = None
        self.__minuteTimestampDict = None

        self.__tickStartIndexAllDict = None
        self.__tickEndIndexAllDict = None
        self.__minuteStartIndexAllDict = None
        self.__minuteEndIndexAllDict = None
        self.__dailyStartIndexAllDict = None
        self.__dailyEndIndexAllDict = None

        self.__tickStartIndexDict = None
        self.__tickCurrIndexDict = None
        self.__tickEndIndexDict = None
        self.__minuteStartIndexDict = None
        self.__minuteCurrIndexDict = None
        self.__minuteEndIndexDict = None
        self.__dailyStartIndexDict = None
        self.__dailyEndIndexDict = None

        self.__currIndex = None
        self.__broadcastingEndTimestamp = None

    def onNewDay(self, date):
        self.__tickData1 = None
        self.__tickData2 = None
        self.__minuteData = None
        self.__dailyData = None
        self.__tickData1SA = None
        self.__tickData2SA = None
        self.__minuteDataSA = None
        self.__dailyDataSA = None
        self.__tickTimestampDict = {}
        self.__minuteTimestampDict = {}

        self.__tickStartIndexAllDict = {}
        self.__tickEndIndexAllDict = {}
        self.__minuteStartIndexAllDict = {}
        self.__minuteEndIndexAllDict = {}
        self.__dailyStartIndexAllDict = {}
        self.__dailyEndIndexAllDict = {}

        self.__tickStartIndexDict = {}
        self.__tickCurrIndexDict = {}
        self.__tickEndIndexDict = {}
        self.__minuteStartIndexDict = {}
        self.__minuteCurrIndexDict = {}
        self.__minuteEndIndexDict = {}
        self.__dailyStartIndexDict = {}
        self.__dailyEndIndexDict = {}

        self.__currIndex = None
        self.__broadcastingEndTimestamp = dt.datetime.strptime(f"{date}145700", "%Y%m%d%H%M%S").timestamp()

        self.__loadData()
        self.__generateStartEndIndexAllDict()
        self.__generateStartEndIndexDict(date)

    def __loadData(self):
        self.__tickData1, self.__tickData2 = self.__dataManager.getTickData(self.__stockIndexUASet, False)
        self.__minuteData = self.__dataManager.getMinuteData(self.__stockIndexUASet, False)
        self.__dailyData = self.__dataManager.getDailyData(self.__stockIndexUASet, False)

        tickData1 = self.__tickData1[self.__symbol]
        tickData2 = self.__tickData2[self.__symbol]
        mask = tickData1[:, self.__tickColumnIndexDict1["Time"]] >= 93015000
        self.__tickData1[self.__symbol] = tickData1[mask, :]
        self.__tickData2[self.__symbol] = tickData2[mask, :]

        if self.__splitAdjustedNeeded:
            self.__tickData1SA, self.__tickData2SA = self.__dataManager.getTickData(self.__stockIndexUASet, True)
            self.__minuteDataSA = self.__dataManager.getMinuteData(self.__stockIndexUASet, True)
            self.__dailyDataSA = self.__dataManager.getDailyData(self.__stockIndexUASet, True)

    def __generateStartEndIndexAllDict(self):
        # Generate StartIndexAllDict & EndIndexAllDict according to the data
        for stock in self.__stockIndexUASet:
            if stock in self.__indexSet:
                timestampIndex = self.__tickColumnIndexDictIndex["Timestamp"]
                dateIndex = self.__tickColumnIndexDictIndex["Date"]
            elif stock in self.__UASet:
                timestampIndex = self.__tickColumnIndexDict1UA["Timestamp"]
                dateIndex = self.__tickColumnIndexDict1UA["Date"]
            else:
                timestampIndex = self.__tickColumnIndexDict1["Timestamp"]
                dateIndex = self.__tickColumnIndexDict1["Date"]
            tickData = self.__tickData1[stock]
            self.__tickTimestampDict[stock] = tickData[:, timestampIndex]
            dates, counts = np.unique(tickData[:, dateIndex], return_counts=True)
            indices = np.cumsum(counts)
            if dates.shape[0] > 0:
                self.__tickEndIndexAllDict[stock] = {int(date): int(index) for date, index in zip(dates, indices)}
                self.__tickStartIndexAllDict[stock] = {
                    int(date): int(index) for date, index in zip(dates, np.hstack((0, indices[:-1])))
                }
            else:
                self.__tickEndIndexAllDict[stock] = {date: 0 for date in self.__tradingDayList}
                self.__tickStartIndexAllDict[stock] = {date: 0 for date in self.__tradingDayList}

            if stock in self.__indexSet:
                timestampIndex = self.__minuteColumnIndexDictIndex["Timestamp"]
                dateIndex = self.__minuteColumnIndexDictIndex["Date"]
            elif stock in self.__UASet:
                timestampIndex = self.__minuteColumnIndexDictUA["Timestamp"]
                dateIndex = self.__minuteColumnIndexDictUA["Date"]
            else:
                timestampIndex = self.__minuteColumnIndexDict["Timestamp"]
                dateIndex = self.__minuteColumnIndexDict["Date"]
            minuteData = self.__minuteData[stock]
            self.__minuteTimestampDict[stock] = minuteData[:, timestampIndex]
            dates, counts = np.unique(minuteData[:, dateIndex], return_counts=True)
            indices = np.cumsum(counts)
            if dates.shape[0] > 0:
                self.__minuteEndIndexAllDict[stock] = {int(date): int(index) for date, index in zip(dates, indices)}
                self.__minuteStartIndexAllDict[stock] = {
                    int(date): int(index) for date, index in zip(dates, np.hstack((0, indices[:-1])))
                }
            else:
                self.__minuteEndIndexAllDict[stock] = {date: 0 for date in self.__tradingDayList}
                self.__minuteStartIndexAllDict[stock] = {date: 0 for date in self.__tradingDayList}

            if stock in self.__indexSet:
                dateIndex = self.__dailyColumnIndexDictIndex["Date"]
            elif stock in self.__UASet:
                dateIndex = self.__dailyColumnIndexDictUA["Date"]
            else:
                dateIndex = self.__dailyColumnIndexDict["Date"]
            dailyData = self.__dailyData[stock]
            dates, counts = np.unique(dailyData[:, dateIndex], return_counts=True)
            indices = np.cumsum(counts)
            if dates.shape[0] > 0:
                self.__dailyEndIndexAllDict[stock] = {int(date): int(index) for date, index in zip(dates, indices)}
                self.__dailyStartIndexAllDict[stock] = {
                    int(date): int(index) for date, index in zip(dates, np.hstack((0, indices[:-1])))
                }
            else:
                self.__dailyEndIndexAllDict[stock] = {date: 0 for date in self.__tradingDayList}
                self.__dailyStartIndexAllDict[stock] = {date: 0 for date in self.__tradingDayList}

        # Fill the missing dates in StartIndexAllDict & EndIndexAllDict according to the tradingDaySet
        # This happens when there is not enough available data for new stock OR there is missing data in the database
        for stock in self.__stockIndexUASet:
            preTickEndIndex = 0
            for date in self.__tradingDayList:
                if date not in self.__tickStartIndexAllDict[stock]:
                    self.__tickStartIndexAllDict[stock][date] = preTickEndIndex
                    self.__tickEndIndexAllDict[stock][date] = preTickEndIndex
                preTickEndIndex = self.__tickEndIndexAllDict[stock][date]

            preMinuteEndIndex = 0
            for date in self.__tradingDayList:
                if date not in self.__minuteStartIndexAllDict[stock]:
                    self.__minuteStartIndexAllDict[stock][date] = preMinuteEndIndex
                    self.__minuteEndIndexAllDict[stock][date] = preMinuteEndIndex
                preMinuteEndIndex = self.__minuteEndIndexAllDict[stock][date]

            preDailyEndIndex = 0
            for date in self.__tradingDayList:
                if date not in self.__dailyStartIndexAllDict[stock]:
                    self.__dailyStartIndexAllDict[stock][date] = preDailyEndIndex
                    self.__dailyEndIndexAllDict[stock][date] = preDailyEndIndex
                preDailyEndIndex = self.__dailyEndIndexAllDict[stock][date]

    def __generateStartEndIndexDict(self, date):
        for symbol in self.__stockIndexUASet:
            self.__tickStartIndexDict[symbol] = self.__tickStartIndexAllDict[symbol][date]
            self.__tickEndIndexDict[symbol] = self.__tickEndIndexAllDict[symbol][date]
            self.__tickCurrIndexDict[symbol] = self.__tickStartIndexAllDict[symbol][date]
            self.__minuteStartIndexDict[symbol] = self.__minuteStartIndexAllDict[symbol][date]
            self.__minuteEndIndexDict[symbol] = self.__minuteEndIndexAllDict[symbol][date]
            self.__minuteCurrIndexDict[symbol] = self.__minuteStartIndexAllDict[symbol][date]
            self.__dailyStartIndexDict[symbol] = self.__dailyStartIndexAllDict[symbol][date]
            self.__dailyEndIndexDict[symbol] = self.__dailyEndIndexAllDict[symbol][date]
        self.__currIndex = self.__minuteStartIndexDict[self.__symbol]

    def broadcast(self):
        self.__currIndex += 1
        if (self.__currIndex > self.__minuteEndIndexDict[self.__symbol]
                or self.__minuteTimestampDict[self.__symbol][self.__currIndex - 1] > self.__broadcastingEndTimestamp):
            return None

        self.__minuteCurrIndexDict[self.__symbol] = self.__currIndex
        thisMinuteTimestamp = self.__minuteTimestampDict[self.__symbol][self.__currIndex - 1]

        thisTickCurrIndex = self.__tickCurrIndexDict[self.__symbol]
        thisTickTimestampArray = self.__tickTimestampDict[self.__symbol]
        while (thisTickCurrIndex < thisTickTimestampArray.shape[0]
               and thisTickTimestampArray[thisTickCurrIndex] <= thisMinuteTimestamp):
            thisTickCurrIndex += 1
        self.__tickCurrIndexDict[self.__symbol] = thisTickCurrIndex

        for symbol in self.__stockIndexUASet2:
            tickCurrIndex = self.__tickCurrIndexDict[symbol]
            tickTimestampArray = self.__tickTimestampDict[symbol]
            while (tickCurrIndex < tickTimestampArray.shape[0]
                   and tickTimestampArray[tickCurrIndex] <= thisMinuteTimestamp - self.__TICK_PLAY_LAG):
                tickCurrIndex += 1
            self.__tickCurrIndexDict[symbol] = tickCurrIndex

            minuteCurrIndex = self.__minuteCurrIndexDict[symbol]
            minuteTimestampArray = self.__minuteTimestampDict[symbol]
            while (minuteCurrIndex < minuteTimestampArray.shape[0]
                   and minuteTimestampArray[minuteCurrIndex] <= thisMinuteTimestamp - self.__MINUTE_PLAY_LAG):
                minuteCurrIndex += 1
            self.__minuteCurrIndexDict[symbol] = minuteCurrIndex

        return thisMinuteTimestamp

    def getLastNTickData(self, field, startDate, stock, splitAdjusted, mode, n=None):
        if stock in self.__stockSet:
            splitAdjusted = False

        tickData, tickColumnIndexDict = self.__getTickData(field, splitAdjusted, stock)

        if mode == 0:
            # All
            tickStartIndex = self.__tickStartIndexAllDict[stock][startDate]
            tickEndIndex = self.__tickCurrIndexDict[stock]
        elif mode == 1:
            # Today
            tickStartIndex = self.__tickStartIndexDict[stock]
            tickEndIndex = self.__tickCurrIndexDict[stock]
        elif mode == 2:
            # Historical
            tickStartIndex = self.__tickStartIndexAllDict[stock][startDate]
            tickEndIndex = self.__tickStartIndexDict[stock]
        else:
            raise Exception("Unexpected mode for getLastNTickData")

        if n is not None:
            tickStartIndex = max(tickEndIndex - n, tickStartIndex)

        return tickData[tickStartIndex:tickEndIndex, tickColumnIndexDict[field]]

    def getLastNTickDataForStockGroup(self, field, startDate, stockList, splitAdjusted, mode, isStacked, n=None):
        splitAdjusted = False

        tickDataAll, tickColumnIndexDict, fillValue = self.__getTickData(field, splitAdjusted, isGetAll=True)

        tickDataList = []
        for symbol in stockList:
            if mode == 0:
                # All
                tickStartIndex = self.__tickStartIndexAllDict[symbol][startDate]
                tickEndIndex = self.__tickCurrIndexDict[symbol]
            elif mode == 1:
                # Today
                tickStartIndex = self.__tickStartIndexDict[symbol]
                tickEndIndex = self.__tickCurrIndexDict[symbol]
            elif mode == 2:
                # Historical
                tickStartIndex = self.__tickStartIndexAllDict[symbol][startDate]
                tickEndIndex = self.__tickStartIndexDict[symbol]
            else:
                raise Exception("Unexpected mode for getLastNTickDataForStockGroup")

            tickData = tickDataAll[symbol]

            if n is not None:
                tickStartIndex = max(tickEndIndex - n, tickStartIndex)

            res = tickData[tickStartIndex:tickEndIndex, tickColumnIndexDict[field]]
            tickDataList.append(res)

        return np.stack(self.__alignNdArrayList(tickDataList, fillValue), axis=1) if isStacked else tickDataList

    def getLastNMinuteData(self, field, startDate, stock, splitAdjusted, mode, n=None):
        if stock in self.__stockSet:
            splitAdjusted = False

        minuteData, minuteColumnIndexDict = self.__getMinuteData(splitAdjusted, stock)

        if mode == 0:
            # All
            minuteStartIndex = self.__minuteStartIndexAllDict[stock][startDate]
            minuteEndIndex = self.__minuteCurrIndexDict[stock]
        elif mode == 1:
            # Today
            minuteStartIndex = self.__minuteStartIndexDict[stock]
            minuteEndIndex = self.__minuteCurrIndexDict[stock]
        elif mode == 2:
            # Historical
            minuteStartIndex = self.__minuteStartIndexAllDict[stock][startDate]
            minuteEndIndex = self.__minuteStartIndexDict[stock]
        else:
            raise Exception("Unexpected mode for getLastNMinuteData")

        if n is not None:
            minuteStartIndex = max(minuteEndIndex - n, minuteStartIndex)

        return minuteData[minuteStartIndex:minuteEndIndex, minuteColumnIndexDict[field]]

    def getLastNMinuteDataForStockGroup(self, field, startDate, stockList, splitAdjusted, mode, isStacked, n=None):
        splitAdjusted = False

        minuteDataAll, minuteColumnIndexDict = self.__getMinuteData(splitAdjusted, isGetAll=True)

        minuteDataList = []
        for symbol in stockList:
            if mode == 0:
                # All
                minuteStartIndex = self.__minuteStartIndexAllDict[symbol][startDate]
                minuteEndIndex = self.__minuteCurrIndexDict[symbol]
            elif mode == 1:
                minuteStartIndex = self.__minuteStartIndexDict[symbol]
                minuteEndIndex = self.__minuteCurrIndexDict[symbol]
            elif mode == 2:
                # Historical
                minuteStartIndex = self.__minuteStartIndexAllDict[symbol][startDate]
                minuteEndIndex = self.__minuteStartIndexDict[symbol]
            else:
                raise Exception("Unexpected mode for getLastNMinuteDataForStockGroup")

            minuteData = minuteDataAll[symbol]

            if n is not None:
                minuteStartIndex = max(minuteEndIndex - n, minuteStartIndex)

            res = minuteData[minuteStartIndex:minuteEndIndex, minuteColumnIndexDict[field]]
            minuteDataList.append(res)

        return np.stack(self.__alignNdArrayList(minuteDataList), axis=1) if isStacked else minuteDataList

    def getLastNHistoricalDailyData(self, field, startDate, stock, splitAdjusted, n=None):
        if stock in self.__stockSet:
            splitAdjusted = False

        dailyData, dailyColumnIndexDict = self.__getDailyData(splitAdjusted, stock)

        dailyStartIndex = self.__dailyStartIndexAllDict[stock][startDate]
        dailyEndIndex = self.__dailyStartIndexDict[stock]

        if n is not None:
            dailyStartIndex = max(dailyEndIndex - n, dailyStartIndex)

        return dailyData[dailyStartIndex:dailyEndIndex, dailyColumnIndexDict[field]]

    def getLastNHistoricalDailyDataForStockGroup(self, field, startDate, stockList, splitAdjusted, isStacked, n=None):
        splitAdjusted = False

        dailyDataAll, dailyColumnIndexDict = self.__getDailyData(splitAdjusted, isGetAll=True)

        dailyDataList = []
        for symbol in stockList:
            dailyStartIndex = self.__dailyStartIndexAllDict[symbol][startDate]
            dailyEndIndex = self.__dailyStartIndexDict[symbol]

            dailyData = dailyDataAll[symbol]

            if n is not None:
                dailyStartIndex = max(dailyEndIndex - n, dailyStartIndex)

            res = dailyData[dailyStartIndex:dailyEndIndex, dailyColumnIndexDict[field]]
            dailyDataList.append(res)

        return np.stack(self.__alignNdArrayList(dailyDataList), axis=1) if isStacked else dailyDataList

    def __getTickData(self, field, splitAdjusted, stock=None, isGetAll=False):
        if stock in self.__indexSet:
            return self.__tickData1[stock], self.__tickColumnIndexDictIndex
        elif stock in self.__UASet:
            if splitAdjusted:
                if field in self.__tickColumnIndexDict1UA:
                    return self.__tickData1SA[stock], self.__tickColumnIndexDict1UA
                else:
                    return self.__tickData2SA[stock], self.__tickColumnIndexDict2UA
            else:
                if field in self.__tickColumnIndexDict1UA:
                    return self.__tickData1[stock], self.__tickColumnIndexDict1UA
                else:
                    return self.__tickData2[stock], self.__tickColumnIndexDict2UA
        else:
            if splitAdjusted:
                if field in self.__tickColumnIndexDict1:
                    if isGetAll:
                        return self.__tickData1SA, self.__tickColumnIndexDict1, np.nan
                    else:
                        return self.__tickData1SA[stock], self.__tickColumnIndexDict1
                else:
                    if isGetAll:
                        return self.__tickData2SA, self.__tickColumnIndexDict2, None
                    else:
                        return self.__tickData2SA[stock], self.__tickColumnIndexDict2
            else:
                if field in self.__tickColumnIndexDict1:
                    if isGetAll:
                        return self.__tickData1, self.__tickColumnIndexDict1, np.nan
                    else:
                        return self.__tickData1[stock], self.__tickColumnIndexDict1
                else:
                    if isGetAll:
                        return self.__tickData2, self.__tickColumnIndexDict2, None
                    else:
                        return self.__tickData2[stock], self.__tickColumnIndexDict2

    def __getMinuteData(self, splitAdjusted, stock=None, isGetAll=False):
        if stock in self.__indexSet:
            return self.__minuteData[stock], self.__minuteColumnIndexDictIndex
        elif stock in self.__UASet:
            if splitAdjusted:
                return self.__minuteDataSA[stock], self.__minuteColumnIndexDictUA
            else:
                return self.__minuteData[stock], self.__minuteColumnIndexDictUA
        else:
            if splitAdjusted:
                if isGetAll:
                    return self.__minuteDataSA, self.__minuteColumnIndexDict
                else:
                    return self.__minuteDataSA[stock], self.__minuteColumnIndexDict
            else:
                if isGetAll:
                    return self.__minuteData, self.__minuteColumnIndexDict
                else:
                    return self.__minuteData[stock], self.__minuteColumnIndexDict

    def __getDailyData(self, splitAdjusted, stock=None, isGetAll=False):
        if stock in self.__indexSet:
            return self.__dailyData[stock], self.__dailyColumnIndexDictIndex
        elif stock in self.__UASet:
            if splitAdjusted:
                return self.__dailyDataSA[stock], self.__dailyColumnIndexDictUA
            else:
                return self.__dailyData[stock], self.__dailyColumnIndexDictUA
        else:
            if splitAdjusted:
                if isGetAll:
                    return self.__dailyDataSA, self.__dailyColumnIndexDict
                else:
                    return self.__dailyDataSA[stock], self.__dailyColumnIndexDict
            else:
                if isGetAll:
                    return self.__dailyData, self.__dailyColumnIndexDict
                else:
                    return self.__dailyData[stock], self.__dailyColumnIndexDict

    @staticmethod
    def __alignNdArrayList(dataList, fillValue=np.nan):
        dataLengthList = [res.shape[0] for res in dataList]
        maxLength = max(dataLengthList)
        minLength = min(dataLengthList)
        if minLength < maxLength:
            dataList = [np.concatenate([[fillValue] * (maxLength - res.shape[0]), res], axis=0) for res in dataList]

        return dataList

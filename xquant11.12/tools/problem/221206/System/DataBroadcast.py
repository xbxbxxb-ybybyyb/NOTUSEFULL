# -*- coding: utf-8 -*-
"""
Updated on 2018/5/25 10:28 --  将数据源由ReadDataFile（来自存为.mat文件的宏汇tdb行情）改为GetXQuantData2（来自mdp接口提供的存在HDFS上的行情）
将这个文件复制到XQuant工程的System下，覆盖DataBroadcast.py即可
Updated on 2018/7/11 15:50 by 006566-- 新增对逐笔成交数据的支持
Updated on 2018/7/16 by 010022 & 006566-- 改造以支持取跨日数据+并行化运算
Updated on 2018/8/9  修正了取逐笔成交数据时，原前闭后闭的问题，现改为前闭后开
Updated on 2018/10/13 原放弃了第1个tick的逐笔成交信息，现补加进来
Updated on 2018/10/14 计算tick因子去除了13:00:00-13:00:15期间的tick行情，计算逐笔成交因子时则不会去除这期间的逐笔成交行情
"""
from System.SliceData import SliceData
from System import GetXQuantData2
import datetime as dt
from System.RemotePrint import print as rp


# from System import ReadDataFile


class DataBroadcast:
    """
    该类用于存储准备单个计算任务的数据，即1个Strategy中的1个股票组（加上factorUnderlyingCode）在被切分后的若干天的数据
    """

    def __init__(self):
        # 该成员和Strategy中的对应成员不一样，这里是单层list，即Strategy中的tradingUnderlyingCode的1个子项
        self.__tradingUnderlyingCode = []
        self.__factorUnderlyingCode = []
        self.__startDateTime = None  # 和Strategy中的startDateTime一致（但已转为datetime）
        self.__endDateTime = None  # 和Strategy中的endDateTime一致（但已转为datetime）
        self.__tradingDays = None  # 切分后的日期list
        self.__dictData = None
        self.__prepareData = None
        self.__iterList = []
        self.__indexForPrepare = []

    def getTradingUnderlyingCode(self):
        return self.__tradingUnderlyingCode

    def getFactorUnderlyingCode(self):
        return self.__factorUnderlyingCode

    def getStartDateTime(self):
        return self.__startDateTime

    def getEndDateTime(self):
        return self.__endDateTime

    def getTradingDays(self):
        return self.__tradingDays

    def getDictData(self):
        return self.__dictData

    def getLenForLoop(self):
        """
        和单机版本不同，这里返回的不是二元组，而是包含的天数
        """
        return self.__tradingDays.__len__()

    def setTradingUnderlyingCode(self, tradingUnderlyingCode):
        self.__tradingUnderlyingCode = tradingUnderlyingCode

    def setFactorUnderlyingCode(self, factorUnderlyingCode):
        self.__factorUnderlyingCode = factorUnderlyingCode

    def setStartDateTime(self, startDateTime):
        self.__startDateTime = startDateTime

    def setEndDateTime(self, endDateTime):
        self.__endDateTime = endDateTime

    def setTradingDays(self, tradingDays):
        self.__tradingDays = tradingDays

    def loadData(self, dfs, srcDir):
        dictKey = list(set(self.__tradingUnderlyingCode + self.__factorUnderlyingCode))

        self.__dictData = {}
        for i in range(len(dictKey)):  # 根据并行化项目的改造，这里dictKey长度为1，亦即只有1只股票
            emptyList = []
            for j in range(len(self.__tradingDays)):
                emptyList.append([])
            self.__dictData.update({dictKey[i]: emptyList[:]})

        for iDictKey in dictKey:
            iDictStockData = []
            iDictTransactionData = []
            start_date = self.__tradingDays[0]
            end_date = self.__tradingDays[-1]
            for day in self.__tradingDays:
                startDate2 = day  # 根据并行化项目的改造，这里self.__tradingDays只有1天
                endDate2 = day  # 所以self.__tradingDays[0]和self.__tradingDays[-1]其实是同一天
                startDateTime2 = dt.datetime(startDate2.year, startDate2.month, startDate2.day,
                                             self.__startDateTime.hour, self.__startDateTime.minute,
                                             self.__startDateTime.second)
                endDateTime2 = dt.datetime(endDate2.year, endDate2.month, endDate2.day, self.__endDateTime.hour,
                                           self.__endDateTime.minute, self.__endDateTime.second)
                try:
                    # iDictStockData = ReadDataFile.getData(dfs, srcDir, iDictKey, self.__startDateTime, self.__endDateTime, self.__tradingDays)
                    temp_DictStockData = GetXQuantData2.getXQuantTickData2(
                        iDictKey,
                        startDateTime2,
                        endDateTime2,
                        timeMode=3,
                        tradingPhaseCode=["0", "1", "2", "3", "4", "5", "6", "7"]
                    )
                # 获得iDict这只股票（或指数）指定时间段内连续竞价期间的数据
                # iDictStockData是一个list, 长度等于交易日的天数（在此就是1），list中的每个元素即是每个交易日的数据，每个元素的类型都为字典
                except:
                    temp_DictStockData = [None]

                try:
                    temp_DictTransactionData = GetXQuantData2.getXQuantTransactionData2(
                        iDictKey,
                        startDateTime2,
                        endDateTime2,
                        cancellationFilter=True,
                        testMode=True,
                        timeMode=3
                    )
                except:
                    temp_DictTransactionData = [None]

                if temp_DictStockData[0] is None:
                    rp(iDictKey, day, "No Tick Data")
                if temp_DictTransactionData[0] is None:
                    rp(iDictKey, day, "No Transaction Data")

                iDictStockData.extend(temp_DictStockData)
                iDictTransactionData.extend(temp_DictTransactionData)

            if (iDictKey[0] == "0" and iDictKey[-1] == "H") or (
                            iDictKey[:2] == "39" and iDictKey[-1] == "Z"):  # 如果是指数，则在指数文件夹下读取文档
                for ii in range(iDictStockData.__len__()):
                    stockData = iDictStockData[ii]  # iDict股票每天的数据
                    if stockData is None:
                        continue
                    for i in range(len(stockData['Price'])):
                        lastPrice = stockData['Price'][i]
                        volume = stockData['Volume'][i]
                        amount = stockData['Turover'][i]
                        totalVolume = stockData['AccVolume'][i]
                        totalAmt = stockData['AccTurover'][i]
                        preClose = stockData['PreClose'][i]
                        timeStamp = stockData['TimeStamp'][i]
                        time = stockData['Time'][i]
                        # 如果是指数，则4个盘口数据的信息都为None
                        sliceData = SliceData(iDictKey, timeStamp, time, None, None, None, None, lastPrice, volume,
                                              amount, totalVolume, totalAmt, preClose, None, None)
                        self.__dictData[iDictKey][ii].append(sliceData)

            else:  # 如果是股票
                for ii in range(iDictStockData.__len__()):
                    stockData = iDictStockData[ii]  # iDict股票每天的数据
                    stockTransactionData = iDictTransactionData[ii]  # iDict股票当天的逐笔成交数据
                    if stockData is None or stockTransactionData is None:
                        continue
                    lastTimeStampIdxTran = 0  # Tick行情中上个切片的时间戳在Transaction的时间戳中的位置（索引）
                    tick_count_afternoon_beginning = 0
                    for i in range(len(stockData['BidP1'])):
                        # if 130000000 <= stockData['Time'][i] < 130015000:
                        #     tick_count_afternoon_beginning += 1
                        #     continue
                        bidPrice = [stockData['BidP1'][i], stockData['BidP2'][i], stockData['BidP3'][i],
                                    stockData['BidP4'][i], stockData['BidP5'][i], stockData['BidP6'][i],
                                    stockData['BidP7'][i], stockData['BidP8'][i], stockData['BidP9'][i],
                                    stockData['BidP10'][i]]
                        askPrice = [stockData['AskP1'][i], stockData['AskP2'][i], stockData['AskP3'][i],
                                    stockData['AskP4'][i], stockData['AskP5'][i], stockData['AskP6'][i],
                                    stockData['AskP7'][i], stockData['AskP8'][i], stockData['AskP9'][i],
                                    stockData['AskP10'][i]]
                        bidVolume = [stockData['BidV1'][i], stockData['BidV2'][i], stockData['BidV3'][i],
                                     stockData['BidV4'][i], stockData['BidV5'][i], stockData['BidV6'][i],
                                     stockData['BidV7'][i], stockData['BidV8'][i], stockData['BidV9'][i],
                                     stockData['BidV10'][i]]
                        askVolume = [stockData['AskV1'][i], stockData['AskV2'][i], stockData['AskV3'][i],
                                     stockData['AskV4'][i], stockData['AskV5'][i], stockData['AskV6'][i],
                                     stockData['AskV7'][i], stockData['AskV8'][i], stockData['AskV9'][i],
                                     stockData['AskV10'][i]]
                        lastPrice = stockData['Price'][i]
                        volume = stockData['Volume'][i]
                        amount = stockData['Turover'][i]
                        totalVolume = stockData['AccVolume'][i]
                        totalAmt = stockData['AccTurover'][i]
                        preClose = stockData['PreClose'][i]
                        timeStamp = stockData['TimeStamp'][i]
                        time = stockData['Time'][i]
                        if i > 0:   # 如果不是第1条tick记录
                            # 获取上个tick/slice的TimeStamp；注意下午13:00:00-13:00:15的tick被略过、但逐笔成交要包括进来
                            timeStampOfLastTick = stockData['TimeStamp'][i - 1 - tick_count_afternoon_beginning]
                            tick_count_afternoon_beginning = 0
                        else:
                            timeStampOfLastTick = dt.datetime.strptime(str(self.__tradingDays[ii]), "%Y-%m-%d").timestamp()
                        while (lastTimeStampIdxTran < stockTransactionData['TimeStamp'].__len__()
                               and stockTransactionData['TimeStamp'][lastTimeStampIdxTran] < timeStampOfLastTick):
                            lastTimeStampIdxTran += 1
                        currentTimeStampIdxTran = lastTimeStampIdxTran
                        # currentTimeStampIdxTran是Tick行情中本切片的时间戳在Transaction的时间戳中的位置（索引）
                        while (currentTimeStampIdxTran < stockTransactionData['TimeStamp'].__len__()
                               and stockTransactionData['TimeStamp'][currentTimeStampIdxTran] < timeStamp):
                            currentTimeStampIdxTran += 1
                        transactionData = [
                            stockTransactionData['AskOrder'][lastTimeStampIdxTran: currentTimeStampIdxTran],
                            stockTransactionData['BidOrder'][lastTimeStampIdxTran: currentTimeStampIdxTran],
                            stockTransactionData['BSFlag'][lastTimeStampIdxTran: currentTimeStampIdxTran],
                            stockTransactionData['Price'][lastTimeStampIdxTran: currentTimeStampIdxTran],
                            stockTransactionData['Volume'][lastTimeStampIdxTran: currentTimeStampIdxTran]]
                        # 数据转置
                        transactionData = [[row[i] for row in transactionData] for i in
                                           range(len(transactionData[0]))]
                        transactionTimeStamp = stockTransactionData['TimeStamp'][lastTimeStampIdxTran:
                                               currentTimeStampIdxTran]
                        sliceData = SliceData(iDictKey, timeStamp, time, bidPrice, askPrice, bidVolume, askVolume,
                                              lastPrice, volume, amount, totalVolume, totalAmt, preClose,
                                              transactionData, transactionTimeStamp)

                        if (int(self.__startDateTime.strftime("%H%M%S") + "000") <= time < 113000000
                                or 130015000 <= time <= int(self.__endDateTime.strftime("%H%M%S") + "000")):
                            self.__dictData[iDictKey][ii].append(sliceData)

    def getSliceData(self):
        sendSlice = self.__prepareData[self.__indexForPrepare[0]][self.__iterList[0]]
        indexMove = 0
        if len(self.__indexForPrepare) > 1:
            for i in range(len(self.__indexForPrepare)):
                if self.__prepareData[self.__indexForPrepare[i]][self.__iterList[i]].timeStamp < sendSlice.timeStamp:
                    sendSlice = self.__prepareData[self.__indexForPrepare[i]][self.__iterList[i]]
                    indexMove = i
        self.__iterList[indexMove] += 1

        if len(self.__prepareData[self.__indexForPrepare[indexMove]]) <= self.__iterList[indexMove]:
            self.__indexForPrepare.pop(indexMove)
            self.__iterList.pop(indexMove)
        return sendSlice

    def prepareSliceData(self, iDate):
        self.__iterList = []
        dictKey = list(set(self.__tradingUnderlyingCode + self.__factorUnderlyingCode))
        self.__indexForPrepare = list(range(dictKey.__len__()))
        self.__prepareData = []
        sliceNum = 0
        for i in range(len(dictKey)):
            self.__prepareData.append(self.__dictData[dictKey[i]][iDate])
            self.__iterList.append(0)
            if len(self.__dictData[dictKey[i]][iDate]) != 0:
                sliceNum = sliceNum + len(self.__dictData[dictKey[i]][iDate])
            else:
                sliceNum = 0  # 只要当天组内有一只股票停牌，那么令sliceNum=0，并结束循环，返回0
                break
        return sliceNum
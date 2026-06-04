#-*- coding:utf-8 -*-
# author: 015629
# datetime:2022/1/25 16:22
# -*- coding: utf-8 -*-
import os
import numpy as np
import datetime as dt
import pandas as pd
from DataAPI.TradingDay import trading_day
from xquant.factordata import FactorData
from xquant.marketdata import MarketData
from xquant.compute.sparkmr import remote_print


def load_l2p_tick_data(hbase_library, code, date):
    """"""
    TICK_SUFFIX = "T"
    ALIGN_TICK_COLUMNS = ["Code", "Timestamp", "Date", "Time", "PreviousClose", "OpenPrice", "HighPrice", "LowPrice", "MaxPrice", "MinPrice", "LastPrice",
                          "Volume", "Amount", "TotalVolume", "TotalAmount", "BidPrice", "AskPrice", "BidVolume", "AskVolume"]
    TICK_HBASE_COLUMNS = list(map(lambda x: "{0}_{1}".format(TICK_SUFFIX, x), ALIGN_TICK_COLUMNS))
    TICK_TARGET_COLUMNS = ["Code", "Date", "Time", "Timestamp", "PreviousClose", "OpenPrice", "HighPrice", "LowPrice",
                           "MaxPrice", "MinPrice", "LastPrice", "TotalVolume", "TotalAmount", "Volume", "Amount",
                           "BidP1", "BidP2", "BidP3", "BidP4", "BidP5", "BidP6", "BidP7", "BidP8", "BidP9", "BidP10",
                           "AskP1", "AskP2", "AskP3", "AskP4", "AskP5", "AskP6", "AskP7", "AskP8", "AskP9", "AskP10",
                           "BidV1", "BidV2", "BidV3", "BidV4", "BidV5", "BidV6", "BidV7", "BidV8", "BidV9", "BidV10",
                           "AskV1", "AskV2", "AskV3", "AskV4", "AskV5", "AskV6", "AskV7", "AskV8", "AskV9", "AskV10"
                           ]
    TICK_COLUMN_RENAME = {"PreviousClose": "PreClose", "TotalVolume": "AccVolume", "TotalAmount": "AccTurover", "LastPrice": "Price",
                          "OpenPrice": "Open", "HighPrice": "High", "LowPrice": "Low", "MaxPrice": "MaxP", "MinPrice": "MinP",
                          "Timestamp": "TimeStamp", "Amount": "Turover"}
    try:
        l2p_tick = FactorData().get_factor_value(hbase_library, code, date, TICK_HBASE_COLUMNS + ["{}_IsMock".format(TICK_SUFFIX)])
        l2p_tick.columns = list(map(lambda x: x.replace("{0}_".format(TICK_SUFFIX), ""), l2p_tick.columns.to_list()))
        l2p_tick = l2p_tick[l2p_tick["IsMock"] == 0].reset_index(drop=True)
        l2p_tick = l2p_tick.reindex(columns=ALIGN_TICK_COLUMNS)
        l2p_tick.columns = ALIGN_TICK_COLUMNS
    except Exception as e:
        MyPrint(" L2P Tick Data Empty: {}-{}-{}-{} ".format(hbase_library, code, date, e))
        l2p_tick = pd.DataFrame(columns=ALIGN_TICK_COLUMNS)

    for level in range(1, 11):
        l2p_tick["AskP{}".format(level)] = l2p_tick["AskPrice"].apply(lambda x: x.tolist()[level - 1]).values
        l2p_tick["AskV{}".format(level)] = l2p_tick["AskVolume"].apply(lambda x: x.tolist()[level - 1]).values
        l2p_tick["BidP{}".format(level)] = l2p_tick["BidPrice"].apply(lambda x: x.tolist()[level - 1]).values
        l2p_tick["BidV{}".format(level)] = l2p_tick["BidVolume"].apply(lambda x: x.tolist()[level - 1]).values

    l2p_tick = l2p_tick.reindex(columns=TICK_TARGET_COLUMNS)
    l2p_tick.columns = TICK_TARGET_COLUMNS
    l2p_tick = l2p_tick.rename(columns=TICK_COLUMN_RENAME)

    return l2p_tick

def getL2PTickData2(stockCode, startDateTime, endDateTime, hbaseLibrary="LiveL2PDataLib"):
    startDate8digit = startDateTime.year * 10000 + startDateTime.month * 100 + startDateTime.day
    endDate8digit = endDateTime.year * 10000 + endDateTime.month * 100 + endDateTime.day
    if endDate8digit < startDate8digit:
        print("Error: the end date", endDate8digit, "is earlier than the start date", startDate8digit)
        return [], []

    dateList = [int(date) for date in trading_day(startDate8digit, endDate8digit)]

    stockData = pd.DataFrame()
    for date in dateList:
        tempStockData = load_l2p_tick_data(hbaseLibrary, stockCode, str(date))
        if tempStockData.__len__() == 0:
            continue
        if stockData.__len__() > 0:
            stockData = stockData.append(tempStockData)
        else:
            stockData = tempStockData.copy()

    if stockData.__len__() == 0:
        return [], []

    stockData['Time'] = stockData['Time'].astype('int32')  # 这里默认Time是obj,转为int以便后续过滤
    stockData['Date'] = stockData['Date'].astype('int32')  # 这里默认Date是obj,转为int以便后续过滤

    stockDataList = df2List(stockData, dateList, stockCode)

    return stockDataList, dateList

def getXQuantTickData2(stockCode, startDateTime, endDateTime, timeMode=2, tradingPhaseCode=[], dfs=None):
    mdp = MarketData(dfs)
    """
    【2018/5/3：注意暂不支持在XQuant的GPU环境运行】
    这个函数实现的功能模仿原 System.ReadDataFile.getData，根据输入的股票代码、开始日期时间、终止日期时间，输出tick数据
    输出的数据的格式是list, 其长度等于开始日期和终止日期之间的交易所日历交易日天数
    输出的list的内容是dict, dict共有52个key，若某天股票停牌，则当天的内容为None
    如timeMode=1，则输出的每天的数据的时间是startDateTime.time()和endDateTime.time()之间的时间；若为2则为每天连续竞价期间的数据
    本函数与GetInsight系列的区别在于，本函数从HDFS读取数据，而GetInsight系列则是从底层Insight行情读取数据，因此本函数速度大幅提升
    本函数返回的格式和内容与原函数是一致的

    tradingPhaseCode默认为["3"]，输出连续竞价期间的数据；"0"-开盘前，"1"-开盘集合竞价
    """
    # XQuant上取tick数据、取到的字段与原数据文件的字段不同，多了一些（后续要删掉），也少了一些（少了3个：成交量Volume、成交额Turover和时间戳TimeStamp），少的要补上
    startDate8digit = startDateTime.year * 10000 + startDateTime.month * 100 + startDateTime.day
    endDate8digit = endDateTime.year * 10000 + endDateTime.month * 100 + endDateTime.day
    if endDate8digit < startDate8digit:
        print("Error: the end date", endDate8digit, "is earlier than the start date", startDate8digit)
        return [], []

    if timeMode == 2:
        tradingPhaseCode = ["3"]  # 如timeMode == 2，则将tradingPhaseCode设为3

    dateList = trading_day(startDate8digit, endDate8digit)

    # 因mdp接口取数据的最大范围是180天，这里通过datesSegment函数将日期切为每170天一段
    startDate = dt.date(int(str(dateList[0])[0:4]), int(str(dateList[0])[4:6]), int(str(dateList[0])[6:8]))
    endDate = dt.date(int(str(dateList[-1])[0:4]), int(str(dateList[-1])[4:6]), int(str(dateList[-1])[6:8]))
    dateList2 = datesSegment(startDate, endDate)  # 将日期分段

    stockData = pd.DataFrame()
    # mdp接口是从存在HDFS上的高频行情（而非Insight底层数据库）提取数据，最后的["3"]表示通过tradingPhaseCode这一字段取连续竞价期间的数据
    # 截至20180503有功能未完成，即上交所股票tick行情若有缺失的、从宏汇tdb提取数据补全，但宏汇tdb的行情没有tradingPhaseCode这一字段，因此上交所的行情可能须另写语句提取
    for iDateList in dateList2:  # 每170天一段取数据，并将分段取得的数据拼接起来
        tempStockData = mdp.get_data_by_time_frame("Stock", stockCode, iDateList[0] + " 000001000",
                                                   iDateList[1] + " 235959000", tradingPhaseCode)
        if tempStockData.__len__() == 0:
            continue
        tempStockData = tempStockData.replace({'PreClosePx': 0.0}, np.nan)  # 如遇PreClose为0的，以前值填充之
        tempStockData = tempStockData.fillna(method='ffill')

        tempStockData = tickDataKeepUsefulColumns(tempStockData)  # 仅保留有用的列，并对列进行改名
        tempStockData = tickDataOHLFilter(tempStockData)  # 若连续竞价期间Open, High, Low有0，则删除之
        tempStockData = tickDataAppendVolumeNTurover(tempStockData)  # 新增成交量和成交额列
        if stockData.__len__() > 0:
            stockData = stockData.append(tempStockData)
        else:
            stockData = tempStockData.copy()

    if stockData.__len__() == 0:  # 如无数据，则直接返回None
        return [], []

    stockData = appendTimeStamp(stockData)  # 添加TimeStamp字段

    stockData['Time'] = stockData['Time'].astype('int32')  # 这里默认Time是obj,转为int以便后续过滤
    stockData['Date'] = stockData['Date'].astype('int32')  # 这里默认Date是obj,转为int以便后续过滤

    startTime8digit = startDateTime.hour * 10000000 + startDateTime.minute * 100000 + startDateTime.second * 1000
    endTime8digit = endDateTime.hour * 10000000 + endDateTime.minute * 100000 + endDateTime.second * 1000
    if timeMode == 1:  # 如timeMode=1，则输出的每天的数据的时间是startDateTime.time()和endDateTime.time()之间的时间
        if stockCode[-1] == 'H':  # 上交所的股票或指数
            timeFilter = (startTime8digit <= stockData['Time']) & (stockData['Time'] <= endTime8digit)
        else:  # 深交所的股票或指数
            timeFilter = (startTime8digit <= stockData['Time']) & (stockData['Time'] <= endTime8digit)
        stockData = stockData[timeFilter]

    # 过滤中午期间的行情
    # timeFilter = (stockData['Time'] < 113000000) | (stockData['Time'] >= 130000000)
    # stockData = stockData[timeFilter]

    # 将stockData由DataFrame转化为List, 该List的长度等于开始日期和终止日期之间的交易所日历交易日天数；list的内容每天的数据，格式是list
    stockDataList = df2List(stockData, dateList, stockCode)

    return stockDataList, dateList


def getXQuantTransactionData2(stockCode, startDateTime, endDateTime, cancellationFilter=True, testMode=False,
                              timeMode=1, dfs=None):
    mdp = MarketData(dfs)
    """
    【2018/5/3：注意暂不支持在XQuant的GPU环境运行】
    函数实现的功能类似原ReadDataFile.getTransactiondata，根据输入的股票代码、开始日期时间、终止日期时间，输出逐笔成交数据
    输出的数据的格式是list, 其长度等于开始日期和终止日期之间的交易所日历交易日天数
    输出的list的内容是dict, dict共有9个key: ['Date', 'Time', 'BidOrder', 'AskOrder', 'TradeType', 'BSFlag', 'Price', 'Volume', 'TimeStamp']
    若某天股票停牌，则list当天的内容为None
    cancellationFilter默认=True，则所有撤单的信息不会输出
    【注意！】这里取到的数据和原Project最大的区别在于，原存在S盘的数据的BSFlag中，1是买、-1是卖；而insight行情（同实盘行情）1是买，2是卖
    testMode默认=False, 如为True的话，则BSFlag改为1是买、-1是卖（同原存在S盘的数据）；这一改动未来将删除
    timeMode默认=1，则输出的每天的数据的时间是startDateTime.time()和endDateTime.time()之间的时间，但其实对于逐笔成交而言，这一过滤意义不大
    """
    startDate8digit = startDateTime.year * 10000 + startDateTime.month * 100 + startDateTime.day
    endDate8digit = endDateTime.year * 10000 + endDateTime.month * 100 + endDateTime.day
    if endDate8digit < startDate8digit:
        print("Error: the end date", endDate8digit, "is earlier than the start date", startDate8digit)
        return [], []

    dateList = trading_day(startDate8digit, endDate8digit)

    # 因mdp接口取数据的最大范围是180天，这里通过datesSegment函数将日期切为每170天一段
    startDate = dt.date(int(str(dateList[0])[0:4]), int(str(dateList[0])[4:6]), int(str(dateList[0])[6:8]))
    endDate = dt.date(int(str(dateList[-1])[0:4]), int(str(dateList[-1])[4:6]), int(str(dateList[-1])[6:8]))
    dateList2 = datesSegment(startDate, endDate)  # 将日期分段

    stockData = pd.DataFrame()
    for iDateList in dateList2:  # 每170天一段取数据，并将分段取得的数据拼接起来
        tempStockData = mdp.get_data_by_time_frame("Transaction", stockCode, iDateList[0] + " 000001000", iDateList[1] + " 235959000")
        if tempStockData.__len__() == 0:
            continue
        tempStockData = transactionKeepUsefulColumns(tempStockData)  # 仅保留有用的列，并对列进行改名
        tempStockData = appendTimeStamp(tempStockData)  # 添加TimeStamp字段
        if stockData.__len__() > 0:
            stockData = stockData.append(tempStockData)
        else:
            stockData = tempStockData.copy()

    if stockData.__len__() == 0:  # 如无数据，则直接返回None
        return [], []

    if timeMode == 1:  # 如timeMode=1，则输出的每天的数据的时间是startDateTime.time()和endDateTime.time()之间的时间
        stockData['Time'] = stockData['Time'].astype('int32')  # 这里默认Time是obj,转为int以便后续过滤
        stockData['Date'] = stockData['Date'].astype('int32')  # 这里默认Date是obj,转为int以便后续过滤
        startTime8digit = startDateTime.hour * 10000000 + startDateTime.minute * 100000 + startDateTime.second * 1000
        endTime8digit = endDateTime.hour * 10000000 + endDateTime.minute * 100000 + endDateTime.second * 1000
        timeFilter = ((stockData['Time'] >= startTime8digit) & (stockData['Time'] < endTime8digit))  # 逐笔成交不用过滤中午
        stockData = stockData[timeFilter]

    stockData['Time'] = stockData['Time'].astype('int32')  # 这里默认Time是obj,转为int以便后续过滤
    stockData['Date'] = stockData['Date'].astype('int32')  # 这里默认Date是obj,转为int以便后续过滤

    if cancellationFilter:
        stockData = stockData[stockData['TradeType'] == 0]  # 只保留成交的数据，删除撤单的数据，这种改动是为了迎合原S盘的数据格式

    # 若testMode为True，则将主卖的标志替换为-1，这种改动是为了迎合原S盘的数据格式；注意原insight行情及实盘中主卖是的标志都是2
    if testMode:
        stockData.loc[stockData['BSFlag'] == 2, 'BSFlag'] = -1

    # 将stockData由DataFrame转化为List, 该List的长度等于开始日期和终止日期之间的交易所日历交易日天数；list的内容每天的数据，格式是list
    stockDataList = df2List(stockData, dateList, stockCode)

    return stockDataList, dateList


def datesSegment(startDate, endDate):
    # 因为取XQuant的MDP接口所能取的最大时间跨度是180天，若原函数输入的日期跨度较大，则需拆分为多段分别获取数据
    # 本函数将起止日期的拆分为每170天一组
    # 虽然输入的类型是dt.date，但为了后续使用方便，输出的最小元素转为8位数字的字符串
    daysDiff = (endDate - startDate).days
    if divmod(daysDiff, 170)[1] > 0 or daysDiff == 0:
        datesPeriod = divmod(daysDiff, 170)[0] + 1
    else:
        datesPeriod = divmod(daysDiff, 170)[0]
    if datesPeriod == 1:
        startEndDatesList = [[startDate, endDate]]
    else:
        startEndDatesList = [None for _ in range(datesPeriod)]
        for i in range(datesPeriod - 1):
            startEndDatesList[i] = [startDate, startDate + dt.timedelta(170)]
            startDate = startDate + dt.timedelta(171)
        startEndDatesList[-1] = [startDate, endDate]
    # 截至到此，startEndDatesList的最小元素全部是dt.date类型，以下转化为8位数字的字符串，例如'20180101'
    startEndDatesList2 = [None for _ in range(datesPeriod)]
    for iPeriod in range(startEndDatesList.__len__()):
        startEndDatesList2[iPeriod] = [str(iDate.year * 10000 + iDate.month * 100 + iDate.day) for iDate in
                                       startEndDatesList[iPeriod]]
    return startEndDatesList2

def tickDataAppendVolumeNTurover(df):
    """
    这个函数处理的情况：从XQuant接口的mdp读取了跨日的Tick数据（格式为DataFrame），但数据中没有成交量和成交额字段，且数据索引不连续
    函数的功能1：通过累计成交额和累计成交量的差分，算出成交量和成交额；另外每日第1行的成交额、成交量直接用累计成交额、累计成交量代替
    函数的功能2：重建索引，将索引变为连续的
    函数最后仍返回DataFrame格式的数据
    """
    df = df.copy()
    df['Date2'] = df['Date'].astype('int32')  # 将日期转为int，以便后续计算
    dateList = np.array(df['Date2'])
    del df['Date2']
    dateListDiff = np.diff(dateList)  # 对日期进行差分
    dateListDiffLogic = dateListDiff != 0
    changeDayInx = np.argwhere(dateListDiffLogic)  # 若为True，则表示这行到了新的一天；找到行号
    changeDayInx = (changeDayInx + 1).tolist()  # 差分后会少一行，所以行号需要+1
    changeDayInx = [y for x in changeDayInx for y in x]  # np.argwhere会给结果带上[]，把括号去掉
    changeDayInx.insert(0, 0)  # 第1天的第1行也必然因为差分而丢失了，需补上
    df = df.reset_index(drop=True)  # 需要重塑index，因为从XQuant取到的原始行情，索引不是连续的（因为只取了连续竞价期间数据）
    df['Volume'] = df['AccVolume'].diff()
    df['Turover'] = df['AccTurover'].diff()
    df['Volume'] = df['Volume'].clip_lower(0)  # 如遇负数，改为0
    df['Turover'] = df['Turover'].clip_lower(0)
    for i in changeDayInx:
        df.loc[i, 'Volume'] = df.loc[i, 'AccVolume']
        df.loc[i, 'Turover'] = df.loc[i, 'AccTurover']
    return df

def tickDataKeepUsefulColumns(df):
    # 本函数保留Tick数据中符合原模型框架的部分字段（即删去部分字段）；并将字段名改为符合原模型框架的字段名
    df2 = df[['MDDate', 'MDTime', 'TradingPhaseCode', 'PreClosePx', 'TotalVolumeTrade', 'TotalValueTrade', 'LastPx',
              'OpenPx', 'HighPx', 'LowPx', 'MaxPx', 'MinPx', 'HTSCSecurityID', 'Buy1Price', 'Buy1OrderQty',
              'Sell1Price', 'Sell1OrderQty', 'Buy2Price', 'Buy2OrderQty', 'Sell2Price', 'Sell2OrderQty', 'Buy3Price',
              'Buy3OrderQty', 'Sell3Price', 'Sell3OrderQty', 'Buy4Price', 'Buy4OrderQty', 'Sell4Price', 'Sell4OrderQty',
              'Buy5Price', 'Buy5OrderQty', 'Sell5Price', 'Sell5OrderQty', 'Buy6Price', 'Buy6OrderQty', 'Sell6Price',
              'Sell6OrderQty', 'Buy7Price', 'Buy7OrderQty', 'Sell7Price', 'Sell7OrderQty', 'Buy8Price', 'Buy8OrderQty',
              'Sell8Price', 'Sell8OrderQty', 'Buy9Price', 'Buy9OrderQty', 'Sell9Price', 'Sell9OrderQty', 'Buy10Price',
              'Buy10OrderQty', 'Sell10Price', 'Sell10OrderQty']].copy()
    df2.columns = ['Date', 'Time', 'TradingPhaseCode', 'PreClose', 'AccVolume', 'AccTurover', 'Price', 'Open', 'High',
                   'Low', 'MaxP', 'MinP', 'Code', 'BidP1', 'BidV1', 'AskP1', 'AskV1', 'BidP2', 'BidV2', 'AskP2',
                   'AskV2', 'BidP3', 'BidV3', 'AskP3', 'AskV3', 'BidP4', 'BidV4', 'AskP4', 'AskV4', 'BidP5', 'BidV5',
                   'AskP5', 'AskV5', 'BidP6', 'BidV6', 'AskP6', 'AskV6', 'BidP7', 'BidV7', 'AskP7', 'AskV7', 'BidP8',
                   'BidV8', 'AskP8', 'AskV8', 'BidP9', 'BidV9', 'AskP9', 'AskV9', 'BidP10', 'BidV10', 'AskP10',
                   'AskV10']
    return df2

def transactionKeepUsefulColumns(df):
    # 本函数保留逐笔成交数据中符合原模型框架的部分字段（即删去部分字段）；并将字段名改为符合原模型框架的字段名
    df2 = df[['MDDate', 'MDTime', 'TradeBuyNo', 'TradeSellNo', 'TradeType', 'TradeBSFlag', 'TradePrice', 'TradeQty',
              'HTSCSecurityID']].copy()
    df2.columns = ['Date', 'Time', 'BidOrder', 'AskOrder', 'TradeType', 'BSFlag', 'Price', 'Volume', 'Code']
    return df2

def appendTimeStamp(df):
    # 本函数给DataFrame结构新增TimeStamp字段，可在提取tick, transaction和order时重复使用
    df['DateTime'] = df['Date'] + df['Time']  # 将字符串相连
    df['DateTime'] = pd.to_datetime(df['DateTime'], format='%Y%m%d%H%M%S%f')  # 将字符串的日期时间转为datetime类型
    df['TimeStamp'] = (df['DateTime'] - dt.datetime(1970, 1, 1)).dt.total_seconds() - 28800  # 计算TimeStamp并保存为float格式
    del df['DateTime']
    return df

def df2List(stockDataDf, dateList, stockCode):
    # 本函数将DataFrame结构转化为List结构，将DataFrame的内容逐日拆分放进List，如当日内容为空的则List的对应位置是None
    # List中每日的数据的格式是Dict, 原DataFrame的Column是Dict的Key
    stockData2List = [None for _ in range(dateList.__len__())]  # 每一个交易日都先用None填充占位
    for iTradeDate in range(dateList.__len__()):
        tempStockData = stockDataDf[stockDataDf['Date'] == dateList[iTradeDate]]
        if len(tempStockData) == 0:  # 如全天tick数量为0，则跳过；那么当天的值就是None
            print(stockCode, dateList[iTradeDate], "No Data")
            continue
        tempStockData2 = {}
        for column in tempStockData:
            tempStockData2[column] = tempStockData[column].tolist()
        stockData2List[iTradeDate] = tempStockData2
    return stockData2List

def tickDataOHLFilter(stockDataDf):
    # 本函数将连续竞价期间Open, High和Low为0的条目删掉
    stockDataDf2 = stockDataDf[((True ^ stockDataDf['Open'].isin([0])) & (True ^ stockDataDf['High'].isin([0])) &
                                (True ^ stockDataDf['Low'].isin([0])))].copy()
    return stockDataDf2


def MyPrint(x_str):
    if "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ:
        return remote_print(x_str)
    else:
        return print(x_str)

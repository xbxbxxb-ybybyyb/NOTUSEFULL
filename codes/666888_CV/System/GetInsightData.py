"""
Created on 2018/4/27 9:19
Updated on 2018/5/2 17:51 -- 给getInsightTickData和getInsightTransactionData都强行加入一行命令，按TimeStamp升序排列
Updated on 2018/5/4 14:38 -- 将'Date'和'Time'字段都转为int，以保持和原系统一致
Updated on 2018/5/8 14:46 -- 1) 修正了取停牌期间tick数据会报错的问题；2) 如某日的tick数据直到末尾的AccVolume都等于0，
                            则当天视为停牌，输出None；3) 过滤下午14:56:57之后的数据
Updated on 2018/5/8 20:17 -- 为Tick数据保留涨停价（MaxP）和跌停价（MinP）字段
@author: 006566
"""
from xquant.marketdata import MarketData
import datetime as dt
from xquant import quant
import pandas as pd
import numpy as np
ma = MarketData()


def getInsightTickData(stockCode, startDateTime, endDateTime, timeMode=1):
    """
    这个函数实现的功能模仿原 System.ReadDataFile.getData，根据输入的股票代码、开始日期时间、终止日期时间，输出tick数据

    输出的数据的格式是list, 其长度等于开始日期和终止日期之间的交易所日历交易日天数
    输出的list的内容是dict, dict共有52个key，若某天股票停牌，则当天的内容为None
    timeMode默认=1，则输出的每天的数据的时间是startDateTime.time()和endDateTime.time()之间的时间；否则为每天093000到145659之间的数据

    和原函数不同的地方在于，原函数是从我们保存好的数据文件中读取数据，本函数是根据xquant的接口获取数据；本函数目前获取数据的速度比较慢，【请忍耐】
    本函数返回的格式和内容与原函数是一致的
    """
    # XQuant上取tick数据只能每日取，取到的字段与原数据文件的字段不同，多了一些（后续要删掉），也少了一些（少了3个：成交量Volume、成交额Turover和时间戳TimeStamp），少的要补上
    startDate8digit = startDateTime.year * 10000 + startDateTime.month * 100 + startDateTime.day
    endDate8digit = endDateTime.year * 10000 + endDateTime.month * 100 + endDateTime.day
    startTime6digit = str(startDateTime.hour * 10000 + startDateTime.minute * 100 + startDateTime.second)
    if startTime6digit.__len__() < 6:  # 如开始时间是上午9:30:01，不足6位需补齐
        startTime6digit = '0' + startTime6digit
    endDate6digit = str(endDateTime.hour * 10000 + endDateTime.minute * 100 + endDateTime.second)
    if endDate6digit.__len__() < 6:
        endDate6digit = '0' + endDate6digit

    # 用xquant的api取交易日日期, 得到的是格式如[20180319, 20180320, 20180321]的数据
    dateList = quant.tradingDay(startDate8digit, endDate8digit)
    # 生成类似这样的list —— [['20180320093000', '20180320145659'], ['20180321093000', '20180321145659']]
    if timeMode == 1:
        dateTimeStr = [[str(iDate) + str(startTime6digit), str(iDate) + str(endDate6digit)] for iDate in dateList]
    else:
        dateTimeStr = [[str(iDate) + '093000', str(iDate) + '145657'] for iDate in dateList]

    stockData = pd.DataFrame()
    for iDateTime in dateTimeStr:
        # 获取当日的tick数据
        df = ma.getMDSecurityTickDataFrame(stockCode, iDateTime[0], iDateTime[1], 1)
        if df.__len__() > 0:
            # insight行情中原没有成交量和成交额的字段，这里做一个差分
            df['Volume'] = df['TotalVolumeTrade'].diff()
            df['Turover'] = df['TotalValueTrade'].diff()
            # 对于差分得到的首行（NaN），需填充
            df.loc[0, 'Volume'] = df['TotalVolumeTrade'][0]
            df.loc[0, 'Turover'] = df['TotalValueTrade'][0]
            df['DateTime'] = df['MDDate'] + df['MDTime']  # 将字符串相连
        else:  # 如当天无行情，则跳过
            continue
        # 将每日的数据堆叠起来（因为目前只能逐日取数据）
        if stockData.__len__() > 0:
            stockData = stockData.append(df)
        else:
            stockData = df.copy()

    # 将insight的原始字段名改为原project的字段名
    stockData.columns = ['Date', 'Time', 'SecurityType', 'PreClose', 'NumTrades', 'AccVolume', 'AccTurover', 'Price', 'Open', 'High', 'Low',
                         'MaxP', 'MinP', 'Code', 'WeightedAvgBidPx', 'WeightedAvgOfferPx', 'TotalBidNumber', 'TotalOfferNumber', 'BidP1', 'BidV1', 'AskP1', 'AskV1',
                         'BidP2', 'BidV2', 'AskP2', 'AskV2', 'BidP3', 'BidV3', 'AskP3', 'AskV3', 'BidP4', 'BidV4', 'AskP4', 'AskV4', 'BidP5', 'BidV5', 'AskP5', 'AskV5',
                         'BidP6', 'BidV6', 'AskP6', 'AskV6', 'BidP7', 'BidV7', 'AskP7', 'AskV7', 'BidP8', 'BidV8', 'AskP8', 'AskV8', 'BidP9', 'BidV9', 'AskP9', 'AskV9',
                         'BidP10', 'BidV10', 'AskP10', 'AskV10', 'Volume', 'Turover', 'DateTime']

    # 删除部分暂无用的字段
    del stockData['SecurityType']
    del stockData['NumTrades']
    del stockData['TotalBidNumber']
    del stockData['TotalOfferNumber']
    del stockData['WeightedAvgBidPx']
    del stockData['WeightedAvgOfferPx']

    stockData['DateTime'] = pd.to_datetime(stockData['DateTime'], format='%Y%m%d%H%M%S%f')  # 将字符串的日期时间转为datetime类型
    stockData['TimeStamp'] = (stockData['DateTime'] - dt.datetime(1970, 1, 1)).dt.total_seconds() - 28800  # 计算TimeStamp并保存为float格式
    stockData['Time'] = stockData['Time'].astype(int)  # 这里默认Time是obj,转为int以便后续过滤，且保持与原project一致
    stockData['Date'] = stockData['Date'].astype(int)  # 这里默认Date是obj,转为int以便后续过滤，且保持与原project一致

    stockData = stockData.sort_values(by='TimeStamp')  # 对所有数据根据TimeStamp升序排列

    # 将中午休市时间和下午14:56:57之后的数据过滤
    timeFilter = (stockData['Time'] < 113000000) | (stockData['Time'] >= 130000000)
    stockData = stockData[timeFilter]
    timeFilter = stockData['Time'] < 145657000
    stockData = stockData[timeFilter]

    del stockData['DateTime']

    stockData2 = [None for _ in range(dateList.__len__())]
    for iTradeDate in range(dateList.__len__()):
        tempStockData = stockData[stockData['Date'] == dateList[iTradeDate]]
        # 如全天无行情，则当天数据直接跳过，在List中当天的值None
        if tempStockData.__len__() == 0:
            continue
        # 如当天最后一个tick的累计成交量都是0，则也跳过，在List中当天的值为0
        if tempStockData.at[tempStockData.index[-1], 'AccVolume'] == 0:
            continue
        tempStockData2 = {}
        for column in tempStockData:
            tempStockData2[column] = np.array(tempStockData[column]).tolist()
        stockData2[iTradeDate] = tempStockData2

    return stockData2


def getInsightTransactionData(stockCode, startDateTime, endDateTime, cancellationFilter=True, testMode=False, timeMode=1):
    """
    函数实现的功能类似原ReadDataFile.getTransactiondata，根据输入的股票代码、开始日期时间、终止日期时间，输出逐笔成交数据

    输出的数据的格式是list, 其长度等于开始日期和终止日期之间的交易所日历交易日天数
    输出的list的内容是dict, dict共有9个key: ['Date', 'Time', 'BidOrder', 'AskOrder', 'TradeType', 'BSFlag', 'Price', 'Volume', 'TimeStamp']
    若某天股票停牌，则list当天的内容为None
    cancellationFilter默认=True，则所有撤单的信息不会输出
    【注意！】这里取到的数据和原Project最大的区别在于，原柯楠提供的BSFlag中，1是买、-1是卖；而insight行情（同实盘行情）1是买，2是卖
    testMode默认=False, 如为True的话，则BSFlag改为1是买、=1是卖；这一改动未来将删除

    timeMode默认=1，则输出的每天的数据的时间是startDateTime.time()和endDateTime.time()之间的时间；若为2则为每天093000到145659之间的数据
    """
    startDate8digit = startDateTime.year * 10000 + startDateTime.month * 100 + startDateTime.day
    endDate8digit = endDateTime.year * 10000 + endDateTime.month * 100 + endDateTime.day
    startTime6digit = str(startDateTime.hour * 10000 + startDateTime.minute * 100 + startDateTime.second)
    if startTime6digit.__len__() < 6:  # 如开始时间是上午9:30:01，不足6位需补齐
        startTime6digit = '0' + startTime6digit
    endDate6digit = str(endDateTime.hour * 10000 + endDateTime.minute * 100 + endDateTime.second)
    if endDate6digit.__len__() < 6:
        endDate6digit = '0' + endDate6digit

    # 用xquant的api取交易日日期, 得到的是格式如[20180319, 20180320, 20180321]的数据
    dateList = quant.tradingDay(startDate8digit, endDate8digit)
    # 生成类似这样的list —— [['20180320093000', '20180320145659'], ['20180321093000', '20180321145659']]
    if timeMode == 1:
        dateTimeStr = [[str(iDate) + str(startTime6digit), str(iDate) + str(endDate6digit)] for iDate in dateList]
    else:
        dateTimeStr = [[str(iDate) + '093000', str(iDate) + '145659'] for iDate in dateList]

    stockData = pd.DataFrame()
    for iDateTime in dateTimeStr:
        # 获取当日的逐笔成交数据
        df = ma.getMDTransactionDataFrame(stockCode, iDateTime[0], iDateTime[1])
        if df.__len__() > 0:
            df['DateTime'] = df['MDDate'] + df['MDTime']  # 将字符串相连
        else:
            continue
        # 将每日的数据堆叠起来（因为目前只能逐日取数据）
        if stockData.__len__() > 0:
            stockData = stockData.append(df)
        else:
            stockData = df.copy()

    if cancellationFilter:
        stockData = stockData[stockData['TradeType'] == 0]  # 只保留成交的数据，删除撤单的数据

    if testMode:
        stockData.loc[stockData['TradeBSFlag'] == 2, 'TradeBSFlag'] = -1  # 在测试模式中，将主卖的2替换为-1

    # 删除部分暂无用的字段
    del stockData['SecurityType']
    del stockData['TradeIndex']
    del stockData['HTSCSecurityID']
    del stockData['TradeMoney']

    # 将字段名重命名为原Project的字段名
    stockData.columns = ['Date', 'Time', 'BidOrder', 'AskOrder', 'TradeType', 'BSFlag', 'Price', 'Volume', 'DateTime']

    stockData['DateTime'] = pd.to_datetime(stockData['DateTime'], format='%Y%m%d%H%M%S%f')  # 将字符串的日期时间转为datetime类型
    stockData['TimeStamp'] = (stockData['DateTime'] - dt.datetime(1970, 1, 1)).dt.total_seconds() - 28800  # 计算TimeStamp并保存为float格式

    stockData = stockData.sort_values(by='TimeStamp')  # 对所有数据根据TimeStamp升序排列
    stockData['Time'] = stockData['Time'].astype(int)  # 这里默认Time是obj,转为int以便后续过滤，且保持与原project一致
    stockData['Date'] = stockData['Date'].astype(int)  # 这里默认Date是obj,转为int以便后续过滤，且保持与原project一致

    del stockData['DateTime']

    stockData2 = [None for _ in range(dateList.__len__())]
    for iTradeDate in range(dateList.__len__()):
        tempStockData = stockData[stockData['Date'] == dateList[iTradeDate]]
        # 如取到的数据为空，则跳过，当天值为None
        if tempStockData.empty:
            continue
        tempStockData2 = {}
        for column in tempStockData:
            tempStockData2[column] = np.array(tempStockData[column]).tolist()
        stockData2[iTradeDate] = tempStockData2

    return stockData2


# 以下代码是debug时用到的，可不用理会
# getInsightTickData('601688.SH', dt.datetime(2018,4,9,9,30,00), dt.datetime(2018,4,10,14,56,59))
# data1 = getInsightTickData('300104.SZ', dt.datetime(2018,1,1,9,30,00), dt.datetime(2018,1,24,14,56,59))
# print(type(data1))
# print(type(data1[0]))
# print(data1[-1].keys())
# print(data1[-1]['Time'])
# print(data1.head())
# data1.info()

# data2 = getInsightTransactionData('000002.SZ', dt.datetime(2018,1,5,9,30,00), dt.datetime(2018,1,24,14,56,59), True)
# print(type(data2))
# print(data2.__len__())
# print(type(data2[0]))
# print(data2[-1].keys())
# print(data2[0])
# print(data2[0]['Volume'][0])
# print(data2[-1]['Time'])
# print(data2[-1]['Time'].__len__())

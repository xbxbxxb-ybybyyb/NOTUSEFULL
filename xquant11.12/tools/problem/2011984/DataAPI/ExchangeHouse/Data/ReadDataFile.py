import pandas as pd
import datetime as dt
import scipy.io as sio
from os import path
from Utils.Rpc.RemotePrint import print


def getData(dfs, srcDir, stockCode, startDateTime, endDateTime, exchangeTradingDayList, timemode=1):
    """
    getData这个函数是根据输入的股票代码、开始日期时间、终止日期时间及交易所日历中的交易日(exchangeTradingDayList，输出所选的股票数据
    输出的数据的格式是list, 其长度等于开始日期和终止日期之间的交易所日历交易日天数
    输出的list的内容是dict, 若某天股票停牌，则当天为空
    timemode默认=1，则输出的每天的数据的时间是startDateTime.time()和endDateTime.time()之间的时间

    注意，该函数的startDateTime和endDateTime都是Strategy定义的时间，而exchangeTradingDayList是切分后的日期list，
    例如，startDateTime=2017/10/10/09/30/00，endDateTime=2017/10/16/15/00/00，exchangeTradingDayList=[2017/10/12, 2017/10/13]
    """

    # 根据exchangeTradingDayList输出年月
    # 例如输出的yearmonth_list是 ['2016-11', '2016-12', '2017-01']
    yearMonth_set = set()
    for date in exchangeTradingDayList:
        yearMonth_set.add('{}-{:0>2d}'.format(date.year, date.month))
    startTime8digit = startDateTime.hour * 10000000 + startDateTime.minute*100000 + startDateTime.second * 10000
    endTime8digit = endDateTime.hour * 10000000 + endDateTime.minute*100000 + endDateTime.second * 10000
    yearMonth_list = list(yearMonth_set)
    yearMonth_list.sort()

    StockData = pd.DataFrame()
    for i in range(yearMonth_list.__len__()):
        if (stockCode[0] == "0" and stockCode[-1] == "H") or (stockCode[:2] == "39" and stockCode[-1] == "Z"):    # 如果是指数，则在指数文件夹下读取文档
            matFilePath = path.join(srcDir, 'IndexTickData', stockCode, 'TickInfo_' + stockCode + '_' + yearMonth_list[i] + '.mat')
        else:
            matFilePath = path.join(srcDir, 'StockTickData', stockCode, 'TickInfo_' + stockCode + '_' + yearMonth_list[i] + '.mat')
        if not dfs.exists(matFilePath):
            # 若这只股票当月无数据文件，则跳过
            print('{} {} 无数据'.format(stockCode, yearMonth_list[i]))
            continue
        matData = sio.loadmat(dfs.open(matFilePath, 'rb', buffer_size=1024))  # 将matlab数据读进来，得到一个叫matdata的字典
        if len(matData['TimeStamp']) == 0:  # 若股票整个月都停牌，则跳过
            continue
        DateTimeIndex = [None for _ in range(len(matData['TimeStamp']))]
        for iTime in range(0, len(matData['TimeStamp'])):
            DateTimeIndex[iTime] = dt.datetime.fromtimestamp(matData['TimeStamp'][iTime])
        del matData['__header__']   # 读入mat文件会生成这3个无用的数据，删去
        del matData['__version__']
        del matData['__globals__']
        tempStockData = pd.DataFrame(index=DateTimeIndex)
        for key in matData:
            tempStockData[key] = matData[key]
        if StockData.__len__() > 0:
            StockData = StockData.append(tempStockData)
        else:
            StockData = tempStockData.copy()

    startDateTimeStamp = startDateTime.timestamp()
    endDateTimeStamp = endDateTime.timestamp()
    firstDate = exchangeTradingDayList[0]
    lastDate = exchangeTradingDayList[-1]
    firstDateTimeStamp = dt.datetime(firstDate.year, firstDate.month, firstDate.day, 0, 0, 0).timestamp()
    lastDateTimeStamp = dt.datetime(lastDate.year, lastDate.month, lastDate.day, 23, 59, 59).timestamp()
    validTime1 = (StockData['TimeStamp'] >= startDateTimeStamp) & (StockData['TimeStamp'] <= endDateTimeStamp) \
        & (StockData['TimeStamp'] >= firstDateTimeStamp) & (StockData['TimeStamp'] <= lastDateTimeStamp)
    StockData = StockData[validTime1]  # 仅保留startDateTime和endDateTime之间的数据
    if timemode == 1:
        if stockCode[-1] == 'H':  # 上交所的股票或指数
            timeFilter = (startTime8digit <= StockData['Time']) & (StockData['Time'] <= endTime8digit) & \
                         ((StockData['Time'] < 113000000) | (StockData['Time'] >= 130000000)) & (StockData['Time'] < 145957000)
        else:  # 深交所的股票或指数
            timeFilter = (startTime8digit <= StockData['Time']) & (StockData['Time'] <= endTime8digit) &\
                         ((StockData['Time'] < 113000000) | (StockData['Time'] >= 130000000)) & (StockData['Time'] < 145657000)
    else:
        if stockCode[-1] == 'H':  # 上交所的股票或指数
            timeFilter = ((StockData['Time'] >= 93000000) & (StockData['Time'] < 113000000)) | ((StockData['Time'] >= 130000000) & (StockData['Time'] < 145957000))
        else:   # 深交所的股票或指数
            timeFilter = ((StockData['Time'] >= 93000000) & (StockData['Time'] < 113000000)) | ((StockData['Time'] >= 130000000) & (StockData['Time'] < 145657000))
    StockData = StockData[timeFilter]  # 仅保留在连续竞价期间的数据

    tradeDates = list(set(StockData.index.date))   # 股票本身在这段期间的交易日
    tradeDates.sort()   # 对交易日进行排序
    StockData2 = [None for _ in range(exchangeTradingDayList.__len__())]   # StockData2是一个list, 里面每个元素是一天的数据
    for iTradeDate in range(exchangeTradingDayList.__len__()):
        if exchangeTradingDayList[iTradeDate] in tradeDates:     # 对交易所交易日进行循环，如果当天股票有交易
            tempStockData = StockData[str(exchangeTradingDayList[iTradeDate])]
            tempStockData2 = {}
            for column in tempStockData:
                tempStockData2[column] = tempStockData[column].tolist()
            StockData2[iTradeDate] = tempStockData2
    return StockData2

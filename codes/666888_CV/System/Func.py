# Updated on 2018/10/14  若T+1日涨跌幅绝对值超过9%，则T+1日后续的行情不再参与因子和标签计算；
# Updated on 2018/10/28  将第1天的sliceData的逐笔成交信息都设为[]、第2天不再给preDayTick新增对象，试图减少内存占用

# -*- coding: utf-8 -*-
from System.ExecuteStrategy import ExecuteStrategy
from System import Utils
from System.SliceData import SliceData
import datetime as dt
from System.RemotePrint import print
import copy


def execute(strategy, broadcast, writer):
    """
    用户自定义的处理1个策略1个股票组在若干连续日期内的数据的函数。

    :param strategy: Strategy
    :param broadcast: DataBroadcast
    :param writer: file
    """
    # print('Starts to execute func on strategy: {}, code: {}, days: {}'.format(strategy.getStrategyName()))
    #    broadcast.getTradingUnderlyingCode(), broadcast.getTradingDays()))
    preDayTicks = []
    for i in range(broadcast.getLenForLoop()):
        factors = []
        timestamps = []
        tags = []
        sliceNum = broadcast.prepareSliceData(i)
        if sliceNum == 0:   # 如果sliceNum ==0 则表示当天组中有至少一只股票停牌，那么跳过
            continue
        executeStrategy = ExecuteStrategy(strategy, broadcast.getTradingUnderlyingCode())
        if len(preDayTicks) != 0:
            executeStrategy.setPreDayticks(preDayTicks)
            preDayTicks = []

            sliceData = broadcast.getSliceData()
            executeStrategy.onMarketData(sliceData)  # 把数据传进去并且计算
            factor, factorName, timestamp, tag = executeStrategy.getOutput()
            factors.append(factor)
            timestamps.append(timestamp)
            tags.append(tag)
            # preDayTicks.append(sliceData)
            previousSliceData: SliceData = sliceData

            for j in range(sliceNum - 1):
                sliceData = broadcast.getSliceData()
                if abs(sliceData.lastPrice / sliceData.previousClosingPrice - 1) >= 0.09:
                    sliceData.isLastSlice = True
                    break
                # 比较相邻两个sliceData的timeStamp, 并除以3，取商的整数
                tickTimeDiff, _ = divmod(sliceData.timeStamp - previousSliceData.timeStamp, 3)
                # 如相邻两个sliceData的时间戳差距小于6秒，或差距在3000秒以上（跨中午了），则正常播放不用补行情
                if tickTimeDiff < 2 or tickTimeDiff > 1000:
                    if j == sliceNum - 2:
                        sliceData.isLastSlice = True
                    executeStrategy.onMarketData(sliceData)    # 把数据传进去并且计算
                    factor, factorName, timestamp, tag = executeStrategy.getOutput()
                    factors.append(factor)
                    timestamps.append(timestamp)
                    tags.append(tag)
                    # preDayTicks.append(sliceData)
                    previousSliceData: SliceData = sliceData
                # 如相邻两个sliceData的时间戳差距大于等于6秒，开始补sliceData
                # 补的原则是时间+3秒、量和额为0、逐笔成交为空，盘口信息等不变
                else:
                    # 以下播放补的sliceData的行情
                    tickNeedFillingNum = tickTimeDiff - 1
                    tickFilledNum = 0
                    while tickNeedFillingNum > 0:
                        tickNeedFillingNum -= 1
                        tickFilledNum = tickFilledNum + 1
                        fillingSliceData: SliceData = copy.deepcopy(previousSliceData)
                        fillingSliceData.timeStamp = previousSliceData.timeStamp + 3 * tickFilledNum
                        fillingSliceData.time = timeStamp2TimeInt(fillingSliceData.timeStamp)
                        # print(dt.datetime.fromtimestamp(fillingSliceData.timeStamp))
                        fillingSliceData.amount = 0
                        fillingSliceData.volume = 0
                        fillingSliceData.transactionData = []
                        fillingSliceData.transactionTimeStamp = []
                        executeStrategy.onMarketData(fillingSliceData)  # 把数据传进去并且计算
                        factor, factorName, timestamp, tag = executeStrategy.getOutput()
                        factors.append(factor)
                        timestamps.append(timestamp)
                        tags.append(tag)
                        # preDayTicks.append(fillingSliceData)
                    # 然后照常播最新一个sliceData的行情
                    if j == sliceNum - 2:
                        sliceData.isLastSlice = True
                    executeStrategy.onMarketData(sliceData)    # 把数据传进去并且计算
                    factor, factorName, timestamp, tag = executeStrategy.getOutput()
                    factors.append(factor)
                    timestamps.append(timestamp)
                    tags.append(tag)
                    # preDayTicks.append(sliceData)
                    previousSliceData: SliceData = sliceData

            subTags = [t.subTag for t in tags]
            # 由于每天的计算结果独立, 为了节约内存, 每天的计算结果完成后都先输出到文件再进行下一天的计算
            Utils.encodeOutputs(factors, subTags, broadcast.getTradingUnderlyingCode(), factorName, writer)
        else:
            for j in range(sliceNum):
                sliceData = broadcast.getSliceData()
                sliceData = sliceDataDepreciated(sliceData)
                if j == sliceNum - 1:
                    sliceData.isLastSlice = True
                preDayTicks.append(sliceData)


def timeStamp2TimeInt(timeStamp):
    timeDatetime = dt.datetime.fromtimestamp(timeStamp)
    timeInt = timeDatetime.hour * 10000000 + timeDatetime.minute * 100000 + timeDatetime.second * 1000
    return timeInt


def sliceDataDepreciated(sliceDataInput: SliceData):
    sliceDataInput.transactionData = []
    sliceDataInput.transactionTimeStamp = []
    return sliceDataInput
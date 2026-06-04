# -*- coding: utf-8 -*-
from System.ExecuteStrategy import ExecuteStrategy
from System import Utils
from System.RemotePrint import print


def execute(strategy, broadcast, writer):
    """
    用户自定义的处理1个策略1个股票组在若干连续日期内的数据的函数。

    :param strategy: Strategy
    :param broadcast: DataBroadcast
    :param writer: file
    """
    #print('Starts to execute func on strategy: {}, code: {}, days: {}'.format(strategy.getStrategyName(),
    #    broadcast.getTradingUnderlyingCode(), broadcast.getTradingDays()))
    preDayTicks= []
    for i in range(broadcast.getLenForLoop()):
        factors = []
        timestamps = []
        tags = []
        sliceNum = broadcast.prepareSliceData(i)
        if sliceNum == 0:   # 如果sliceNum ==0 则表示当天组中有至少一只股票停牌，那么跳过
            continue
        executeStrategy = ExecuteStrategy(strategy, broadcast.getTradingUnderlyingCode())
        #factorName = executeStrategy.getFactorName()
        if len(preDayTicks) != 0:
            executeStrategy.setPreDayticks(preDayTicks)
            preDayTicks = []

            for j in range(sliceNum):
                sliceData = broadcast.getSliceData()
                if j == sliceNum - 1:
                    sliceData.isLastSlice = True
                executeStrategy.onMarketData(sliceData)    # 把数据传进去并且计算
                factor, factorName, timestamp, tag = executeStrategy.getOutput()
                factors.append(factor)
                timestamps.append(timestamp)
                tags.append(tag)
                preDayTicks.append(sliceData)
            subTags = [t.subTag for t in tags]
            # 由于每天的计算结果独立, 为了节约内存, 每天的计算结果完成后都先输出到文件再进行下一天的计算
            Utils.encodeOutputs(factors, subTags, broadcast.getTradingUnderlyingCode(), factorName, writer)
        else:
            for j in range(sliceNum):
                sliceData = broadcast.getSliceData()
                if j == sliceNum - 1:
                    sliceData.isLastSlice = True
                preDayTicks.append(sliceData)

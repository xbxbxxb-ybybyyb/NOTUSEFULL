# -*- coding: utf-8 -*-
"""
Created on 2018/7/25
@author: 012807
"""
from System.ExecuteStrategy import ExecuteStrategy
from System import Utils
from System.RemotePrint import print
import numpy as np
import time
N_PRE_DAY_REPLAY_TICKS = 500
N_SAVE_PREDAY = 0

def shift_slice(slicePreDay, sliceToday, i_shift):
    # calculate gap
    if max(slicePreDay.askPrice[0], slicePreDay.bidPrice[0]) > 0 and max(sliceToday.askPrice[0], sliceToday.bidPrice[0])> 0:
        gap_mid_price = (sliceToday.askPrice[0] + sliceToday.bidPrice[0])/2 - (slicePreDay.askPrice[0]+slicePreDay.bidPrice[0])/2
    else:
        gap_mid_price = max(sliceToday.askPrice[0], sliceToday.bidPrice[0]) - max(slicePreDay.askPrice[0], slicePreDay.bidPrice[0])
    gap_total_amount = slicePreDay.totalAmount
    gap_total_volume = slicePreDay.totalVolume
  
    # fake time
    slicePreDay.timeStamp = sliceToday.timeStamp - i_shift*3
    time_local = time.localtime(slicePreDay.timeStamp)
    d = time.strftime("%Y-%m-%d\%H%M%S000", time_local)
    t = int(d.split("\\")[1])
    slicePreDay.time = t

    
    # gap fill
    for i_level in np.arange(0, 10):
        #print(slice_.askPrice[i])
        if slicePreDay.askPrice[i_level] != 0:
            slicePreDay.askPrice[i_level] = slicePreDay.askPrice[i_level] + gap_mid_price
        if slicePreDay.bidPrice[i_level] != 0:
            slicePreDay.bidPrice[i_level] = slicePreDay.bidPrice[i_level] + gap_mid_price
    slicePreDay.totalAmount = slicePreDay.totalAmount - gap_total_amount
    slicePreDay.totalVolume = slicePreDay.totalVolume - gap_total_volume
    return slicePreDay

def execute(strategy, broadcast, writer):
    """
    用户自定义的处理1个策略1个股票组在若干连续日期内的数据的函数。

    :param strategy: Strategy
    :param broadcast: DataBroadcast
    :param writer: file
    """
    preDayTicks= []
    for i in range(broadcast.getLenForLoop()):
        factors = []
        timestamps = []
        tags = []
        sliceNum = broadcast.prepareSliceData(i)
        #print("SliceNum:",sliceNum)
        if sliceNum == 0:   # 如果sliceNum ==0 则表示当天组中有至少一只股票停牌，那么跳过
            continue
        executeStrategy = ExecuteStrategy(strategy, broadcast.getTradingUnderlyingCode())
        if len(preDayTicks) > 0:
            #-----------------Repaly PreDay-----------------------------------
            if len(preDayTicks) > N_PRE_DAY_REPLAY_TICKS:
                PreDayToReplay = preDayTicks[-N_PRE_DAY_REPLAY_TICKS:]
            else:
                PreDayToReplay = preDayTicks
            sliceData = broadcast.getSliceData()
            PreDayToReplay = PreDayToReplay[:-1]
            cnt_pre = len(PreDayToReplay)
            for slicePreDay in PreDayToReplay:
                slicePreDay = shift_slice(slicePreDay, sliceData, cnt_pre)            
                executeStrategy.onMarketData(slicePreDay)                
                if cnt_pre < N_SAVE_PREDAY:
                    factor, factorName, timestamp, tag = executeStrategy.getOutput()
                    factors.append(factor)
                    timestamps.append(timestamp)
                    tags.append(tag)
                cnt_pre = cnt_pre - 1  
            #------------------Repaly ----------------------------------
            executeStrategy.setPreDayticks(preDayTicks)
            preDayTicks = []
            for j in range(sliceNum):
                if j==0:
                    executeStrategy.onMarketData(sliceData)  
                    continue
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

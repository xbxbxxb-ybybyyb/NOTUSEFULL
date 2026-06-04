"""
Created on 2018/7/16
根据输入的股票代码、开始日期和结束日期，输出有效交易日list
Updated on 2018/7/17: 若个股某日无交易，将股票代码和日期打印出来

@author: 006566
"""

import xquant.quant as xq
import System.GetTradingDay as GTD
import datetime as dt


def getValidTradingDayList(stockCode, startDate, endDate, printNotTradeDay=False):
    if isinstance(startDate, dt.date):
        startDateInt = startDate.year * 10000 + startDate.month * 100 + startDate.day
        endDateInt = endDate.year * 10000 + endDate.month * 100 + endDate.day
        dateMode = 1
    else:
        startDateInt = startDate
        endDateInt = endDate
        dateMode = 2
    tradingDayList = GTD.getTradingDay(startDateInt, endDateInt)
    [factorData, _, _] = xq.hfactor([stockCode], [xq.Factors.volume], tradingDayList)
    
    if factorData.__len__() <= 0:
        print(stockCode, "has no valid trading day from", tradingDayList[0], "to", tradingDayList[-1])
        return []
        
    print (stockCode)    
    validTradingDayList = [tradingDayList[i] for i in range(tradingDayList.__len__()) if factorData[0][1][0][i] is not None and factorData[0][1][0][i] >= 100]
    if validTradingDayList.__len__() < factorData[0][1][0].__len__() and printNotTradeDay:
        notTradeDay = list(set(tradingDayList) - set(validTradingDayList))
        notTradeDay.sort()
        for iDay in notTradeDay:
            print(stockCode, "did not trade on", iDay)
    if dateMode == 1:
        validTradingDayList2 = [intDate2DtDate(i) for i in validTradingDayList]
    else:
        validTradingDayList2 = validTradingDayList
    return validTradingDayList2


def intDate2DtDate(dateInt):
    return dt.date(int(str(dateInt)[0:4]), int(str(dateInt)[4:6]), int(str(dateInt)[6:8]))

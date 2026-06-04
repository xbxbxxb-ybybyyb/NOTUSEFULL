"""
Created on 2018/7/16
根据输入的股票代码、开始日期和结束日期，输出有效交易日list
Updated on 2018/7/17: 若个股某日无交易，将股票代码和日期打印出来

@author: 006566
"""

import System.GetTradingDay as GTD
import datetime as dt
from xquant.factordata import FactorData
fd = FactorData()

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

    df1 = fd.get_factor_value("Basic_factor", [stockCode], list(map(str, tradingDayList)), ["trade_status"])
    df1 = df1.reset_index()
    df2 = df1[~df1["trade_status"].isnull()]
    df2 = df2[df2["trade_status"] != "停牌"]
    df2 = df2[df2["trade_status"] != "待核查"]
    dateList = df2["mddate"].astype("int").tolist()
    dateList.sort()

    if dateMode == 1:
        validTradingDayList2 = [intDate2DtDate(i) for i in dateList]
    else:
        validTradingDayList2 = dateList
    return validTradingDayList2


def intDate2DtDate(dateInt):
    return dt.date(int(str(dateInt)[0:4]), int(str(dateInt)[4:6]), int(str(dateInt)[6:8]))

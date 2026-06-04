import datetime as dt
import numpy as np
import pandas as pd
import DataAPI.GetTradingDay
import DataAPI.DataToolkit as dtk


def getKeyMinutes():
    minutes = ([dt.datetime(1949, 10, 1, 9, 40, 0) + dt.timedelta(minutes=10 * i) for i in range(11)]
               + [dt.datetime(1949, 10, 1, 13, 0, 0) + dt.timedelta(minutes=10 * i) for i in range(13)])
    minutes = list(map(lambda x: x.strftime("%H:%M:%S"), minutes))

    return minutes


def getTradingDayList(startDate, endDate):
    tradingDays = DataAPI.GetTradingDay.trading_day_list
    dates = [x for x in tradingDays if startDate <= x <= endDate]

    return dates


def getNonSuspendStartDate(symbol, startDate, period):
    tradingDays = DataAPI.GetTradingDay.trading_day_list
    startDateIndex = np.searchsorted(tradingDays, startDate)
    startIndex = startDateIndex - period
    endIndex = startDateIndex - 1

    while True:
        amt = dtk.get_panel_daily_pv_df([symbol], tradingDays[startIndex], tradingDays[endIndex], "amt")
        validDayNumber = (amt[symbol] > 0).sum()

        if validDayNumber == period:
            break

        startIndex -= 1

    return tradingDays[startIndex]


def getDailyVolumeSeries(df):
    preMinute = 0

    minutes = getKeyMinutes()
    minutes = list(map(lambda x: int(x[:2] + x[3:5]), minutes))

    df = df.droplevel(0)
    df.loc[930, "volume"] += df.loc[925, "volume"]
    df = df.drop(925)
    df.loc[1456, "volume"] += df.loc[1457, "volume"]
    df.loc[1457, "volume"] = df.loc[1500, "volume"]
    df = df.drop(1500)

    volumeSummation = df.groupby(pd.cut(df.index, [preMinute] + minutes, right=False), as_index=False)["volume"].sum()
    volumeSummation.index = minutes

    return volumeSummation


def getTargetQtyIntervalList(symbol, targetQty, date, period):
    nonSuspendStartDate = getNonSuspendStartDate(symbol, date, period)
    minuteData = dtk.get_single_stock_minute_data2(symbol, nonSuspendStartDate, date)

    dailyVolumeDF = minuteData.groupby(level=0).apply(getDailyVolumeSeries)
    dailyVolumeDF = dailyVolumeDF["volume"].unstack(level=1)
    dailyVolumeDF = dailyVolumeDF[dailyVolumeDF.sum(axis=1) > 0]
    dailyVolumeDF = dailyVolumeDF.rolling(period).sum()
    dailyVolumeDF = dailyVolumeDF.iloc[-1]

    targetQtyPctSeries = (dailyVolumeDF / dailyVolumeDF.sum()).cumsum()

    targetQtyIntervalSeries = targetQtyPctSeries * targetQty
    targetQtyIntervalSeries = targetQtyIntervalSeries.apply(lambda x: int(x / 100) * 100)
    targetQtyIntervalSeries.iloc[-1] = int(targetQty)

    return targetQtyIntervalSeries.tolist()


def generateTimetableAndTargetQtyInterval(symbol, quantity, date, period):
    try:
        targetQty = abs(quantity)
        timetable = getKeyMinutes()
        targetQtyIntervalList = getTargetQtyIntervalList(symbol, targetQty, date, period)

        timetableRes = []
        targetQtyIntervalRes = []
        lastQty = None
        for tt, tq in zip(timetable, targetQtyIntervalList):
            if tq == 0 or tq == lastQty:
                continue

            timetableRes.append(tt)
            targetQtyIntervalRes.append(tq)

            lastQty = tq

        if quantity > 0:
            result = [{"Time": str(v1), "TargetQty": str(v2)} for v1, v2 in zip(timetableRes, targetQtyIntervalRes)]
        else:
            result = [{"Time": str(v1), "TargetQty": str(-v2)} for v1, v2 in zip(timetableRes, targetQtyIntervalRes)]

        return result
    except Exception as e:
        print(repr(e))
        return None

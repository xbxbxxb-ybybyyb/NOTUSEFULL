import json
import datetime as dt
import numpy as np
import pandas as pd
import DataAPI.GetTradingDay
import DataAPI.DataToolkit as dtk
from xquant.pyfile import Pyfile


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


def getTargetQtyIntervalDict(symbol, targetQty, startDate, endDate, period):
    tradingDayList = getTradingDayList(startDate, endDate)
    if not tradingDayList:
        raise Exception("No trading day between {} and {}".format(str(startDate), str(endDate)))

    nonSuspendStartDate = getNonSuspendStartDate(symbol, tradingDayList[0], period)
    minuteData = dtk.get_single_stock_minute_data2(symbol, nonSuspendStartDate, tradingDayList[-1])

    dailyVolumeDF = minuteData.groupby(level=0).apply(getDailyVolumeSeries)
    dailyVolumeDF = dailyVolumeDF["volume"].unstack(level=1)
    dailyVolumeDF = dailyVolumeDF[dailyVolumeDF.sum(axis=1) > 0]
    dailyVolumeDF = dailyVolumeDF.rolling(period).sum().shift(1)
    dailyVolumeDF = dailyVolumeDF.loc[startDate:endDate]

    targetQtyPctDF = dailyVolumeDF.div(dailyVolumeDF.sum(axis=1), axis=0).cumsum(axis=1)
    targetQtyPctDF.iloc[:, -1] = 1

    targetQtyIntervalDF = targetQtyPctDF * targetQty
    targetQtyIntervalDF = targetQtyIntervalDF.applymap(lambda x: int(x / 100) * 100)
    targetQtyIntervalDF.index = targetQtyIntervalDF.index.astype("str")
    targetQtyIntervalDict = targetQtyIntervalDF.T.to_dict(orient="list")

    return targetQtyIntervalDict


def generateTimetableAndTargetQtyInterval(outputDir, portfolioPath, startDate, endDate, period):
    py = Pyfile()
    portfolioDF = pd.read_excel(portfolioPath)
    portfolioDF = portfolioDF.set_index("证券代码")
    targetQtyDict = (portfolioDF["买入证券数量"] + portfolioDF["卖出证券数量"]).to_dict()

    symbols = list(targetQtyDict.keys())
    symbols.sort()
    symbols = symbols[:]

    stockNumber = len(symbols)
    currNumber = 1
    for symbol in symbols:
        time1 = dt.datetime.now()

        try:
            result = {}

            targetQty = abs(targetQtyDict[symbol])
            timetable = getKeyMinutes()
            targetQtyIntervalDict = getTargetQtyIntervalDict(symbol, targetQty, startDate, endDate, period)

            resTimetable = {}
            resTargetQtyInterval = {}

            for k, v in targetQtyIntervalDict.items():
                timetableRes = []
                targetQtyIntervalRes = []
                lastQty = None
                for tt, tq in zip(timetable, v):
                    if tq == 0 or tq == lastQty:
                        continue

                    timetableRes.append(tt)
                    targetQtyIntervalRes.append(tq)

                    lastQty = tq

                resTimetable[k] = timetableRes
                resTargetQtyInterval[k] = targetQtyIntervalRes

            result["Timetable"] = resTimetable
            result["TargetQtyInterval"] = resTargetQtyInterval

            with py.open("{}/{}.json".format(outputDir, symbol), "wb") as f:
                json.dump(result, f)
        except Exception as e:
            print(repr(e))

        time2 = dt.datetime.now()
        print("{} time cost: {}s, {}/{}".format(symbol, (time2 - time1).total_seconds(), currNumber, stockNumber))

        currNumber += 1


def main():
    portfolio = "5161101"
    testSuffix = "20191223"
    startDate = 20191007
    endDate = 20191220
    period = 20

    outputDir = "Apollo/cv_params/{}-{}_{}/{}/".format(startDate, endDate, testSuffix, portfolio)
    portfolioPath = "/data/user/666888/Apollo/portfolios/{}/night/Apollo_{}_{}.xlsx".format(
        testSuffix, portfolio, testSuffix
    )

    generateTimetableAndTargetQtyInterval(outputDir, portfolioPath, startDate, endDate, period)


if __name__ == "__main__":
    main()

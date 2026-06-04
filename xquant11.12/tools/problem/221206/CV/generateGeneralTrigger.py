import datetime as dt
import pandas as pd
from DataAPI.GetTradingDay import trading_day
from xquant.factordata import FactorData

fd = FactorData()

signalLibrary = "Model20190101_48"
columnNames = ["timestamp", "ticktime", "prediction1minLong", "prediction2minLong", "prediction5minLong",
               "prediction1minShort", "prediction2minShort", "prediction5minShort"]


def processSignals(data):
    data["predictionLong"] = data[["prediction1minLong", "prediction2minLong", "prediction5minLong"]].mean(axis=1)
    data["predictionShort"] = data[["prediction1minShort", "prediction2minShort", "prediction5minShort"]].mean(axis=1)
    data["ticktime"] = data["ticktime"].apply(lambda x: dt.datetime.strptime(x, "%H:%M:%S").time())

    data = averageSpecialTime(data, dt.time(11, 25, 0), dt.time(11, 28, 0), dt.time(11, 30, 0))
    data = averageSpecialTime(data, dt.time(14, 52, 0), dt.time(14, 55, 0), dt.time(14, 57, 0))

    data["ticktime"] = data["ticktime"].apply(lambda x: int(x.strftime("%H%M")))

    return data


def averageSpecialTime(data, time1, time2, time3):
    mask1 = (time1 <= data["ticktime"]) & (data["ticktime"] < time2)
    data.loc[mask1, "predictionLong"] = data.loc[mask1, ["prediction1minLong", "prediction2minLong"]].mean(axis=1)
    data.loc[mask1, "predictionShort"] = data.loc[mask1, ["prediction1minShort", "prediction2minShort"]].mean(axis=1)

    mask2 = (time2 <= data["ticktime"]) & (data["ticktime"] < time3)
    data.loc[mask2, "predictionLong"] = data.loc[mask2, "prediction1minLong"]
    data.loc[mask2, "predictionShort"] = data.loc[mask2, "prediction1minShort"]

    return data


def generateGeneralTrigger(symbol, triggerDate):
    allDates = fd.search_by_stock(signalLibrary, symbol, list(map(str, trading_day(20190101, int(triggerDate)))))
    btDataDates = allDates[-20:]

    signalList = []
    for date in btDataDates:
        signalDF = fd.get_factor_value(signalLibrary, symbol, date, columnNames)
        signalDF = processSignals(signalDF)
        signalDF["Date"] = date
        signalDF = signalDF.set_index("Date")
        signalList.append(signalDF)

    signalDF = pd.concat(signalList)

    longAggressiveRatio, longPassiveRatio = signalDF["predictionLong"].quantile([0.97, 0.94])
    shortAggressiveRatio, shortPassiveRatio = signalDF["predictionShort"].quantile([0.03, 0.06])

    triggerRatioDict = {
        "longAggressiveRatio": longAggressiveRatio,
        "longPassiveRatio": longPassiveRatio,
        "shortAggressiveRatio": shortAggressiveRatio,
        "shortPassiveRatio": shortPassiveRatio
    }

    return triggerRatioDict

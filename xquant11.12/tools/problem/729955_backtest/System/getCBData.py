import os
import sys

sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
import datetime as dt
import numpy as np
import pandas as pd
from System.TradingDay import getTradingDay
from xquant.bonddata import BondData

bd = BondData()


def getCBTickData(stock, startDate, endDate):
    res = {}

    dayUnit = 20
    tradingDayList = getTradingDay(int(startDate), int(endDate))
    startDateList = tradingDayList[::dayUnit]
    endDateList = tradingDayList[dayUnit - 1:-1:dayUnit] + [tradingDayList[-1]]

    dataList = []
    for sDate, eDate in zip(startDateList, endDateList):
        dataList.append(bd.get_bond_data(stock, "{} 090000000".format(sDate), "{} 200000000".format(eDate), "TICK"))

    if not dataList:
        return res

    data = pd.concat(dataList, axis=0)

    if data.empty:
        return res

    tickVolumeColumnNames = [
        "TotalVolumeTrade", "Buy1OrderQty", "Sell1OrderQty", "Buy2OrderQty", "Sell2OrderQty", "Buy3OrderQty",
        "Sell3OrderQty", "Buy4OrderQty", "Sell4OrderQty", "Buy5OrderQty", "Sell5OrderQty", "Buy6OrderQty",
        "Sell6OrderQty", "Buy7OrderQty", "Sell7OrderQty", "Buy8OrderQty", "Sell8OrderQty", "Buy9OrderQty",
        "Sell9OrderQty", "Buy10OrderQty", "Sell10OrderQty"
    ]
    if stock[-2:] == "SH":
        data.loc[:, tickVolumeColumnNames] *= 10

    data = data.replace({"PreClosePx": 0.0}, np.nan)
    data = data.fillna(method="ffill")

    data = __tickDataKeepUsefulColumns(data)
    data = __tickDataOHLFilter(data)
    data = __tickDataAppendVolumeNTurover(data)
    data = __appendTimeStamp(data)

    data = data.astype({"Date": "int", "Time": "int"})

    for date, df in data.groupby("Date"):
        res[date] = df.to_dict("list")

    return res


def getCBTransactionData(stock, startDate, endDate):
    res = {}

    dayUnit = 20
    tradingDayList = getTradingDay(int(startDate), int(endDate))
    startDateList = tradingDayList[::dayUnit]
    endDateList = tradingDayList[dayUnit - 1:-1:dayUnit] + [tradingDayList[-1]]

    dataList = []
    for sDate, eDate in zip(startDateList, endDateList):
        dataList.append(
            bd.get_bond_data(stock, "{} 090000000".format(sDate), "{} 200000000".format(eDate), "TRANSACTION")
        )

    if not dataList:
        return res

    data = pd.concat(dataList, axis=0)

    if data.empty:
        return res

    transactionVolumeColumnNames = [
        "TradeQty"
    ]
    if stock[-2:] == "SH":
        data.loc[:, transactionVolumeColumnNames] *= 10

    data = __transactionKeepUsefulColumns(data)
    data = __appendTimeStamp(data)

    data = data.loc[data["TradeType"] == 0, :]
    data.loc[data["BSFlag"] == 2, "BSFlag"] = -1

    data = data.astype({"Date": "int", "Time": "int"})

    for date, df in data.groupby("Date"):
        res[date] = df.to_dict("list")

    return res


def __tickDataKeepUsefulColumns(df):
    oldColumnNames = [
        "MDDate", "MDTime", "PreClosePx", "TotalVolumeTrade", "TotalValueTrade", "LastPx", "OpenPx", "HighPx", "LowPx",
        "MaxPx", "MinPx", "HTSCSecurityID", "Buy1Price", "Buy1OrderQty", "Sell1Price", "Sell1OrderQty", "Buy2Price",
        "Buy2OrderQty", "Sell2Price", "Sell2OrderQty", "Buy3Price", "Buy3OrderQty", "Sell3Price", "Sell3OrderQty",
        "Buy4Price", "Buy4OrderQty", "Sell4Price", "Sell4OrderQty", "Buy5Price", "Buy5OrderQty", "Sell5Price",
        "Sell5OrderQty", "Buy6Price", "Buy6OrderQty", "Sell6Price", "Sell6OrderQty", "Buy7Price", "Buy7OrderQty",
        "Sell7Price", "Sell7OrderQty", "Buy8Price", "Buy8OrderQty", "Sell8Price", "Sell8OrderQty", "Buy9Price",
        "Buy9OrderQty", "Sell9Price", "Sell9OrderQty", "Buy10Price", "Buy10OrderQty", "Sell10Price", "Sell10OrderQty",
    ]
    newColumnNames = [
        "Date", "Time", "PreClose", "AccVolume", "AccTurover", "Price", "Open", "High", "Low", "MaxP", "MinP", "Code",
        "BidP1", "BidV1", "AskP1", "AskV1", "BidP2", "BidV2", "AskP2", "AskV2", "BidP3", "BidV3", "AskP3", "AskV3",
        "BidP4", "BidV4", "AskP4", "AskV4", "BidP5", "BidV5", "AskP5", "AskV5", "BidP6", "BidV6", "AskP6", "AskV6",
        "BidP7", "BidV7", "AskP7", "AskV7", "BidP8", "BidV8", "AskP8", "AskV8", "BidP9", "BidV9", "AskP9", "AskV9",
        "BidP10", "BidV10", "AskP10", "AskV10",
    ]

    df = df.loc[:, oldColumnNames]
    df.columns = newColumnNames

    return df


def __tickDataOHLFilter(df):
    mask1 = df["Open"] == 0
    mask2 = df["High"] == 0
    mask3 = df["Low"] == 0
    mask = ~(mask1 | mask2 | mask3)

    return df.loc[mask, :]


def __tickDataAppendVolumeNTurover(df):
    volumeSeriesList = []
    for _, accVolumeSeries in df.groupby("Date")["AccVolume"]:
        volumeSeries = accVolumeSeries.diff()
        volumeSeries.iloc[0] = accVolumeSeries.iloc[0]
        volumeSeriesList.append(volumeSeries)
    df["Volume"] = pd.concat(volumeSeriesList)

    turoverSeriesList = []
    for _, accTuroverSeries in df.groupby("Date")["AccTurover"]:
        turoverSeries = accTuroverSeries.diff()
        turoverSeries.iloc[0] = accTuroverSeries.iloc[0]
        turoverSeriesList.append(turoverSeries)
    df["Turover"] = pd.concat(turoverSeriesList)

    df["Volume"] = df["Volume"].clip_lower(0)
    df["Turover"] = df["Turover"].clip_lower(0)

    return df


def __transactionKeepUsefulColumns(df):
    oldColumnNames = [
        "MDDate", "MDTime", "TradeBuyNo", "TradeSellNo", "TradeType", "TradeBSFlag", "TradePrice", "TradeQty",
        "HTSCSecurityID",
    ]
    newColumnNames = [
        "Date", "Time", "BidOrder", "AskOrder", "TradeType", "BSFlag", "Price", "Volume", "Code",
    ]

    df = df.loc[:, oldColumnNames]
    df.columns = newColumnNames

    return df


def __appendTimeStamp(df):
    dfDatetime = pd.to_datetime(df["Date"] + df["Time"], format="%Y%m%d%H%M%S%f")
    df["TimeStamp"] = (dfDatetime - dt.datetime(1970, 1, 1)).dt.total_seconds() - 28800

    return df


if __name__ == "__main__":
    getCBTickData("110001.SH", 20200410, 20200413)
    # getCBTransactionData("113526.SH", 20200413, 20200413)

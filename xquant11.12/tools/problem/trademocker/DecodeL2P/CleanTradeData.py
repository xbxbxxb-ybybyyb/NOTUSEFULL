#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/2/5 14:04
import datetime as dt
import numpy as np
import pandas as pd


def tickDataKeepUsefulColumns(df):
    oldColumnNames = [
        "MDDate", "MDTime", "TradingPhaseCode", "PreClosePx", "TotalVolumeTrade", "TotalValueTrade", "LastPx",
        "OpenPx", "HighPx", "LowPx", "MaxPx", "MinPx", "HTSCSecurityID", "Buy1Price", "Buy1OrderQty", "Sell1Price",
        "Sell1OrderQty", "Buy2Price", "Buy2OrderQty", "Sell2Price", "Sell2OrderQty", "Buy3Price",
        "Buy3OrderQty", "Sell3Price", "Sell3OrderQty", "Buy4Price", "Buy4OrderQty", "Sell4Price", "Sell4OrderQty",
        "Buy5Price", "Buy5OrderQty", "Sell5Price", "Sell5OrderQty", "Buy6Price", "Buy6OrderQty", "Sell6Price",
        "Sell6OrderQty", "Buy7Price", "Buy7OrderQty", "Sell7Price", "Sell7OrderQty", "Buy8Price", "Buy8OrderQty",
        "Sell8Price", "Sell8OrderQty", "Buy9Price", "Buy9OrderQty", "Sell9Price", "Sell9OrderQty", "Buy10Price",
        "Buy10OrderQty", "Sell10Price", "Sell10OrderQty",
    ]
    newColumnNames = [
        "Date", "Time", "TradingPhaseCode", "PreClose", "AccVolume", "AccTurover", "Price", "Open", "High",
        "Low", "MaxP", "MinP", "Code", "BidP1", "BidV1", "AskP1", "AskV1", "BidP2", "BidV2", "AskP2",
        "AskV2", "BidP3", "BidV3", "AskP3", "AskV3", "BidP4", "BidV4", "AskP4", "AskV4", "BidP5", "BidV5",
        "AskP5", "AskV5", "BidP6", "BidV6", "AskP6", "AskV6", "BidP7", "BidV7", "AskP7", "AskV7", "BidP8",
        "BidV8", "AskP8", "AskV8", "BidP9", "BidV9", "AskP9", "AskV9", "BidP10", "BidV10", "AskP10", "AskV10",
    ]

    df = df.loc[:, oldColumnNames]
    df.columns = newColumnNames

    return df

def tickDataOHLFilter(df):
    mask1 = df["Open"] == 0
    mask2 = df["High"] == 0
    mask3 = df["Low"] == 0
    mask = ~(mask1 | mask2 | mask3)

    return df.loc[mask, :]

def tickDataAppendVolumeNTurover(df):
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

def transactionKeepUsefulColumns(df):
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

def appendTimeStamp(df):
    dfDatetime = pd.to_datetime(df["Date"] + df["Time"], format="%Y%m%d%H%M%S%f")
    df["TimeStamp"] = (dfDatetime - dt.datetime(1970, 1, 1)).dt.total_seconds() - 28800

    return df

def clean_market_tick_data(data):
    data = data.replace({"PreClosePx": 0.0}, np.nan)
    data = data.fillna(method="ffill")

    data = tickDataKeepUsefulColumns(data)
    data = tickDataOHLFilter(data)

    data = tickDataAppendVolumeNTurover(data)
    data = appendTimeStamp(data)

    data = data.astype({"Date": "int", "Time": "int"})

    return data

def clean_market_transaction_data(data):
    data = transactionKeepUsefulColumns(data)
    data = appendTimeStamp(data)

    data = data.loc[data["TradeType"] == 0, :]
    data.loc[data["BSFlag"] == 2, "BSFlag"] = -1

    data = data.astype({"Date": int, "Time": int})

    return data
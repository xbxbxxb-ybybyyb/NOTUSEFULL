# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
INFACTOR_CONFIG = [

    {
        "FactorName": "INFAmount",
        "ClassName": "INFAmount",
        "StockGroup": "SW2",
        "DataTypeCS": "Tick"
    },

    {
        "FactorName": "INFAskDelegateVolumeRatio",
        "ClassName": "INFAskDelegateVolumeRatio",
        "StockGroup": "SW2",
        "DataTypeCS": "Tick",
        "DailyLengthCS": 1,
    },

    {
        "FactorName": "INFBidDelegateVolumeRatio",
        "ClassName": "INFBidDelegateVolumeRatio",
        "StockGroup": "SW2",
        "DataTypeCS": "Tick",
        "DailyLengthCS": 1,
    },

    {
        "FactorName": "INFLastPrice",
        "ClassName": "INFLastPrice",
        "StockGroup": "SW2",
        "DataTypeCS": "Tick",
        "DailyLengthCS": 1,
    },

    {
        "FactorName": "INFLastPriceRatioWeighted_5",
        "ClassName": "INFLastPriceRatioWeighted",
        "StockGroup": "SW2",
        "DataTypeCS": "Tick",
        "DailyLengthCS": 4,
        "Parameters": {
            "DayLag": 5
        }
    },

    {
        "FactorName": "INFLastPriceTsRankMean_20",
        "ClassName": "INFLastPriceTsRankMean",
        "StockGroup": "SW2",
        "DataTypeCS": "Tick",
        "DailyLengthCS": 20,
        "Parameters": {
            "DayLag": 20
        }
    },

    {
        "FactorName": "INFMidPriceReturnsRank_900",
        "ClassName": "INFMidPriceReturnsRank",
        "StockGroup": "SW2",
        "DataTypeCS": "Tick",
        "Parameters": {
            "Lag": 900,  # 15min
            "IndexName": "SW2"
        }
    },

    {
        "FactorName": "INFMidPriceReturnsRank_300",
        "ClassName": "INFMidPriceReturnsRank",
        "StockGroup": "SW2",
        "DataTypeCS": "Tick",
        "Parameters": {
            "Lag": 300,  # 5min
            "IndexName": "SW2"
        }
    },

    {
        "FactorName": "INFMidPriceReturnsSkew_600",
        "ClassName": "INFMidPriceReturnsSkew",
        "StockGroup": "SW2",
        "DataTypeCS": "Tick",
        "Parameters": {
            "Lag": 600,  # 10min
            "IndexName": "SW2"
        }
    },

    {
        "FactorName": "INFTransAskVolumeRank",
        "ClassName": "INFTransAskVolumeRank",
        "StockGroup": "SW2",
        "DataTypeCS": "Tick",
    },

    {
        "FactorName": "INFTransBidVolumeRank",
        "ClassName": "INFTransBidVolumeRank",
        "StockGroup": "SW2",
        "DataTypeCS": "Tick",
    },

    {
        "FactorName": "INFTransBidVolumeRatio",
        "ClassName": "INFTransBidVolumeRatio",
        "StockGroup": "SW2",
        "DataTypeCS": "Tick",
    },

    {
        "FactorName": "INFVolume",
        "ClassName": "INFVolume",
        "StockGroup": "SW2",
        "DataTypeCS": "Tick"
    },

]
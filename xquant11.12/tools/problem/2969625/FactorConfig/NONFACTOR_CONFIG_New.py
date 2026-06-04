# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/04/17
NONFACTOR_CONFIG = [
    {
        "ClassName": "OrderEvaluate2",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "Albest",
    },
    {
        "ClassName": "EMA",
        "Owner": "Albest",
    },
    {
        "ClassName": "OrderAmountPressure",
        "DataSource": ["P"],
        "NonFactors": ["AveOrderAmountWeightedM"],
        "Owner": "Albest",
    },
    {
        "ClassName": "OrderVolumePressure",
        "DataSource": ["P"],
        "NonFactors": ["AveOrderVolumeWeightedM"],
        "Owner": "Albest",
    },
    {
        "ClassName": "AveOrderVolumeWeightedM",
        "DataSource": ["P"],
        "Owner": "Albest",
    },
    {
        "ClassName": "AveOrderAmountWeightedM",
        "DataSource": ["P"],
        "Owner": "Albest",
    },
    {
        "ClassName": "MidPrice",
        "DataSource": ["P"],
        "Owner": "Albest",
    },
    {
        "ClassName": "MidPrice",
        "DataSource": ["P"],
        "Owner": "Albest",
    },
    {
        "ClassName": "AvePrice",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPrice"],
        "Owner": "Albest",
    },
    {
        "ClassName": "MidPriceHistorical",
        "DataSource": ["P"],
        "Owner": "015619(LST)",
    },
    {
        "ClassName": "VWAPPriceAdjAllDay",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
    },
    {
        "ClassName": "AskVwap",
        "DataSource": ["P"],
        "Owner": "011668(JS)",
    },
    {
        "ClassName": "BidVwap",
        "DataSource": ["P"],
        "Owner": "011668(JS)",
    },
    {
        "ClassName": "AskVwapAdj_0.005",
        "Parameters": {
            "percentile": 0.005
        },
        "DataSource": ["P"],
        "Owner": "011668(JS)",
    },
    {
        "ClassName": "BidVwapAdj_0.005",
        "Parameters": {
            "percentile": 0.005
        },
        "DataSource": ["P"],
        "Owner": "011668(JS)",
    },
    {
        "ClassName": "MdfBidAmtPerTrade",
        "DataSource": ["TR"],
        "Owner": "018106(LYH)",
    },
    {
        "ClassName": "BidAmtPerTrade",
        "DataSource": ["TR"],
        "Owner": "018106(LYH)",
    },
    {
        "ClassName": "TickBidAmt",
        "DataSource": ["P"],
        "Owner": "018106(LYH)",
    },
    {
        "ClassName": "TradeNumWeightedM",
        "DataSource": ["T", "TR"],
        "Owner": "017023(HZW)",
    },
    {
        "ClassName": "TradeVolumeWeightedM",
        "DataSource": ["T", "TR"],
        "Owner": "017023(HZW)",
    },

]
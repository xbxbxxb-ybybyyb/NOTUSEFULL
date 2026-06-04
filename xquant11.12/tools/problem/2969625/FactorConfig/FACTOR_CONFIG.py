FACTOR_CONFIG_ZEUS = [
    # TIME SERIES
    # Submitted by 013544(HZQ)
    {
        "FactorName": "factor40PredRetBaseAmt",
        "ClassName": "Factor40PredRetBaseAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "015629(YJP)",
        'DailyLength': 1,
        'SplitAdjusted': True,
        "Parameters": {
            "WindowLong": 40,
            "WindowShort": 10
        },
    },

    {
        "FactorName": "factor200PredRetBaseAmt",
        "ClassName": "Factor200PredRetBaseAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        'DailyLength': 1,
        'SplitAdjusted': True,
        "Parameters": {
            "WindowLong": 200,
            "WindowShort": 10,
        },
    },

    {
        "FactorName": "factor40IlliqBidAmt",
        "ClassName": "Factor40IlliqBidAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["BidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015619(LST)",
        "Parameters": {
            "Window": 40
        }
    },

    {
        "FactorName": "factor100IlliqBidAmt",
        "ClassName": "Factor100IlliqBidAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["BidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015619(LST)",
        "Parameters": {
            "Window": 100
        },
    },

    {
        "FactorName": "factor100IlliqAskAmt",
        "ClassName": "Factor100IlliqAskAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["AskAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "Parameters": {
            "Window": 100
        }
    },

    {
        "FactorName": "factor200IlliqAskAmt",
        "ClassName": "Factor200IlliqAskAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["AskAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015629(YJP)",
        "Parameters": {
            "Window": 200
        }
    },

    {
        "FactorName": "factorFlex20RelAskAmtPerTrade",
        "ClassName": "FactorFlex20RelAskAmtPerTrade",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["AskAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015629(YJP)",
        "TickLength": 1,
        "Parameters": {
            "Window": 20,
            "LongWindow": 4730
        },
    },

    {
        "FactorName": "factorFlex200AskAmtPerTradeZScore",
        "ClassName": "FactorFlex200AskAmtPerTradeZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "013544(HZQ)",
        "Successor": "011668(JS)",
        "TickLength": 1,
        "Parameters": {
            "Window": 200,
            "LongWindow": 4730
        },
    },

    {
        "FactorName": "factorFlex40AskAmtPerTradeZScore",
        "ClassName": "FactorFlex40AskAmtPerTradeZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "TickLength": 1,
        "Parameters": {
            "Window": 40,
            "LongWindow": 4730
        },
    },

    {
        "FactorName": "factorFlex20BidAmtPerTradeZScore",
        "ClassName": "FactorFlex20BidAmtPerTradeZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "013544(HZQ)",
        "Successor": "015629(YJP)",
        "TickLength": 1,
        "Parameters": {
            "Window": 20,
            "LongWindow": 4730
        },
    },

    {
        "FactorName": "factorFlex100RelBidAmtPerTrade",
        "ClassName": "FactorFlex100RelBidAmtPerTrade",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["BidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "TickLength": 1,
        "Parameters": {
            "Window": 100,
            "LongWindow": 4730
        },
    },

    {
        "FactorName": "factorFlex20RelBidAmtPerTrade",
        "ClassName": "FactorFlex20RelBidAmtPerTrade",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["BidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015619(LST)",
        "TickLength": 1,
        "Parameters": {
            "Window": 20,
            "LongWindow": 4730
        },
    },

    {
        "FactorName": "factor40BidAmtPerTradeZScore",
        "ClassName": "Factor40BidAmtPerTradeZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["BidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015629(YJP)",
        "Parameters": {
            "Window": 40
        }
    },

    {
        "FactorName": "factor20BidAmtPerTradeZScore",
        "ClassName": "Factor20BidAmtPerTradeZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["BidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "Parameters": {
            "Window": 20
        }
    },

    {
        "FactorName": "factor100RelBidAmtPerTrade",
        "ClassName": "Factor100RelBidAmtPerTrade",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["BidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "Parameters": {
            "Window": 100
        }
    },

    {
        "FactorName": "factor100RelAskAmtPerTrade",
        "ClassName": "Factor100RelAskAmtPerTrade",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["AskAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015629(YJP)",
        "Parameters": {
            "Window": 100
        }
    },

    {
        "FactorName": "factor40AskAmtPerTradeStd",
        "ClassName": "Factor40AskAmtPerTradeStd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["AskAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "Parameters": {
            "Window": 40
        }
    },

    {
        "FactorName": "factor40BidAmtPerTradeStd",
        "ClassName": "Factor40BidAmtPerTradeStd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["BidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "011668(JS)",
        "Parameters": {
            "Window": 40
        }
    },

    {
        "FactorName": "factor20BidAmtPerTrade",
        "ClassName": "Factor20BidAmtPerTrade",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["BidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015619(LST)",
        "Parameters": {
            "Window": 20
        }
    },

    {
        "FactorName": "factor20AskAmtPerTrade",
        "ClassName": "Factor20AskAmtPerTrade",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["AskAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015619(LST)",
        "Parameters": {
            "Window": 20
        }
    },

    {
        "FactorName": "factor200AskAmtPerTrade",
        "ClassName": "Factor200AskAmtPerTrade",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["AskAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "Parameters": {
            "Window": 200
        }
    },

    {
        "FactorName": "factor200BidAmtPerTrade",
        "ClassName": "Factor200BidAmtPerTrade",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["BidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "011668(JS)",
        "Parameters": {
            "Window": 200
        }
    },

    {
        "FactorName": "factorAskBidNumRatioStd",
        "ClassName": "FactorAskBidNumRatioStd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "Parameters": {
            "Window": 20
        }
    },

    {
        "FactorName": "factor40PVMove",
        "ClassName": "Factor40PVMove",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "015629(YJP)",
        "Parameters": {
            "WindowLong": 40,
            "WindowShort": 20,
        },
    },

    {
        "FactorName": "factor200PVMove",
        "ClassName": "Factor200PVMove",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "Parameters": {
            "WindowLong": 200,
            "WindowShort": 100
        },
    },

    {
        "FactorName": "factor20Reverse",
        "ClassName": "Factor20Reverse",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "011668(JS)",
        'SplitAdjusted': True,
        "Parameters": {
            "WindowLong": 20,
            "WindowShort": 10
        },
    },

    {
        "FactorName": "factor200Reverse",
        "ClassName": "Factor200Reverse",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "015619(LST)",
        'SplitAdjusted': True,
        "Parameters": {
            "WindowLong": 200,
            "WindowShort": 100,
        },
    },

    {
        "FactorName": "factor40RealReverseAskAmt",
        "ClassName": "Factor40RealReverseAskAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["AskAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015629(YJP)",
        'SplitAdjusted': True,
        "Parameters": {
            "Window": 40
        },
    },

    {
        "FactorName": "factor40RealReverseBidAmt",
        "ClassName": "Factor40RealReverseBidAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["BidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015629(YJP)",
        'SplitAdjusted': True,
        "Parameters": {
            "Window": 40
        },
    },

    {
        "FactorName": "factor200RealReverseAskAmt",
        "ClassName": "Factor200RealReverseAskAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["AskAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "011668(JS)",
        'SplitAdjusted': True,
        "Parameters": {
            "Window": 200
        },
    },

    {
        "FactorName": "factor200RealReverseBidAmt",
        "ClassName": "Factor200RealReverseBidAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["BidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015619(LST)",
        'SplitAdjusted': True,
        "Parameters": {
            "Window": 200
        },
    },

    {
        "FactorName": "factorPriceVolumeRatio",
        "ClassName": "FactorPriceVolumeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "015629(YJP)",
        'TickLength': 1,
        'SplitAdjusted': True,
        "Parameters": {
            "WindowShort": 200,
            "WindowLong": 400,
        }
    },

    {
        "FactorName": "factorPriceRatio",
        "ClassName": "FactorPriceRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "011668(JS)",
        "TickLength": 1,
        "SplitAdjusted": True,
        "Parameters": {
            "Window": 20,
            "AvgWindow": 5,
        }
    },

    {
        "FactorName": "factorPredPrice",
        "ClassName": "FactorPredPrice",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "TickLength": 1,
        "SplitAdjusted": True,
        "Parameters": {
            "Window": 20,
            "AvgWindow": 5
        }
    },

    {
        "FactorName": "factorLongRetWithHighVol",
        "ClassName": "FactorLongRetWithHighVol",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "Parameters": {
            "Window": 200,
            "RelWindow": 20
        }
    },

    {
        "FactorName": "factorRetWithHighVol",
        "ClassName": "FactorRetWithHighVol",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "015619(LST)",
        "Parameters": {
            "Window": 40,
            "RelWindow": 20
        }
    },

    {
        "FactorName": "factorPVCorr",
        "ClassName": "FactorPVCorr",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "015619(LST)",
        "Parameters": {
            "Window": 300,
            "ShortWindow": 100
        }
    },

    {
        "FactorName": "factorScaleVolumePCorr",
        "ClassName": "FactorScaleVolumePCorr",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "Parameters": {
            "Window": 300,
            "ShortWindow": 60
        }
    },

    {
        "FactorName": "factor200TickAmtChangePct",
        "ClassName": "FactorTickAmtChangePct",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["TickBidAmt"],
        "Owner": "013544(HZQ)",
        "Successor": "011668(JS)",
        "Parameters": {
            "Window": 200
        },
    },

    {
        "FactorName": "factor20TickAmtChangePct",
        "ClassName": "FactorTickAmtChangePct",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["TickBidAmt"],
        "Owner": "013544(HZQ)",
        "Successor": "011668(JS)",
        "Parameters": {
            "Window": 20
        },
    },

    {
        "FactorName": "factor200TickAskAmtChangePct",
        "ClassName": "FactorTickAskAmtChangePct",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["TickAskAmt"],
        "Owner": "013544(HZQ)",
        "Successor": "015619(LST)",
        "Parameters": {
            "Window": 200
        },
    },

    {
        "FactorName": "factor20TickAskAmtChangePct",
        "ClassName": "FactorTickAskAmtChangePct",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["TickAskAmt"],
        "Owner": "013544(HZQ)",
        "Successor": "015629(YJP)",
        "Parameters": {
            "Window": 20
        },
    },

    # Submitted by 015619(LST)
    {
        "FactorName": "factorDistanceToMidPBand",
        "ClassName": "FactorDistanceToMidPBand",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "T", "P"],
        "NonFactors": ["MidPrice"],
        "Owner": "015619(LST)",
        "SplitAdjusted": True,
        "MinuteLength": 5,
        "DataType": "Both",
        "Parameters": {
            "MinLag": 10,
            "VolLag": 5,
            "VolScale": 0.6
        }
    },

    {
        "FactorName": "factorDistanceToMidPBandTwoSides",
        "ClassName": "FactorDistanceToMidPBandTwoSides",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "T", "P"],
        "NonFactors": ["MidPrice"],
        "Owner": "015619(LST)",
        "SplitAdjusted": True,
        "MinuteLength": 10,
        "DataType": "Both",
        "Parameters": {
            "MinLag": 5,
            "VolLag": 10,
            "VolScale": 0.6
        }
    },

    {
        "FactorName": "factorVolumePaceRatio",
        "ClassName": "FactorVolumePaceRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "M", "T"],
        "Owner": "015619(LST)",
        "DailyLength": 10,
        "MinuteLength": 10,
        "DataType": "Both",
        "Parameters": {
            "MinLag": 1,
            "DayLag": 10
        }
    },

    {
        "FactorName": "factorSupportBreakBand",
        "ClassName": "FactorSupportBreakBand",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "T", "P"],
        "NonFactors": ["MidPrice"],
        "Owner": "015619(LST)",
        "DailyLength": 10,
        "Parameters": {
            "DayLag": 10,
            "SupScale": 0.6,
            "BreakScale": 0.8
        }
    },

    {
        "FactorName": "factorTrackVolatility",
        "ClassName": "FactorTrackVolatility",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "MinLag": 5
        }
    },

    {
        "FactorName": "factorWeightedReturns",
        "ClassName": "FactorWeightedReturns",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Tags": [1, 2, 5, 10]
        }
    },

    {
        "FactorName": "factorVolumeOutbreakCurrent",
        "ClassName": "FactorVolumeOutbreakCurrent",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "VolumeMLag": 5,
            "CompLag": 10,
            "MidPriceThrd": 0.3
        }
    },

    {
        "FactorName": "factorAdjVolumeOutbreak",
        "ClassName": "FactorAdjVolumeOutbreak",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "T", "P"],
        "NonFactors": ["MidPrice"],
        "Owner": "015619(LST)",
        "MinuteLength": 5,
        "DataType": "Both",
        "Parameters": {
            "VolumeMLag": 1,
            "VolumeDLag": 5,
            "MidPriceThrd": 0.3
        }
    },

    {
        "FactorName": "factorAskBidOrderNumberVolatility",
        "ClassName": "FactorAskBidOrderNumberVolatility",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015619(LST)",
        "Parameters": {
            "SecondLag": 200
        }
    },

    {
        "FactorName": "factorDistanceToVwapVolume",
        "ClassName": "FactorDistanceToVwapVolume",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPrice", "VWAPPrice"],
        "Owner": "015619(LST)",
        "Parameters": {
            "VolumeShortLag": 1,
            "VolumeLongLag": 10,
            "DistMinLag": 2
        }
    },

    {
        "FactorName": "factorSpeedToVwap",
        "ClassName": "FactorSpeedToVwap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPrice", "VWAPPrice"],
        "Owner": "015619(LST)",
        "Parameters": {
            "MinLag": 5,
            "MinVwapLag": 5
        }
    },

    {
        "FactorName": "factorPatternRecogProb",
        "ClassName": "FactorPatternRecogProb",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "T"],
        "Owner": "015619(LST)",
        "SplitAdjusted": True,
        "MinuteLength": 7,
        "Parameters": {
            "DayLag": 5,
            "PredictFwd": 5
        }
    },

    {
        "FactorName": "factorJumpPointBand",
        "ClassName": "FactorJumpPointBand",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "M", "T"],
        "Owner": "015619(LST)",
        "SplitAdjusted": True,
        "DailyLength": 11,
        "MinuteLength": 10,
        "DataType": "Both",
        "Parameters": {
            "DayLag": 10,
            "Scale": 0.4
        }
    },

    {
        "FactorName": "factorPositionVolatility",
        "ClassName": "FactorPositionVolatility",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "P"],
        "Owner": "015619(LST)",
        "DailyLength": 10,
        "Parameters": {
            "DayLag": 10
        }
    },

    {
        "FactorName": "factorSR",
        "ClassName": "FactorSR",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 200
        }
    },

    {
        "FactorName": "factorTickJump",
        "ClassName": "FactorTickJump",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "TickLength": 1,
        "Parameters": {
            "Lag": 150
        }
    },

    {
        "FactorName": "factorAskBidWeightedPriceDiff",
        "ClassName": "FactorAskBidWeightedPriceDiff",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "P"],
        "Owner": "015619(LST)",
        "DailyLength": 1
    },

    {
        "FactorName": "factorAskPVolumeMaxChg",
        "ClassName": "FactorAskPVolumeMaxChg",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "MinLag": 5
        }
    },

    {
        "FactorName": "factorBidPVolumeMaxChg",
        "ClassName": "FactorBidPVolumeMaxChg",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "MinLag": 5
        }
    },

    {
        "FactorName": "factorVolumeToReturnsDoD",
        "ClassName": "FactorVolumeToReturnsDoD",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "TickLength": 1,
        "Parameters": {
            "VolumeLag": 40,
            "ReturnsForw": 100
        }
    },

    {
        "FactorName": "factorVolumeReturnsMap",
        "ClassName": "FactorVolumeReturnsMap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "TickLength": 1,
        "Parameters": {
            "Lag": 40,
            "ReturnsLag": 20
        }
    },

    {
        "FactorName": "factorAskBidOrderVolumeVolatility",
        "ClassName": "FactorAskBidOrderVolumeVolatility",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 5
        }
    },

    {
        "FactorName": "factorBidDealMaxRatio",
        "ClassName": "FactorBidDealMaxRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["BidDealVolume"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 5
        }
    },

    {
        "FactorName": "factorAskDealMaxRatio",
        "ClassName": "FactorAskDealMaxRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["AskDealVolume"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 60
        }
    },

    {
        "FactorName": "factorAskDealVolumeVolatility",
        "ClassName": "FactorAskDealVolumeVolatility",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["AskDealVolume"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorBidDealDiff",
        "ClassName": "FactorBidDealDiff",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P", "TR"],
        "NonFactors": ["MidPrice"],
        "Owner": "015619(LST)",
    },

    {
        "FactorName": "factorAskDealDiff",
        "ClassName": "FactorAskDealDiff",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P", "TR"],
        "NonFactors": ["MidPrice"],
        "Owner": "015619(LST)",
    },

    {
        "FactorName": "factorBidWeightedVolumeRatio_20_5",
        "ClassName": "FactorBidWeightedVolumeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "ShortVolumeLag": 5,
            "LongVolumeLag": 20
        }
    },

    {
        "FactorName": "factorAskWeightedVolumeRatio_20_5",
        "ClassName": "FactorAskWeightedVolumeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "ShortVolumeLag": 5,
            "LongVolumeLag": 20
        }
    },

    {
        "FactorName": "factorAskDealPVolumeMaxChg_20",
        "ClassName": "FactorAskDealPVolumeMaxChg",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P", "TR"],
        "NonFactors": ["BidPVolume"],
        "Owner": "015619(LST)",
        "Parameters": {
            "MinLag": 20,
        }
    },

    {
        "FactorName": "factorBidDealPVolumeMaxChg_20",
        "ClassName": "FactorBidDealPVolumeMaxChg",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P", "TR"],
        "NonFactors": ["AskPVolume"],
        "Owner": "015619(LST)",
        "Parameters": {
            "MinLag": 20
        }
    },

    {
        "FactorName": "factorAskPVolumeMaxChgUpd_20",
        "ClassName": "FactorAskPVolumeMaxChgUpd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "MinLag": 20,
        }
    },

    {
        "FactorName": "factorBidPVolumeMaxChgUpd_20",
        "ClassName": "FactorBidPVolumeMaxChgUpd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "MinLag": 20
        }
    },

    {
        "FactorName": "factorBidIncremtActiveVolume_10",
        "ClassName": "FactorBidIncremtActiveVolume",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P", "TR"],
        "NonFactors": ["BidVolumeDeltaSelfSide", "BidVolumeDeltaOtherSide"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 10
        }
    },

    {
        "FactorName": "factorAskIncremtActiveVolume_10",
        "ClassName": "FactorAskIncremtActiveVolume",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P", "TR"],
        "NonFactors": ["AskVolumeDeltaSelfSide", "AskVolumeDeltaOtherSide"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 10
        }
    },

    {
        "FactorName": "factorAskBidVolumeRatioOtherSides_10",
        "ClassName": "FactorAskBidVolumeRatioOtherSides",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "TR"],
        "NonFactors": ["BidVolumeDeltaOtherSide", "AskVolumeDeltaOtherSide"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 10,
        }
    },

    {
        "FactorName": "factorPositionChangeRatio_10",
        "ClassName": "FactorPositionChangeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 10
        }
    },

    {
        "FactorName": "factorCandleReturnsMax_200_20",
        "ClassName": "FactorCandleReturnsMax",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPriceWeighted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 200,
            "Window": 20
        }
    },

    {
        "FactorName": "factorCandleReturnsMin_200_20",
        "ClassName": "FactorCandleReturnsMin",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPriceWeighted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 200,
            "Window": 20
        }
    },

    {
        "FactorName": "factorCandleUpDownwardVolatilityRatio_200_20",
        "ClassName": "FactorCandleUpDownwardVolatilityRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPriceWeighted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 200,
            "Window": 20
        }
    },

    {
        "FactorName": "factorMountValleyReturns_20",
        "ClassName": "FactorMountValleyReturns",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPriceWeighted", "MountValleyMidpW"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Window": 20
        }
    },

    {
        "FactorName": "factorMountValleyReturnsLocal_20",
        "ClassName": "FactorMountValleyReturnsLocal",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPriceWeighted", "MountValleyMidpW"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Window": 20
        }
    },

    {
        "FactorName": "factorMountValleyContinuity_30",
        "ClassName": "FactorMountValleyContinuity",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPriceWeighted", "MountValleyMidpW"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Window": 30,
        }
    },

    {
        "FactorName": "factorTransDistanceHighToVwap",
        "ClassName": "FactorTransDistanceHighToVwap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["TransVwap", "TransHighPrice"],
        "Owner": "015619(LST)",
        "Parameters": {
            "LltLag": 5,
        }
    },

    {
        "FactorName": "factorTransDistanceLowToVwap",
        "ClassName": "FactorTransDistanceLowToVwap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["TransVwap", "TransLowPrice"],
        "Owner": "015619(LST)",
        "Parameters": {
            "LltLag": 5,
        }
    },

    {
        "FactorName": "factorPVCoordRatio_200",
        "ClassName": "FactorPVCoordRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR", "T"],
        "NonFactors": ["TransVwap"],
        "Owner": "015619(LST)",
        "SplitAdjusted": True,
        "TickLength": 1,
        "Parameters": {
            "Lag": 200,
        }
    },

    {
        "FactorName": "factorReturnsMagnification_15_8",
        "ClassName": "FactorReturnsMagnification",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["KLineHighLive", "KLineLowLive", "MidPriceWeighted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "KLineLag": 15,
            "KLineNumber": 8,
        }
    },

    {
        "FactorName": "factorMountValleyLinearPrediction_20",
        "ClassName": "FactorMountValleyLinearPrediction",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPriceWeighted", "MountValleyMidpW"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Window": 20,
        }
    },

    {
        "FactorName": "factorAskBidIncremtDVolume_5",
        "ClassName": "FactorAskBidIncremtDVolume",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskIncremtDelegateVolume", "BidIncremtDelegateVolume"],
        "Owner": "015619(LST)",
        "Parameters": {
            "LltLag": 5,
        }
    },

    {
        "FactorName": "factorMidpwToLLTs",
        "ClassName": "FactorMidpwToLLTs",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["LLTFilter", "MidPriceWeighted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "LLTLag": 5,
        }
    },

    {
        "FactorName": "factorMidpwLLTsGapMax_20",
        "ClassName": "FactorMidpwLLTsGapMax",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["LLTFilter", "MidPriceWeighted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 20,
            "LLTLag": 5,
        }
    },

    {
        "FactorName": "factorMidpwLLTsGapMin_20",
        "ClassName": "FactorMidpwLLTsGapMin",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["LLTFilter", "MidPriceWeighted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 20,
            "LLTLag": 5,
        }
    },

    {
        "FactorName": "factorFFTLoc_1024",
        "ClassName": "FactorFFTLoc",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "D"],
        "Owner": "015619(LST)",
        "DailyLength": 1,
        "TickLength": 1,
        "SplitAdjusted": True,
        "Parameters": {
            "Lag": 1024,
        }
    },

    {
        "FactorName": "factorBid1ConsumptionRate_10",
        "ClassName": "FactorBid1ConsumptionRate",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["AskPVolume"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 10,
        }
    },

    {
        "FactorName": "factorAsk1ConsumptionRate_10",
        "ClassName": "FactorAsk1ConsumptionRate",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["BidPVolume"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 10,
        }
    },

    {
        "FactorName": "factorCandleShadowRatioSkew_30_300",
        "ClassName": "FactorCandleShadowRatioSkew",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "NonFactors": ["KLineHighLive", "KLineLowLive", "KLineOpenLive"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 300,
            "KLineLag": 30,
        }
    },

    {
        "FactorName": "factorCandleHighLoc_200",
        "ClassName": "FactorCandleHighLoc",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "NonFactors": ["KLineHighLive"],
        "Owner": "015619(LST)",
        "Parameters": {
            "KLineLag1": 20,
            "KLineLag2": 40,
            "KLineLag3": 100,
            "KLineLag4": 200,
        }
    },

    {
        "FactorName": "factorCandleLowLoc_400",
        "ClassName": "FactorCandleLowLoc",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "NonFactors": ["KLineLowLive"],
        "Owner": "015619(LST)",
        "Parameters": {
            "KLineLag1": 40,
            "KLineLag2": 100,
            "KLineLag3": 200,
            "KLineLag4": 400,
        }
    },

    {
        "FactorName": "factorVolStratifiedReturnsRatio_100",
        "ClassName": "FactorVolStratifiedReturnsRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPriceWeighted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 100
        }
    },

    {
        "FactorName": "factorAskDelegatePWToBid1",
        "ClassName": "FactorAskDelegatePWToBid1",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015619(LST)",
    },

    {
        "FactorName": "factorBidDelegatePWToAsk1",
        "ClassName": "FactorBidDelegatePWToAsk1",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015619(LST)",
    },

    {
        "FactorName": "factorBidBigDealAmountRatio_200_5",
        "ClassName": "FactorBidBigDealAmountRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["TransActiveBidOrderInfo"],
        "Owner": "015619(LST)",
        "Parameters": {
            "ShortLag": 5,
            "LongLag": 200,
        }
    },

    {
        "FactorName": "factorBidOrderPAmtQuantile",
        "ClassName": "FactorBidOrderPAmtQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["TransActiveBidOrderInfo"],
        "Owner": "015619(LST)",
        "Parameters": {
            "SmoothLag": 3,
        }
    },

    {
        "FactorName": "factorABDealAmountStructure_5",
        "ClassName": "FactorABDealAmountStructure",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["TransDelegateAsk1OrderQueue", "TransDelegateBid1OrderQueue"],
        "Owner": "015619(LST)",
        "Parameters": {
            "MinLag": 5,
        }
    },

    {
        "FactorName": "factorABDealOrderNumRatio_10",
        "ClassName": "FactorABDealOrderNumRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["TransDelegateAsk1OrderQueue", "TransDelegateBid1OrderQueue"],
        "Owner": "015619(LST)",
        "Parameters": {
            "MinLag": 10,
        }
    },

    {
        "FactorName": "factorIncremtBidOrderVolumeHD",
        "ClassName": "FactorIncremtBidOrderVolumeHD",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR", "T", "P"],
        "Owner": "015619(LST)",
        "TickLength": 1,
        "Parameters": {
            "Lag": 20,
            "NumGroups": 5,
        },
    },

    {
        "FactorName": "factorIncremtAskOrderVolumeHD",
        "ClassName": "FactorIncremtAskOrderVolumeHD",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR", "T", "P"],
        "Owner": "015619(LST)",
        "TickLength": 1,
        "Parameters": {
            "Lag": 10,
            "NumGroups": 5,
        },
    },

    {
        "FactorName": "factorAggClusteringEuclid",
        "ClassName": "FactorAggClusteringEuclid",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "T"],
        "Owner": "015619(LST)",
        "MinuteLength": 10,
        "DataType": "Both",
        "Parameters": {
            "Lags": [20, 40, 100, 200, 400],
            "MinuteLags": [1, 2, 5, 10, 20],
            "MinuteStep": 5,
            "NumClusters": 20,
        }
    },

    {
        "FactorName": "factorACTBTopQuantile",
        "ClassName": "FactorACTBTopQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "TR"],
        "NonFactors": ["ActiveABInfoByOrderSmoother", "ActiveBidInfoByOrder"],
        "Owner": "015619(LST)",
        "MinuteLength": 1,
        "Parameters": {
            "TransLag": 5,
        }
    },

    {
        "FactorName": "factorACTBTopRatio",
        "ClassName": "FactorACTBTopRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "TR"],
        "NonFactors": ["ActiveABInfoByOrderSmoother", "ActiveBidInfoByOrder"],
        "Owner": "015619(LST)",
        "MinuteLength": 1,
        "Parameters": {
            "TransLag": 5,
            "Lag": 100,
        }
    },

    {
        "FactorName": "factorACTBTimeToTop",
        "ClassName": "FactorACTBTimeToTop",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "TR", "T"],
        "NonFactors": ["ActiveBidInfoByOrder"],
        "Owner": "015619(LST)",
        "MinuteLength": 1,
        "Parameters": {
            "Lag": 100,
        }
    },

    {
        "FactorName": "factorACTBTopVwapTrend",
        "ClassName": "FactorACTBTopVwapTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "TR"],
        "NonFactors": ["ActiveABInfoByOrderSmoother", "ActiveBidInfoByOrder"],
        "Owner": "015619(LST)",
        "MinuteLength": 1,
        "Parameters": {
            "TransLag": 5,
            "Lag": 40,
        }
    },

    {
        "FactorName": "factorACTNetTopQuantile",
        "ClassName": "FactorACTNetTopQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "TR"],
        "NonFactors": ["ActiveABInfoByOrderSmoother", "ActiveBidInfoByOrder", "ActiveAskInfoByOrder"],
        "Owner": "015619(LST)",
        "MinuteLength": 1,
        "Parameters": {
            "TransLag": 5,
            "Lag": 100,
        }
    },

    {
        "FactorName": "factorACTATailQuantile",
        "ClassName": "FactorACTATailQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "TR"],
        "NonFactors": ["ActiveABInfoByOrderSmoother", "ActiveBidInfoByOrder"],
        "Owner": "015619(LST)",
        "MinuteLength": 1,
        "Parameters": {
            "TransLag": 5,
        }
    },

    {
        "FactorName": "factorACTNetTailQuantile",
        "ClassName": "FactorACTNetTailQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "TR"],
        "NonFactors": ["ActiveABInfoByOrderSmoother", "ActiveBidInfoByOrder", "ActiveAskInfoByOrder"],
        "Owner": "015619(LST)",
        "MinuteLength": 1,
        "Parameters": {
            "TransLag": 5,
            "Lag": 100,
        }
    },

    {
        "FactorName": "factorSpeedMidpwToVwap",
        "ClassName": "FactorSpeedMidpwToVwap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPriceWeighted", "VWAPPrice"],
        "Owner": "015619(LST)",
        "Parameters": {
            "MinLag": 1,
            "MinVwapLag": 1
        }
    },

    {
        "FactorName": "factorCandleUpDownwardExtremeRatio_50_5",
        "ClassName": "FactorCandleUpDownwardExtremeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPriceWeighted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 50,
            "Window": 5,
            "EMALag": 10,
        }
    },

    {
        "FactorName": "factorAskAmountPerTradeDoD",
        "ClassName": "FactorAskAmountPerTradeDoD",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "TR"],
        "NonFactors": ["AskDealAmount"],
        "Owner": "015619(LST)",
        "MinuteLength": 10,
        "Parameters": {
            "Lag": 40,
        }
    },

    {
        "FactorName": "factorBidAmountPerTradeDoD",
        "ClassName": "FactorBidAmountPerTradeDoD",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "TR"],
        "NonFactors": ["BidDealAmount"],
        "Owner": "015619(LST)",
        "MinuteLength": 10,
        "Parameters": {
            "Lag": 40,
        }
    },

    {
        "FactorName": "factorAskBidRatioAmountPerTrade",
        "ClassName": "FactorAskBidRatioAmountPerTrade",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["BidDealAmount", "AskDealAmount"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorAskAmountPerTradeQuantile",
        "ClassName": "FactorAskAmountPerTradeQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["AskDealAmount"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorAskActiveAmountRatio",
        "ClassName": "FactorAskActiveAmountRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["AskDealAmount", "ActiveAskInfoByOrder"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 20,
        },
    },

    {
        "FactorName": "factorBidActiveAmountRatio",
        "ClassName": "FactorBidActiveAmountRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["BidDealAmount", "ActiveBidInfoByOrder"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 20,
        },
    },

    {
        "FactorName": "factorBidOrderVolumeQuantile",
        "ClassName": "FactorBidOrderVolumeQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015619(LST)",
    },

    {
        "FactorName": "factorAskOrderVolumeQuantile",
        "ClassName": "FactorAskOrderVolumeQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015619(LST)",
    },

    {
        "FactorName": "factorBidActiveOVToBQuantile",
        "ClassName": "FactorBidActiveOVToBQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O", "P"],
        "NonFactors": ["Bid1Price"],
        "Owner": "015619(LST)",
    },

    {
        "FactorName": "factorBidDealWaitingTime",
        "ClassName": "FactorBidDealWaitingTime",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O", "TR"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorAskDealWaitingTime",
        "ClassName": "FactorAskDealWaitingTime",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O", "TR"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 40,
        }
    },

    {
        "FactorName": "factorAskNumVolumePKWPR",
        "ClassName": "FactorAskNumVolumePKWPR",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 40,
        }
    },

    {
        "FactorName": "factorBidMaxQuoteVPRatio",
        "ClassName": "FactorBidMaxQuoteVPRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 1200,
        }
    },

    {
        "FactorName": "factorBidMaxQuoteVPToMidpw",
        "ClassName": "FactorBidMaxQuoteVPToMidpw",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["MidPriceWeighted"],
        "Owner": "015619(LST)",
    },

    {
        "FactorName": "factorAskMaxQuoteVPToMidpw",
        "ClassName": "FactorAskMaxQuoteVPToMidpw",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["MidPriceWeighted"],
        "Owner": "015619(LST)",
    },

    {
        "FactorName": "factorBidAggrNewOrderVolumeQuantile",
        "ClassName": "FactorBidAggrNewOrderVolumeQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T", "O", "TR"],
        "NonFactors": ["Bid1PriceTransAdjusted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 10,
        }
    },

    {
        "FactorName": "factorAskBidMildOrderRatio",
        "ClassName": "FactorAskBidMildOrderRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T", "O", "TR"],
        "NonFactors": ["Bid1PriceTransAdjusted", "Ask1PriceTransAdjusted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 5,
        }
    },

    {
        "FactorName": "factorAskAggrMildOrderVRatio",
        "ClassName": "FactorAskAggrMildOrderVRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T", "O", "TR"],
        "NonFactors": ["Ask1PriceTransAdjusted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorBidAggrMildOrderVRatio",
        "ClassName": "FactorBidAggrMildOrderVRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T", "O", "TR"],
        "NonFactors": ["Bid1PriceTransAdjusted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 60,
        }
    },

    {
        "FactorName": "factorAskBidAggrOrderRatio",
        "ClassName": "FactorAskBidAggrOrderRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T", "O", "TR"],
        "NonFactors": ["Bid1PriceTransAdjusted", "Ask1PriceTransAdjusted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "SmoothLag": 10,
        }
    },

    {
        "FactorName": "factorBidAggrCancelVolumeQuantile",
        "ClassName": "FactorBidAggrCancelVolumeQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T", "C", "TR"],
        "NonFactors": ["CancellationPriceST", "CancelOrderTimeST", "Bid1PriceTransAdjusted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 5,
            "SmoothLag": 5,
        }
    },

    {
        "FactorName": "factorBidAggrCancelNumQuantile",
        "ClassName": "FactorBidAggrCancelNumQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T", "C", "TR"],
        "NonFactors": ["CancellationPriceST", "CancelOrderTimeST", "Bid1PriceTransAdjusted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 1,
            "SmoothLag": 5,
        }
    },

    {
        "FactorName": "factorBidMaxOAmtCurrentCumRatio",
        "ClassName": "FactorBidMaxOAmtCurrentCumRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorBidOfferCumAmountRatio",
        "ClassName": "FactorBidOfferCumAmountRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorOfferMaxAmtCurrentCumRatio",
        "ClassName": "FactorOfferMaxAmtCurrentCumRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 5,
            "SmoothLag": 2,
        }
    },

    # Submitted by 016688(JS)
    {
        "FactorName": "factorAmtRatioPerPrice60",
        "ClassName": "FactorAmtRatioPerPrice",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 10,
            "Lag2": 60
        }
    },

    {
        "FactorName": "factorEntrustRatio200",
        "ClassName": "FactorEntrustRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 200,
            "Lag2": 20
        }
    },

    {
        "FactorName": "factorHighDistance600",
        "ClassName": "FactorHighDistance",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 600
        }
    },

    {
        "FactorName": "factorMidPriceSkew300",
        "ClassName": "FactorMidPriceSkew",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 300
        }
    },

    {
        "FactorName": "factorRet20Max120",
        "ClassName": "FactorRetMax",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 120,
            "Lag2": 20
        }
    },

    {
        "FactorName": "factorRet60Max300",
        "ClassName": "FactorRetMax",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 300,
            "Lag2": 60
        }
    },

    {
        "FactorName": "factorRet20MaxMinSum120",
        "ClassName": "FactorRetMaxMinSum",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 120,
            "Lag2": 20
        }
    },

    {
        "FactorName": "factorRet60MaxMinSum300",
        "ClassName": "FactorRetMaxMinSum",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 300,
            "Lag2": 60
        }
    },

    {
        "FactorName": "factorRiseCo60MulRoc40",
        "ClassName": "FactorRiseCoMulRoc",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60,
            "LagRoc": 40
        }
    },

    {
        "FactorName": "factorRiseCoordination90",
        "ClassName": "FactorRiseCoordination",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 90
        }
    },

    {
        "FactorName": "factorSqrtTurnPerPrice60",
        "ClassName": "FactorSqrtTurnPerPrice",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "DailyLength": 1,
        "Parameters": {
            "Lag": 60
        }
    },

    {
        "FactorName": "factorRet20Mean200",
        "ClassName": "FactorRetMean",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 200,
            "Lag2": 20
        }
    },

    {
        "FactorName": "factorRet20SR200",
        "ClassName": "FactorRetSR",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 300,
            "Lag2": 30
        }
    },

    {
        "FactorName": "factorRet20Std200",
        "ClassName": "FactorRetStd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 200,
            "Lag2": 20
        }
    },

    {
        "FactorName": "factorRet2Range300",
        "ClassName": "FactorRet2Range",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 300,
            "Lag2": 20
        }
    },

    {
        "FactorName": "factorRetMulVol200",
        "ClassName": "FactorRetMulVol",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 200,
            "Lag2": 20
        }
    },

    {
        "FactorName": "factorDistance2MA20",
        "ClassName": "FactorDistance2MA",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "T"],
        "Owner": "011668(JS)",
        "DailyLength": 20,
        "SplitAdjusted": True,
        "Parameters": {
            "DayLag": 20
        }
    },

    {
        "FactorName": "factorDistance2MAMulRet60",
        "ClassName": "FactorDistance2MAMulRet",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "T", "P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "DailyLength": 20,
        "SplitAdjusted": True,
        "Parameters": {
            "Lag1": 300,
            "Lag2": 60,
            "DayLag": 20
        }
    },

    {
        "FactorName": "factorPVPercentile300_10",
        "ClassName": "FactorPVPercentile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 300,
            "Lag2": 10
        }
    },


    {
        "FactorName": "factorRetWeightedByVol10_60",
        "ClassName": "FactorRetWeightedByVol",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 10,
            "Lag2": 60
        }
    },

    {
        "FactorName": "factorPricePercentileAdjByVol20",
        "ClassName": "FactorPricePercentileAdjByVol",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "T"],
        "NonFactors": ["VolDailyRatio"],
        "Owner": "011668(JS)",
        "DailyLength": 20,
        "SplitAdjusted": True,
        "Parameters": {
            "DayLag": 20,
            "TickLag": 60
        }
    },

    {
        "FactorName": "factorHighRatio",
        "ClassName": "FactorHighRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "T"],
        "Owner": "011668(JS)",
        "DailyLength": 20,
        "SplitAdjusted": True,
        "Parameters": {
            "Lag": 100,
            "DayLag": 20
        }
    },

    {
        "FactorName": "factorLowRatio",
        "ClassName": "FactorLowRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "T"],
        "Owner": "011668(JS)",
        "DailyLength": 20,
        "SplitAdjusted": True,
        "Parameters": {
            "Lag": 100,
            "DayLag": 20
        }
    },

    {
        "FactorName": "factorPricePer5",
        "ClassName": "FactorPricePer",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "T"],
        "Owner": "011668(JS)",
        "MinuteLength": 5,
        "DataType": "Both",
        "SplitAdjusted": True,
        "Parameters": {
            "DayLag": 5
        }
    },

    {
        "FactorName": "factorAvgClose2Vwap200",
        "ClassName": "FactorAvgClose2Vwap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 200
        }
    },


    {
        "FactorName": "factorVolPer5",
        "ClassName": "FactorVolPer",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "T"],
        "Owner": "011668(JS)",
        "MinuteLength": 5,
        "DataType": "Both",
        "SplitAdjusted": True,
        "Parameters": {
            "DayLag": 5
        }
    },

    {
        "FactorName": "factorAmtPressure20",
        "ClassName": "FactorAmtPressure",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorAmtMag200_60",
        "ClassName": "FactorAmtMag",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 200,
            "Lag2": 60
        }
    },

    {
        "FactorName": "factorVolStrong60_20",
        "ClassName": "FactorVolStrong",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 60,
            "Lag2": 20
        }
    },

    {
        "FactorName": "factorABPriceRatioSR30",
        "ClassName": "FactorABPriceRatioSR",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap", "BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30
        }
    },

    {
        "FactorName": "factorABStrength30_10",
        "ClassName": "FactorABStrength",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 30,
            "Lag2": 10
        }
    },

    {
        "FactorName": "factorABChangeRatio60",
        "ClassName": "FactorABChangeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap", "BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60
        }
    },

    {
        "FactorName": "factorABPriceRatio100",
        "ClassName": "FactorABPriceRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap", "BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 100
        }
    },

    {
        "FactorName": "factorAskDistance60",
        "ClassName": "FactorAskDistance",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60
        }
    },

    {
        "FactorName": "factorBidDistance60",
        "ClassName": "FactorBidDistance",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60
        }
    },

    {
        "FactorName": "factorAskTrend60",
        "ClassName": "FactorAskTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60
        }
    },

    {
        "FactorName": "factorBidTrend30",
        "ClassName": "FactorBidTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30
        }
    },

    {
        "FactorName": "factorABTrendSum40",
        "ClassName": "FactorABTrendSum",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap", "BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 40
        }
    },

    {
        "FactorName": "factorLongStrength30",
        "ClassName": "FactorLongStrength",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30
        }
    },

    {
        "FactorName": "factorShortStrength30",
        "ClassName": "FactorShortStrength",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30
        }
    },

    {
        "FactorName": "factorSellDisSR30",
        "ClassName": "FactorSellDisSR",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30
        }
    },

    {
        "FactorName": "factorSellDistanceStd20",
        "ClassName": "FactorSellDistanceStd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorBuyDistanceStd20",
        "ClassName": "FactorBuyDistanceStd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorAskDistanceMulRet60",
        "ClassName": "FactorAskDistanceMulRet",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60
        }
    },

    {
        "FactorName": "factorBidDistanceMulRet60",
        "ClassName": "FactorBidDistanceMulRet",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60
        }
    },

    {
        "FactorName": "factorMACross",
        "ClassName": "FactorMACross",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MAPrice", "MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "LagShort": 10,
            "LagLong": 30
        }

    },

    {
        "FactorName": "factorMACrossStd",
        "ClassName": "FactorMACrossStd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MAPrice", "MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "LagShort": 10,
            "LagLong": 30,
            "Lag": 30
        }
    },

    {
        "FactorName": "factorVWAPCross",
        "ClassName": "FactorVWAPCross",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["VWAPPrice", "MidPrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "LagShort": 10,
            "LagLong": 30,
            "Lag": 10
        }
    },

    {
        "FactorName": "factorAskVolPower",
        "ClassName": "FactorAskVolPower",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60,
            "LagShort": 60,
            "LagLong": 300,
        }
    },

    {
        "FactorName": "factorBidVolPower",
        "ClassName": "FactorBidVolPower",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60,
            "LagShort": 30,
            "LagLong": 300,
        }
    },

    {
        "FactorName": "factorDistance2BuyVwap",
        "ClassName": "FactorDistance2BuyVwap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 10,
        }
    },

    {
        "FactorName": "factorDistance2SellVwap",
        "ClassName": "FactorDistance2SellVwap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorAskDistanceGap",
        "ClassName": "FactorAskDistanceGap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwapNum"],
        "Owner": "011668(JS)",
        "Parameters": {
            "ShortLevel": 5,
            "LongLevel": 10,
        }
    },

    {
        "FactorName": "factorBidDistanceGap",
        "ClassName": "FactorBidDistanceGap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwapNum"],
        "Owner": "011668(JS)",
        "Parameters": {
            "ShortLevel": 3,
            "LongLevel": 10,
        }
    },

    {
        "FactorName": "factorBidFFTAngle15",
        "ClassName": "FactorBidFFTAngle",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 15,
        }
    },

    {
        "FactorName": "factorABFFTAngleLast",
        "ClassName": "FactorABFFTAngleLast",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap", "BidVwap"],
        "Owner": "011668(JS)",
    },

    {
        "FactorName": "factorAskDistanceFFTAngle",
        "ClassName": "FactorAskDistanceFFTAngle",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 16,
        }
    },

    {
        "FactorName": "factorBidDistanceFFTAngle",
        "ClassName": "FactorBidDistanceFFTAngle",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 16,
        }
    },

    {
        "FactorName": "factorAskDisDetrend",
        "ClassName": "FactorAskDisDetrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 100,
            "SmoothLag": 10,
        }
    },

    {
        "FactorName": "factorBidDisDetrend",
        "ClassName": "FactorBidDisDetrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 100,
            "SmoothLag": 10,
        }
    },

    {
        "FactorName": "factorAskDisFFTAngleMean",
        "ClassName": "FactorAskDisFFTAngleMean",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 32,
            "SmoothLag": 3,
        }
    },

    {
        "FactorName": "factorAskFFTAngle1000",
        "ClassName": "FactorAskFFTAngle",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
    },

    {
        "FactorName": "factorAskDetrend",
        "ClassName": "FactorAskDetrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30,
        }
    },

    {
        "FactorName": "factorAskDisSlope",
        "ClassName": "FactorAskDisSlope",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorBidDisSlope",
        "ClassName": "FactorBidDisSlope",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 22,
        }
    },

    {
        "FactorName": "factorAskDisToAdjVwap",
        "ClassName": "FactorAskDisToAdjVwap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["AskVwap", "VWAPPriceAdjAllDay"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 300,
        }
    },

    {
        "FactorName": "factorAskDisToVwapCorr",
        "ClassName": "FactorAskDisToVwapCorr",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["AskVwap", "AvePrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorBidDisToVwapCorr",
        "ClassName": "FactorBidDisToVwapCorr",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["BidVwap", "AvePrice"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorBidDisToMean",
        "ClassName": "FactorBidDisToMean",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 40,
        }
    },

    {
        "FactorName": "factorAskDisAll",
        "ClassName": "FactorAskDisAll",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30,
        }
    },

    {
        "FactorName": "factorBidDisMax",
        "ClassName": "FactorBidDisMax",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20,
            "Lag2": 60,
        }
    },

    {
        "FactorName": "factorAskDisMax",
        "ClassName": "FactorAskDisMax",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30,
            "Lag2": 100,
        }
    },

    {
        "FactorName": "factorAskMaxMin",
        "ClassName": "FactorAskMaxMin",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 300,
        }
    },

    {
        "FactorName": "factorBidMaxMin",
        "ClassName": "FactorBidMaxMin",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 300,
        }
    },

    {
        "FactorName": "factorAskHighLowTrend",
        "ClassName": "FactorAskHighLowTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30,
        }
    },

    {
        "FactorName": "factorBidHighLowTrend",
        "ClassName": "FactorBidHighLowTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 15,
        }
    },

    {
        "FactorName": "factorAskPerVal30",
        "ClassName": "FactorAskPerVal",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap", "BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30
        }
    },

    {
        "FactorName": "factorBidPerVal35",
        "ClassName": "FactorBidPerVal",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap", "BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 35
        }
    },

    {
        "FactorName": "factorAskPerVal120",
        "ClassName": "FactorAskPerVal",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap", "BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 120
        }
    },

    {
        "FactorName": "factorBidPerVal120",
        "ClassName": "FactorBidPerVal",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap", "BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 120
        }
    },

    {
        "FactorName": "factorOrderBSRatio",
        "ClassName": "FactorOrderBSRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 10,
        }
    },

    {
        "FactorName": "factorOrderBuyCancelRatio",
        "ClassName": "FactorOrderBuyCancelRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O", "C"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60,
        }
    },

    {
        "FactorName": "factorOrderExcessSellRatio",
        "ClassName": "FactorOrderExcessSellRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "O"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60,
        }
    },

    {
        "FactorName": "factorOrderBSRatioGap",
        "ClassName": "FactorOrderBSRatioGap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "O"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorOrderBSRatioRadical",
        "ClassName": "FactorOrderBSRatioRadical",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "O"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 5,
        }
    },

    {
        "FactorName": "factorOrderSellRate",
        "ClassName": "FactorOrderSellRate",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "O", "P"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorOrderBuyExcessRatio",
        "ClassName": "FactorOrderBuyExcessRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O", "P"],
        "NonFactors": ["BidOrderVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorOrderSellExcessRatio",
        "ClassName": "FactorOrderSellExcessRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "O"],
        "NonFactors": ["AskOrderVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorOrderAmtRatio",
        "ClassName": "FactorOrderAmtRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "O"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 5,
        }
    },

    {
        "FactorName": "factorOrderActiveBuyRatio",
        "ClassName": "FactorOrderActiveBuyRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O", "TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 5,
        }
    },

    {
        "FactorName": "factorOrderActiveSellRatio",
        "ClassName": "FactorOrderActiveSellRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O", "TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorTradeDirection",
        "ClassName": "FactorTradeDirection",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 10,
        }
    },

    {
        "FactorName": "factorWeightedBuyDis",
        "ClassName": "FactorWeightedBuyDis",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 5,
        }
    },

    {
        "FactorName": "factorBidOfferQtyRatio",
        "ClassName": "FactorBidOfferQtyRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 10,
        }
    },

    {
        "FactorName": "factorBidOfferQtyEWM",
        "ClassName": "FactorBidOfferQtyEWM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60,
        }
    },

    {
        "FactorName": "factorBidOfferQtyGap",
        "ClassName": "FactorBidOfferQtyGap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30,
        }
    },

    {
        "FactorName": "factorBidQtyRate",
        "ClassName": "FactorBidQtyRate",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60,
        }
    },

    {
        "FactorName": "factorTradeUniqueRatio",
        "ClassName": "FactorTradeUniqueRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["TradeNum"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 10,
        }
    },

    {
        "FactorName": "factorTradeUniqueRatio3",
        "ClassName": "FactorTradeUniqueRatio3",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["TradeNum"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60,
        }
    },

    {
        "FactorName": "factorTradeOnceRatioAsk",
        "ClassName": "FactorTradeOnceRatioAsk",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30,
        }
    },

    {
        "FactorName": "factorTradeOnceRatioBid",
        "ClassName": "FactorTradeOnceRatioBid",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30,
        }
    },

    {
        "FactorName": "factorTradeAmtOnceRatioAsk",
        "ClassName": "FactorTradeAmtOnceRatioAsk",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "TR", "T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 100,
        }
    },

    {
        "FactorName": "factorTradeAmtOnceRatioBid",
        "ClassName": "FactorTradeAmtOnceRatioBid",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR", "P"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 100,
        }
    },

    {
        "FactorName": "factorTradeMultiRatioAsk",
        "ClassName": "FactorTradeMultiRatioAsk",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60,
        }
    },

    {
        "FactorName": "factorTradeMultiRatioBid",
        "ClassName": "FactorTradeMultiRatioBid",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60,
        }
    },

    {
        "FactorName": "factorTradeAmtOnceRatioAsk2",
        "ClassName": "FactorTradeAmtOnceRatioAsk2",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 40,
        }
    },

    {
        "FactorName": "factorTradeAmtOnceRatioBid2",
        "ClassName": "FactorTradeAmtOnceRatioBid2",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 40,
        }
    },

    {
        "FactorName": "factorTradeOnceRatio",
        "ClassName": "FactorTradeOnceRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 300,
        }
    },

    {
        "FactorName": "factorTradeMultiRatioAsk2",
        "ClassName": "FactorTradeMultiRatioAsk2",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 150,
        }
    },

    {
        "FactorName": "factorTradeMultiRatioBid2",
        "ClassName": "FactorTradeMultiRatioBid2",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 150,
        }
    },

    {
        "FactorName": "factorTradeAmtOncePriceAsk",
        "ClassName": "FactorTradeAmtOncePriceAsk",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR", "P", "T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 80,
        }
    },

    {
        "FactorName": "factorTradeAmtOncePriceBid",
        "ClassName": "FactorTradeAmtOncePriceBid",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR", "P", "T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 80,
        }
    },

    {
        "FactorName": "factorTradeMultiPriceAsk",
        "ClassName": "FactorTradeMultiPriceAsk",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR", "P"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 100,
        }
    },

    {
        "FactorName": "factorTradeMultiPriceBid",
        "ClassName": "FactorTradeMultiPriceBid",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR", "P"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 100,
        }
    },

    {
        "FactorName": "factorTradeCompletionBidStd",
        "ClassName": "FactorTradeCompletionBidStd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60,
        }
    },

    {
        "FactorName": "factorTradeCompletionBid",
        "ClassName": "FactorTradeCompletionBid",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 200,
        }
    },

    {
        "FactorName": "factorTradeCompletionAsk",
        "ClassName": "FactorTradeCompletionAsk",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 200,
        }
    },

    {
        "FactorName": "factorTradeCompletionBidSR",
        "ClassName": "FactorTradeCompletionBidSR",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        "FactorName": "factorTradeCompletionAskSR",
        "ClassName": "FactorTradeCompletionAskSR",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20,
        }
    },

    # Submitted by 015629(YJP)
    {
        "FactorName": "factorOrderBookAskVolumeShift",
        "ClassName": "FactorOrderBookAskVolumeShift",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20,
            "Decay": 0.8
        }
    },

    {
        "FactorName": "factorOrderBookBidVolumeShift",
        "ClassName": "FactorOrderBookBidVolumeShift",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20,
            "Decay": 0.8
        }
    },

    {
        "FactorName": "factorPankouBidPressure",
        "ClassName": "FactorPankouBidPressure",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "SliceNum": 4
        }
    },

    {
        "FactorName": "factorPankouPressure",
        "ClassName": "FactorPankouPressure",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "SliceNum": 4
        }
    },

    {
        "FactorName": "factorVOI",
        "ClassName": "FactorVOI",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorAskDriveForce",
        "ClassName": "FactorAskDriveForce",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 5,
            "Lag": 20
        }
    },

    {
        "FactorName": "factorBidDriveForce",
        "ClassName": "FactorBidDriveForce",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 5,
            "Lag": 20
        }
    },

    {
        "FactorName": "factorNetDriveForceRatio",
        "ClassName": "FactorNetDriveForceRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 3
        }
    },

    {
        "FactorName": "factorBidDriveForceSharpe",
        "ClassName": "FactorBidDriveForceSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 3,
            "Lag": 20
        }
    },

    {
        "FactorName": "factorAskDriveForceSharpe",
        "ClassName": "FactorAskDriveForceSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 3,
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrderPressureConsistency",
        "ClassName": "FactorOrderPressureConsistency",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderEvaluate2", "EMA"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 10
        }
    },

    {
        "FactorName": "factorBidDriveForceConsistency",
        "ClassName": "FactorBidDriveForceConsistency",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 5,
            "Lag": 20
        }
    },

    {
        "FactorName": "factorAskDriveForceConsistency",
        "ClassName": "FactorAskDriveForceConsistency",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 5,
            "Lag": 20
        }
    },

    {
        "FactorName": "factorPriceDiffSharpe",
        "ClassName": "FactorPriceDiffSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["AvePrice", "MidPrice"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 100
        }
    },

    {
        "FactorName": "factorVolumeTopTailVwapRatio",
        "ClassName": "FactorVolumeTopTailVwapRatio",
        "TickLength": 1,
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "NonFactors": ["AvePrice"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Window": 200
        }
    },

    {
        "FactorName": "factorAskNumSharpe",
        "ClassName": "FactorAskNumSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorBidNumSharpe",
        "ClassName": "FactorBidNumSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorAskVolumeSharpe",
        "ClassName": "FactorAskVolumeSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorBidVolumeSharpe",
        "ClassName": "FactorBidVolumeSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorMeanVolumeStdRatio",
        "ClassName": "FactorMeanVolumeStdRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorPVolumeStdRatio",
        "ClassName": "FactorPVolumeStdRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 100
        }
    },

    {
        "FactorName": "factorMaPriceBollingUp",
        "ClassName": "FactorMaPriceBollingUp",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "NonFactors": ["LLTFilter", "MidPrice"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "LLTLag": 5,
            "Window": 20
        }
    },

    {
        "FactorName": "factorVolumeRatioQuantile",
        "ClassName": "FactorVolumeRatioQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 200
        }
    },

    {
        "FactorName": "factorPVolumeRatioQuantile",
        "ClassName": "FactorPVolumeRatioQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 40,
            "EMALag": 3
        }
    },

    {
        "FactorName": "factorAskVolumeRatioSharpe",
        "ClassName": "FactorAskVolumeRatioSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorBidVolumeRatioSharpe",
        "ClassName": "FactorBidVolumeRatioSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorAskVolumeRatioAngle",
        "ClassName": "FactorAskVolumeRatioAngle",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 100
        }
    },

    {
        "FactorName": "factorBidVolumeRatioAngle",
        "ClassName": "FactorBidVolumeRatioAngle",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 100
        }
    },

    {
        "FactorName": "factorPriceDiffAngle",
        "ClassName": "FactorPriceDiffAngle",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPrice", "AvePrice"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 5
        }
    },

    {
        "FactorName": "factorTransBidChip",
        "ClassName": "FactorTransBidChip",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorTradeAskSuccessRatio",
        "ClassName": "FactorTradeAskSuccessRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 5
        }
    },

    {
        "FactorName": "factorTradeBidSuccessRatio",
        "ClassName": "FactorTradeBidSuccessRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 5
        }
    },

    {
        "FactorName": "factorTransBidOrderPriceRet",
        "ClassName": "FactorTransBidOrderPriceRet",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR", "T"],
        "NonFactors": ["AvePrice", "MidPrice"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorTransBidOrderPriceRetSharpe",
        "ClassName": "FactorTransBidOrderPriceRetSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR", "T"],
        "NonFactors": ["AvePrice", "MidPrice"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorTransAskOrderPriceRetSharpe",
        "ClassName": "FactorTransAskOrderPriceRetSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR", "T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorPAskPriceRetSharpe",
        "ClassName": "FactorPAskPriceRetSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["AvePrice", "AskVwapNum"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 3,
            "Lag": 20
        }
    },

    {
        "FactorName": "factorPBidPriceRetSharpe",
        "ClassName": "FactorPBidPriceRetSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["AvePrice", "BidVwapNum"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 3,
            "Lag": 20
        }
    },

    {
        "FactorName": "factorRiseVolumeSharpe",
        "ClassName": "FactorRiseVolumeSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorPankouCrossEntropy",
        "ClassName": "FactorPankouCrossEntropy",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Size": 100,
            "Lag": 10
        }
    },

    {
        "FactorName": "factorBidDriveForceQuantile",
        "ClassName": "FactorBidDriveForceQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 3,
            "Lag": 100
        }
    },

    {
        "FactorName": "factorAskDriveForceQuantile",
        "ClassName": "FactorAskDriveForceQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 3,
            "Lag": 100
        }
    },

    {
        "FactorName": "factorPankouCorr",
        "ClassName": "FactorPankouCorr",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorWeightedVolumeRatio",
        "ClassName": "FactorWeightedVolumeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)"
    },

    {
        "FactorName": "factorPriceLevelStable",
        "ClassName": "FactorPriceLevelStable",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "LookBack": 200,
            "Lag": 20
        }
    },

    {
        "FactorName": "factorCMCorr",
        "ClassName": "FactorCMCorr",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "LookBack": 200,
            "Lag": 20
        }
    },

    {
        "FactorName": "factorAskBidPVCorr",
        "ClassName": "FactorAskBidPVCorr",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "LookBack": 300,
            "Lag": 20
        }
    },

    {
        "FactorName": "factorACTRatioStable",
        "ClassName": "FactorACTRatioStable",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorACTRatioQuantile",
        "ClassName": "FactorACTRatioQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "LookBack": 200,
            "Lag": 5
        }
    },

    {
        "FactorName": "factorACTRatioTrend",
        "ClassName": "FactorACTRatioTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorTransNetAmountTrend",
        "ClassName": "FactorTransNetAmountTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorTransBidNumRatio",
        "ClassName": "FactorTransBidNumRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "LagShort": 5,
            "Lag": 60
        }
    },

    {
        "FactorName": "factorTransAskNumRatio",
        "ClassName": "FactorTransAskNumRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "LagShort": 5,
            "Lag": 60
        }
    },

    {
        "FactorName": "factorTransBidNumTrend",
        "ClassName": "FactorTransBidNumTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorTransAskNumTrend",
        "ClassName": "FactorTransAskNumTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorPankouPressureTrend",
        "ClassName": "FactorPankouPressureTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "SliceNum": 4,
            "Lag": 20
        }
    },

    {
        "FactorName": "factorPankouPressureQuantile",
        "ClassName": "FactorPankouPressureQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "SliceNum": 4,
            "Lag": 100,
            "SLag": 5
        }
    },

    {
        "FactorName": "factorRiseVolumeTrend",
        "ClassName": "FactorRiseVolumeTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorRiseVolumeQuantile",
        "ClassName": "FactorRiseVolumeQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 60,
            "SmoothLag": 3
        }
    },

    {
        "FactorName": "factorBidVolumeTrend",
        "ClassName": "FactorBidVolumeTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorBidVolumeQuantile",
        "ClassName": "FactorBidVolumeQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 100,
            "SmoothLag": 5
        }
    },

    {
        "FactorName": "factorAskVolumeTrend",
        "ClassName": "FactorAskVolumeTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorAskVolumeQuantile",
        "ClassName": "FactorAskVolumeQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 100,
            "SmoothLag": 5
        }
    },

    {
        "FactorName": "factorOrderAskBidNumRatio",
        "ClassName": "FactorOrderAskBidNumRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
    },

    {
        "FactorName": "factorOrderBidNumTrend",
        "ClassName": "FactorOrderBidNumTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorOrderAskNumTrend",
        "ClassName": "FactorOrderAskNumTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorOrderAskNumToNumTrades",
        "ClassName": "FactorOrderAskNumToNumTrades",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrderAskBidTNumRatio",
        "ClassName": "FactorOrderAskBidTNumRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
        }
    },
    {
        "FactorName": "factorPriceToBidMaxRange",
        "ClassName": "FactorPriceToBidMaxRange",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorPriceToAskMaxRange",
        "ClassName": "FactorPriceToAskMaxRange",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorOrderBidNumQuantile",
        "ClassName": "FactorOrderBidNumQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 100,
            "SmoothLag": 5
        }
    },
    {
        "FactorName": "factorOrderAskNumQuantile",
        "ClassName": "FactorOrderAskNumQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 100,
            "SmoothLag": 5
        }
    },

    {
        "FactorName": "factorOrderAskBidNumStdRatio",
        "ClassName": "FactorOrderAskBidNumStdRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 60,
        }
    },
    {
        "FactorName": "factorOrderAskNumRatioAngle",
        "ClassName": "FactorOrderAskNumRatioAngle",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 64,
            "SmoothLag": 16
        }
    },
    {
        "FactorName": "factorOrderAskPressure",
        "ClassName": "FactorOrderAskPressure",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "SliceNum": 4
        }
    },
    {
        "FactorName": "factorOrderAskPressureTrend",
        "ClassName": "FactorOrderAskPressureTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "SliceNum": 4,
            "Lag": 20
        }
    },
    {
        "FactorName": "factorOrderAskPressureQuantile",
        "ClassName": "FactorOrderAskPressureQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "SliceNum": 4,
            "Lag": 100,
            "SmoothLag": 5
        }
    },
    {
        "FactorName": "factorOrderBidPressureQuantile",
        "ClassName": "FactorOrderBidPressureQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "SliceNum": 4,
            "Lag": 100,
            "SmoothLag": 5
        }
    },

    {
        "FactorName": "factorPriceToAskMaxStd",
        "ClassName": "FactorPriceToAskMaxStd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 60
        }
    },
    {
        "FactorName": "factorPriceToAskMax",
        "ClassName": "FactorPriceToAskMax",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 200
        }
    },
    {
        "FactorName": "factorPriceToBidMax",
        "ClassName": "FactorPriceToBidMax",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 300
        }
    },

    {
        "FactorName": "factorOrderBidNumToNumTradesRange",
        "ClassName": "FactorOrderBidNumToNumTradesRange",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrderAskNumToNumTradesRange",
        "ClassName": "FactorOrderAskNumToNumTradesRange",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrderAskBidTNumRatioRange",
        "ClassName": "FactorOrderAskBidTNumRatioRange",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrderAskBidTNumRatioTrend",
        "ClassName": "FactorOrderAskBidTNumRatioTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrderBidOfferQtyRatioTrend",
        "ClassName": "FactorOrderBidOfferQtyRatioTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrderBidOfferQtyRatioQuantile",
        "ClassName": "FactorOrderBidOfferQtyRatioQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 200,
            "SmoothLag": 5
        }
    },

    {
        "FactorName": "factorOrderAvgOfferBidPriceRet",
        "ClassName": "FactorOrderAvgOfferBidPriceRet",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)"
    },

    {
        "FactorName": "factorOrderAvgOfferBidPriceRetRange",
        "ClassName": "FactorOrderAvgOfferBidPriceRetRange",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrderAvgBidPriceBounceZscore",
        "ClassName": "FactorOrderAvgBidPriceBounceZscore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrderAvgOfferPriceBounceZscore",
        "ClassName": "FactorOrderAvgOfferPriceBounceZscore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrderAvgBidPriceBounceMax",
        "ClassName": "FactorOrderAvgBidPriceBounceMax",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 100
        }
    },

    {
        "FactorName": "factorOrderAvgOfferPriceBounceStdRatio",
        "ClassName": "FactorOrderAvgOfferPriceBounceStdRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrderOfferQtySkew",
        "ClassName": "FactorOrderOfferQtySkew",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrdAskBidNumRatio",
        "ClassName": "FactorOrdAskBidNumRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 5
        }
    },

    {
        "FactorName": "factorOrdAskBidNumStdRatio",
        "ClassName": "FactorOrdAskBidNumStdRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrdAskNumTrend",
        "ClassName": "FactorOrdAskNumTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrdBidNumTrend",
        "ClassName": "FactorOrdBidNumTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrdAskNumQuantile",
        "ClassName": "FactorOrdAskNumQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 100,
            "Window": 5
        }
    },

    {
        "FactorName": "factorOrdBidNumQuantile",
        "ClassName": "FactorOrdBidNumQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 100,
            "Window": 5
        }
    },

    {
        "FactorName": "factorTranAskQtyCRTrend",
        "ClassName": "FactorTranAskQtyCRTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 10,
            "Window": 20
        }
    },
    {
        "FactorName": "factorTranBigBidQtyRatio",
        "ClassName": "FactorTranBigBidQtyRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 10
        }
    },

    {
        "FactorName": "factorBidSuccessNumRatio",
        "ClassName": "FactorBidSuccessNumRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorAggressiveAskTradeRatio",
        "ClassName": "FactorAggressiveAskTradeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 5
        }
    },

    {
        "FactorName": "factorAggressiveAskTradeRatioTrend",
        "ClassName": "FactorAggressiveAskTradeRatioTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrdAskOrderSkew",
        "ClassName": "FactorOrdAskOrderSkew",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 10
        }
    },

    {
        "FactorName": "factorOrdBidOrderSkew",
        "ClassName": "FactorOrdBidOrderSkew",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 10
        }
    },

    {
        "FactorName": "factorOrdBigBidRatio",
        "ClassName": "FactorOrdBigBidRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 10,
            "Window": 5
        }
    },

    {
        "FactorName": "factorAskNumStable",
        "ClassName": "FactorAskNumStable",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20,
            "ShortLag": 5
        }
    },

    {
        "FactorName": "factorBidNumStable",
        "ClassName": "FactorBidNumStable",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20,
            "ShortLag": 5
        }
    },

    {
        "FactorName": "factorAskVolumeStable",
        "ClassName": "FactorAskVolumeStable",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20,
            "ShortLag": 5
        }
    },

    {
        "FactorName": "factorBidVolumeStable",
        "ClassName": "FactorBidVolumeStable",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20,
            "ShortLag": 5
        }
    },

    {
        "FactorName": "factorOrdAskOrderVolumeTrend",
        "ClassName": "FactorOrdAskOrderVolumeTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrdBidOrderVolumeTrend",
        "ClassName": "FactorOrdBidOrderVolumeTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrdAskOrderNumStable",
        "ClassName": "FactorOrdAskOrderNumStable",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 40,
            "ShortLag": 10
        }
    },

    {
        "FactorName": "factorOrdBidOrderNumStable",
        "ClassName": "FactorOrdBidOrderNumStable",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 40,
            "ShortLag": 10
        }
    },

    {
        "FactorName": "factorOrdAskBidAggressiveRatio",
        "ClassName": "FactorOrdAskBidAggressiveRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 60
        }
    },

    {
        "FactorName": "factorOrdAskBidNetAggressiveTrend20",
        "ClassName": "FactorOrdAskBidNetAggressiveTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "O", "T"],
        "NonFactors": ["OrdAskBidNetAggressive"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorOrdAskBidNetAggressiveTrend40",
        "ClassName": "FactorOrdAskBidNetAggressiveTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "O", "T"],
        "NonFactors": ["OrdAskBidNetAggressive"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 40
        }
    },

    {
        "FactorName": "factorOrdAskBidNetAggressiveRatio",
        "ClassName": "FactorOrdAskBidNetAggressiveRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "O", "T"],
        "NonFactors": ["OrdAskBidNetAggressive"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 60
        }
    },

    {
        "FactorName": "factorOrdAskBidNetAggressiveQuantile",
        "ClassName": "FactorOrdAskBidNetAggressiveQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "O", "T"],
        "NonFactors": ["OrdAskBidNetAggressive"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 60,
            "Window": 10
        }
    },

    # Submitted by 015390(HXJ)
    {
        "FactorName": "factorAskRes",
        "ClassName": "FactorAskRes",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015390(HXJ)",
    },

    {
        "FactorName": "factorBidRes",
        "ClassName": "FactorBidRes",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015390(HXJ)",
    },

    {
        "FactorName": "factorHighRes",
        "ClassName": "FactorHighRes",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T", "M"],
        "Owner": "015390(HXJ)",
        "MinuteLength": 20,
    },

    {
        "FactorName": "factorLowRes",
        "ClassName": "FactorLowRes",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T", "M"],
        "Owner": "015390(HXJ)",
        "MinuteLength": 20,
    },

    {
        "FactorName": "factorBuyActiveUpVolumeZScore",
        "ClassName": "FactorBuyActiveUpVolumeZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O", "P"],
        "NonFactors": ["BuyActiveUpVolume"],
        "Owner": "015390(HXJ)",
        "Parameters": {
            "Lag": 5,
            "Lag2": 20
        }
    },

    {
        "FactorName": "factorSellActiveDownVolumeZScore",
        "ClassName": "FactorSellActiveDownVolumeZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "O"],
        "NonFactors": ["SellActiveDownVolume"],
        "Owner": "015390(HXJ)",
        "Parameters": {
            "Lag": 5,
            "Lag2": 20
        }
    },
    {
        "FactorName": "factorBuyActiveVolumeRatio",
        "ClassName": "FactorBuyActiveVolumeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "TR", "T"],
        "NonFactors": ["BuyActiveVolume"],
        "Owner": "015390(HXJ)",
        "Parameters": {
            "Lag": 5
        }
    },
    {
        "FactorName": "factorSellActiveVolumeRatio",
        "ClassName": "FactorSellActiveVolumeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["SellActiveVolume"],
        "Owner": "015390(HXJ)",
        "Parameters": {
            "Lag": 5
        }
    },
    {
        "FactorName": "factorBuyActiveVolumeZScore",
        "ClassName": "FactorBuyActiveVolumeZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR", "P"],
        "NonFactors": ["BuyActiveVolume"],
        "Owner": "015390(HXJ)",
        "Parameters": {
            "Lag": 5,
            "Lag2": 20
        }
    },
    {
        "FactorName": "factorSellActiveVolumeZScore",
        "ClassName": "FactorSellActiveVolumeZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "TR"],
        "NonFactors": ["SellActiveVolume"],
        "Owner": "015390(HXJ)",
        "Parameters": {
            "Lag": 5,
            "Lag2": 20
        }
    },
    {
        "FactorName": "factorDistanceZScore",
        "ClassName": "FactorDistanceZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR", "P"],
        "NonFactors": ["QuoteVWAP"],
        "Owner": "015390(HXJ)",
        "Parameters": {
            "ShortWindow": 5,
            "Window": 100
        }
    },

    {
        "FactorName": "factorOrderVolumeBig",
        "ClassName": "FactorOrderVolumeBig",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["P", "O", "T"],
        "Parameters": {
            "Lag": 5
        }
    },
    {
        "FactorName": "factorBuyOrderAmtRel520",
        "ClassName": "FactorBuyOrderAmtRel",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["T", "O", "P"],
        "Parameters": {
            "Lag1": 5,
            "Lag2": 20,
        }
    },
    {
        "FactorName": "factorSellOrderAmtRel520",
        "ClassName": "FactorSellOrderAmtRel",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["T", "O", "P"],
        "Parameters": {
            "Lag1": 5,
            "Lag2": 20,
        }
    },
    {
        "FactorName": "factorBuyOrderPriceQ",
        "ClassName": "FactorBuyOrderPriceQ",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["T", "O", "P"],
    },
    {
        "FactorName": "factorDistance2MaxStd",
        "ClassName": "FactorDistance2MaxStd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["TR", "P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Window": 200,
        }
    },
    {
        "FactorName": "factorPassiveOrderRatioBuy",
        "ClassName": "FactorPassiveOrderRatioBuy",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["T", "O", "P"],
        "NonFactors": ["PassiveOrderNum"],
        "Parameters": {
            "Window": 5,
        }
    },
    {
        "FactorName": "factorPassiveOrderRatioSell",
        "ClassName": "FactorPassiveOrderRatioSell",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["T", "O", "P"],
        "NonFactors": ["PassiveOrderNum"],
        "Parameters": {
            "Window": 5,
        }
    },
    {
        "FactorName": "factorPassiveOrderRatioRelBuy",
        "ClassName": "FactorPassiveOrderRatioRelBuy",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["T", "O", "P"],
        "NonFactors": ["PassiveOrderNum"],
        "Parameters": {
            "Window": 5,
            "Lag1": 5,
            "Lag2": 20,
        }
    },
    {
        "FactorName": "factorPassiveOrderRatioRelSell",
        "ClassName": "FactorPassiveOrderRatioRelSell",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["T", "O", "P"],
        "NonFactors": ["PassiveOrderNum"],
        "Parameters": {
            "Window": 5,
            "Lag1": 5,
            "Lag2": 20,
        }
    },
    {
        "FactorName": "factorAggressiveOrderRatioBuy",
        "ClassName": "FactorAggressiveOrderRatioBuy",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["TR", "P"],
        "NonFactors": ["AggressiveOrderNum"],
        "Parameters": {
            "Window": 5,
        }
    },
    {
        "FactorName": "factorAggressiveOrderRatioSell",
        "ClassName": "FactorAggressiveOrderRatioSell",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["TR", "P"],
        "NonFactors": ["AggressiveOrderNum"],
        "Parameters": {
            "Window": 5,
        }
    },
    {
        "FactorName": "factorAggressiveOrderRatioRelBuy",
        "ClassName": "FactorAggressiveOrderRatioRelBuy",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["TR", "P"],
        "NonFactors": ["AggressiveOrderNum"],
        "Parameters": {
            "Window": 5,
            "Lag1": 5,
            "Lag2": 40,
        }
    },
    {
        "FactorName": "factorAggressiveOrderRatioRelSell",
        "ClassName": "FactorAggressiveOrderRatioRelSell",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["TR", "P"],
        "NonFactors": ["AggressiveOrderNum"],
        "Parameters": {
            "Window": 5,
            "Lag1": 5,
            "Lag2": 40,
        }
    },
    {
        "FactorName": "factorPassiveNumRatioBuy",
        "ClassName": "FactorPassiveNumRatioBuy",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["TR", "P"],
        "NonFactors": ["AggressiveOrderNum"],
        "Parameters": {
            "Lag1": 5,
            "Lag2": 20,
        }
    },
    {
        "FactorName": "factorOrderQBuy",
        "ClassName": "FactorOrderQBuy",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["T", "O", "P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 40
        }
    },
    {
        "FactorName": "factorOrderRetQBuy",
        "ClassName": "FactorOrderRetQBuy",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["T", "O", "P"],
        "NonFactors": ["MidPrice"],
    },
    {
        "FactorName": "factorRetOQtyBuy",
        "ClassName": "FactorRetOQtyBuy",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["T", "O", "P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag1": 5,
            "Lag2": 60,
        }
    },
    {
        "FactorName": "factorRetOQtySell",
        "ClassName": "FactorRetOQtySell",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["T", "O", "P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag1": 5,
            "Lag2": 60,
        }
    },
    {
        "FactorName": "factorTORatioBuy",
        "ClassName": "FactorTORatioBuy",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["P", "O", "TR"],
        "Parameters": {
            "Lag1": 5,
            "Lag2": 20,
        }
    },
    {
        "FactorName": "factorTORatioSell",
        "ClassName": "FactorTORatioSell",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["P", "O", "TR"],
        "Parameters": {
            "Lag1": 5,
            "Lag2": 20,
        }
    },
    {
        "FactorName": "factorAskCont",
        "ClassName": "FactorAskCont",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["T", "P"],
    },
    {
        "FactorName": "factorBidCont",
        "ClassName": "FactorBidCont",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["T", "P"],
    },
    {
        "FactorName": "factorBidAskQ",
        "ClassName": "FactorBidAskQ",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["P"],
    },
    {
        "FactorName": "factorNetOrderCont20",
        "ClassName": "FactorNetOrderCont",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["O"],
        "Parameters": {
            "Lag": 20,
        }
    },
    {
        "FactorName": "factorNetOrderCont40",
        "ClassName": "FactorNetOrderCont",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["O"],
        "Parameters": {
            "Lag": 40,
        }
    },
    {
        "FactorName": "factorMDDRelBuy",
        "ClassName": "FactorMDDRelBuy",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["P", "T"],
        "Parameters": {
            "Lag1": 5,
            "Lag2": 100,
        }
    },

    # Submitted by 018187(YY)
    {
        "FactorName": "factorBidOrderK10",
        "ClassName": "FactorBidOrderK",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 10
        }
    },
    {
        "FactorName": "factorBidOrderK20",
        "ClassName": "FactorBidOrderK",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorAskOrderK10",
        "ClassName": "FactorAskOrderK",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 10
        }
    },
    {
        "FactorName": "factorAskOrderK20",
        "ClassName": "FactorAskOrderK",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorAskTrK15",
        "ClassName": "FactorAskTrK",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 15
        }
    },

    {
        "FactorName": "factorAskTrK20",
        "ClassName": "FactorAskTrK",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorBidTrK10",
        "ClassName": "FactorBidTrK",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 10
        }
    },

    {
        "FactorName": "factorBidTrK30",
        "ClassName": "FactorBidTrK",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 30
        }
    },

    {
        "FactorName": "factorOrderFlowK8",
        "ClassName": "FactorOrderFlowK",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 8
        }
    },

    {
        "FactorName": "factorOrderFlowK13",
        "ClassName": "FactorOrderFlowK",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 13
        }
    },

    {
        "FactorName": "factorPanFlowK5",
        "ClassName": "FactorPanFlowK",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 5
        }
    },

    {
        "FactorName": "factorPanFlowK20",
        "ClassName": "FactorPanFlowK",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorOrderBidVolumeToAvg30",
        "ClassName": "FactorOrderBidVolumeToAvg",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 30
        }
    },

    {
        "FactorName": "factorDistanceToOrderVWAP30",
        "ClassName": "FactorDistanceToOrderVWAP",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O", "P"],
        "NonFactor": ["MidPrice"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 30
        }
    },

    {
        "FactorName": "factorOrderAskAmountK13",
        "ClassName": "FactorOrderAskAmountK",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 13
        }
    },

    {
        "FactorName": "factorOrderBidAmountK13",
        "ClassName": "FactorOrderBidAmountK",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {
            "Lag": 13
        }
    },

    {
        "FactorName": "factorGapRatio",
        "ClassName": "FactorGapRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "NonFactor": ["MidPrice"],
        "DataSource": ["P"],
        "Owner": "018187(YY)",

    },

    # PANEL
    # Submitted by 013544(HZQ)
    {
        "FactorName": "factorPnl40AskRetRel_SW2",
        "ClassName": "FactorPnlAskRetRel",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["TR", "T"],
        "NonFactors": ["AskAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        'INFGroup': {
            'SW2': ["LastPrice"]
        },
        "Parameters": {
            "Window": 40,
            "ShortWindow": 10,
            "IndexWindow": 120,
            "IndexName": "SW2",
        },
    },

    {
        "FactorName": "factorPnl200AskRetRel_SW2",
        "ClassName": "FactorPnlAskRetRel",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["TR", "T"],
        "NonFactors": ["AskAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015619(LST)",
        'INFGroup': {
            'SW2': ["LastPrice"]
        },
        "Parameters": {
            "Window": 200,
            "ShortWindow": 10,
            "IndexWindow": 600,
            "IndexName": "SW2",
        },
    },

    {
        "FactorName": "factorPnl40BidRetRel_SW2",
        "ClassName": "FactorPnlBidRetRel",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["TR", "T"],
        "NonFactors": ["BidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "INFGroup": {
            'SW2': ["LastPrice"]
        },
        "Parameters": {
            "Window": 40,
            "ShortWindow": 10,
            "IndexWindow": 120,
            "IndexName": "SW2",
        },
    },

    {
        "FactorName": "factorPnl200BidRetRel_SW2",
        "ClassName": "FactorPnlBidRetRel",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["TR", "T"],
        "NonFactors": ["BidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "INFGroup": {
            'SW2': ["LastPrice"],
        },
        "Parameters": {
            "Window": 200,
            "ShortWindow": 10,
            "IndexWindow": 600,
            "IndexName": "SW2",
        },
    },

    {
        "FactorName": "factorPnlCrossPriceLocationRel_SW2",
        "ClassName": "FactorPnlCrossPriceLocationRel",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "011668(JS)",
        'INFGroup': {
            'SW2': ["LastPrice"],
        },
        "Parameters": {
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlReverseRel_SW2",
        "ClassName": "FactorPnlReverseRel",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "015619(LST)",
        "INFGroup": {
            "SW2": ["Volume"]
        },
        "Parameters": {
            "Window": 100,
            "IndexName": "SW2"
        },
    },

    {
        "FactorName": "factorPnlCrossPriceRankPctRel20_SW2",
        "ClassName": "FactorPnlCrossPriceRankPctRel",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "011668(JS)",
        "INFGroup": {
            'SW2': ["LastPrice"]
        },
        "Parameters": {
            "Window": 20,
            "IndexWindow": 60,
            "IndexName": "SW2",
        },
    },

    {
        "FactorName": "factorPnlCrossPriceRankPctRel200_SW2",
        "ClassName": "FactorPnlCrossPriceRankPctRel",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "011668(JS)",
        "INFGroup": {
            'SW2': ["LastPrice"]
        },
        "Parameters": {
            "Window": 200,
            "IndexWindow": 600,
            "IndexName": "SW2",
        },
    },

    {
        "FactorName": "factorPnlCrossVolumeRatioRet20_SW2",
        "ClassName": "FactorPnlCrossVolumeRatioRet",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["D", "T"],
        "Owner": "013544(HZQ)",
        "Successor": "015629(YJP)",
        "DailyLength": 5,
        "INFGroup": {
            'SW2': ["LastPrice"]
        },
        "Parameters": {
            "DayLag": 5,
            "Window": 20,
            "IndexWindow": 60,
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlCrossVolumeRatioRet200_SW2",
        "ClassName": "FactorPnlCrossVolumeRatioRet",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["D", "T"],
        "Owner": "013544(HZQ)",
        "Successor": "011668(JS)",
        "DailyLength": 5,
        "INFGroup": {
            'SW2': ["LastPrice"]
        },
        "Parameters": {
            "DayLag": 5,
            "Window": 200,
            "IndexWindow": 600,
            "IndexName": "SW2",
        }
    },

    # Submitted by 015619(LST)
    {
        "FactorName": "factorPnlRelativeReturns_SW2",
        "ClassName": "FactorPnlRelativeReturns",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "INFGroup": {
            "SW2": ["LastPrice"]
        },
        "Parameters": {
            "Lag": 100,
            "IndexLag": 300,
            "IndexName": "SW2"
        }
    },

    {
        "FactorName": "factorPnlHighDistance_SW2",
        "ClassName": "FactorPnlHighDistance",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "INFGroup": {
            "SW2": ["LastPrice"],
        },
        "Parameters": {
            "Lag": 60,
            "IndexLag": 180,
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlLowDistance_SW2",
        "ClassName": "FactorPnlLowDistance",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "INFGroup": {
            "SW2": ["LastPrice"]
        },
        "Parameters": {
            "Lag": 60,
            "IndexLag": 180,
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlAmpVolume_SW2",
        "ClassName": "FactorPnlAmpVolume",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "INFGroup": {
            "SW2": ["LastPrice"]
        },
        "Parameters": {
            "IndexLag": 120,
            "LongVLag": 200,
            "ShortVLag": 20,
            "IndexName": "SW2"
        }
    },

    {
        "FactorName": "factorPnlRelativeReturns_HS300",
        "ClassName": "FactorPnlRelativeReturns",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "DataTypeIndex": "Tick",
        "IndexGroup": ["000300.SH"],
        "Parameters": {
            "Lag": 100,
            "IndexLag": 60,
            "IndexName": "000300.SH"
        }
    },

    {
        "FactorName": "factorPnlHighDistance_HS300",
        "ClassName": "FactorPnlHighDistance",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "DataTypeIndex": "Tick",
        "IndexGroup": ["000300.SH"],
        "Parameters": {
            "Lag": 60,
            "IndexLag": 36,
            "IndexName": "000300.SH",
        }
    },

    {
        "FactorName": "factorPnlLowDistance_HS300",
        "ClassName": "FactorPnlLowDistance",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "DataTypeIndex": "Tick",
        "IndexGroup": ["000300.SH"],
        "Parameters": {
            "Lag": 60,
            "IndexLag": 36,
            "IndexName": "000300.SH",
        }
    },

    {
        "FactorName": "factorPnlLinearPrediction_SW2",
        "ClassName": "FactorPnlLinearPrediction",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "TickLengthINF": 1,
        "TickLength": 1,
        "INFGroup": {
            "SW2": ["LastPrice"]
        },
        "Parameters": {
            "MinLag": 5,
            "TicksPerMin": 20,
            "ITicksPerMin": 60,
            "RegressionLag": 200,
            "UpdateLag": 100,
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlRankVariation_SW2",
        "ClassName": "FactorPnlRankVariation",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "INFGroup": {
            "SW2": ["MidPriceReturnsRank_300"]
        },
        "DataTypeCS": "Tick",
        "Parameters": {
            "Lag": 300,
            "TrendLag": 100,
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlAskBidVolRatioPct_SW2",
        "ClassName": "FactorPnlAskBidVolRatioPct",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["TR"],
        "Owner": "015619(LST)",
        "INFGroup": {
            "SW2": ["TransAskVolumeRank", "TransBidVolumeRank"]
        },
        "Parameters": {
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlRevBidVolRatio_SW2",
        "ClassName": "FactorPnlRevBidVolRatio",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["P", "TR"],
        "NonFactors": ["MidPrice"],
        "Owner": "015619(LST)",
        "INFGroup": {
            "SW2": ["TransBidVolumeRatio"]
        },
        "Parameters": {
            "ReturnsLag": 100,
            "TransLag": 30,
            "IndexName": "SW2"
        }
    },

    {
        "FactorName": "factorPnlRelativeVolumeSum_SW2",
        "ClassName": "FactorPnlRelativeVolumeSum",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "INFGroup": {
            "SW2": ["Volume"],
        },
        "Parameters": {
            "ShortMinLag": 1,
            "LongMinLag": 10,
            "TicksPerMin": 20,
            "ITicksPerMin": 60,
            "IndexName": "SW2"
        }
    },

    {
        "FactorName": "factorPnlPassiveVolatility_SW2",
        "ClassName": "FactorPnlPassiveVolatility",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "INFGroup": {
            "SW2": ["LastPrice"]
        },
        "Parameters": {
            "MinLag": 1,
            "Lag": 100,
            "TicksPerMin": 20,
            "ITicksPerMin": 60,
            "IndexName": "SW2"
        }
    },

    {
        "FactorName": "factorTripleRelativeReturns",
        "ClassName": "FactorTripleRelativeReturns",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "DataTypeIndex": "Tick",
        "IndexGroup": ["000300.SH"],
        "INFGroup": {
            "SW2": ["LastPrice"],
        },
        "Parameters": {
            "Lag": 60,
            "WideIndexLag": 36,
            "IndIndexLag": 180,
            "WideIndexName": "000300.SH",
            "IndIndexName": "SW2",
        }
    },

    {
        "FactorName": "factorTripleMaxDistanceToIndex",
        "ClassName": "FactorTripleMaxDistanceToIndex",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "DataTypeIndex": "Tick",
        "IndexGroup": ["000300.SH"],
        "INFGroup": {
            "SW2": ["LastPrice"]
        },
        "Parameters": {
            "Lag": 120,
            "WideIndexLag": 72,
            "IndIndexLag": 360,
            "WideIndexName": "000300.SH",
            "IndIndexName": "SW2",
        }
    },

    {
        "FactorName": "factorTripleMinDistanceToIndex",
        "ClassName": "FactorTripleMinDistanceToIndex",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "DataTypeIndex": "Tick",
        "IndexGroup": ["000300.SH"],
        "INFGroup": {
            "SW2": ["LastPrice"],
        },
        "Parameters": {
            "Lag": 200,
            "WideIndexLag": 120,
            "IndIndexLag": 600,
            "WideIndexName": "000300.SH",
            "IndIndexName": "SW2",
        }
    },

    {
        "FactorName": "factorTripleClosureSquare",
        "ClassName": "FactorTripleClosureSquare",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "DataTypeIndex": "Tick",
        "IndexGroup": ["000300.SH"],
        "INFGroup": {
            "SW2": ["LastPrice"],
        },
        "Parameters": {
            "Lag": 100,
            "WideIndexLag": 60,
            "IndIndexLag": 300,
            "ClosureLag": 60,
            "WideIndexName": "000300.SH",
            "IndIndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlBidVolumeRatio_SW2",
        "ClassName": "FactorPnlBidVolumeRatio",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["D", "P"],
        "Owner": "015619(LST)",
        "INFGroup": {
            "SW2": ["BidDelegateVolumeRatio"]
        },
        "Parameters": {
            "IndexName": "SW2"
        }
    },

    {
        "FactorName": "factorPnlAskVolumeRatio_SW2",
        "ClassName": "FactorPnlAskVolumeRatio",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["D", "P"],
        "Owner": "015619(LST)",
        "INFGroup": {
            "SW2": ["AskDelegateVolumeRatio"]
        },
        "Parameters": {
            "IndexName": "SW2"
        }
    },

    {
        "FactorName": "factorPnlVolumeReturnsAmp_SW2",
        "ClassName": "FactorPnlVolumeReturnsAmp",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "INFGroup": {
            "SW2": ["LastPrice"]
        },
        "Parameters": {
            "Lag": 20,
            "ReturnsLag": 2,
            "IndexReturnsLag": 2,
            "ShortVolumeLag": 40,
            "LongVolumeLag": 200,
            "IndexName": "SW2",
        }
    },

    # Submitted by 011668(JS)
    {
        "FactorName": "factorPnlRetSum200_SW2",
        "ClassName": "FactorPnlRetSum",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "INFGroup": {
            "SW2": ["LastPrice"]
        },
        "Parameters": {
            "Lag": 200,
            "IndexLag": 600,
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlSkew200_SW2",
        "ClassName": "FactorPnlSkew",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "INFGroup": {
            "SW2": ["MidPriceReturnsSkew_600"]
        },
        "DataTypeCS": "Tick",
        "Parameters": {
            "Lag": 200,
            "IndexLag": 600,
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlMA5Sum_SW2",
        "ClassName": "FactorPnlMA5Sum",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["D", "T"],
        "Owner": "011668(JS)",
        "INFGroup": {
            "SW2": ["LastPriceRatioWeighted_5"]
        },
        "Parameters": {
            "Lag1": 20,
            "Lag2": 200,
            "DayLag": 5,
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlTS20RankRet_SW2",
        "ClassName": "FactorPnlTSRankRet",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["D", "T"],
        "Owner": "011668(JS)",
        "INFGroup": {
            "SW2": ["LastPriceTsRankMean_20"]
        },
        "Parameters": {
            "Lag": 20,
            "DayLag": 20,
            "IndexName": "SW2"
        }
    },

    {
        "FactorName": "factorPnlRankMulVol300_SW2",
        "ClassName": "FactorPnlRankMulVol",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["P", "T"],
        "Owner": "011668(JS)",
        "INFGroup": {
            "SW2": ["MidPriceReturnsRank_900"]
        },
        "Parameters": {
            "Lag1": 300,
            "Lag2": 30,
            "IndexLag": 900,
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlDiff20Adj_SW2",
        "ClassName": "FactorPnlDiffAdj",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "NonFactors": ["VolRatio"],
        "Owner": "011668(JS)",
        "INFGroup": {
            "SW2": ["LastPrice"],
        },
        "Parameters": {
            "Lag": 20,
            "IndexLag": 60,
            "ShortVolumeLag": 20,
            "LongVolumeLag": 60,
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlERetWBV20_SW2",
        "ClassName": "FactorPnlERetWBV",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "INFGroup": {
            "SW2": ["LastPrice"]
        },
        "Parameters": {
            "Lag": 20,
            "IndexLag": 60,
            "TickLag": 20,
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlRetDMean20_60_SW2",
        "ClassName": "FactorPnlRetDMean",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "INFGroup": {
            "SW2": ["LastPrice"]
        },
        "Parameters": {
            "Lag1": 20,
            "Lag2": 60,
            "IndexLag": 60,
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlERetTrend200_100_SW2",
        "ClassName": "FactorPnlERetTrend",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "INFGroup": {
            "SW2": ["LastPrice"]
        },
        "Parameters": {
            "Lag1": 200,
            "Lag2": 100,
            "IndexLag": 600,
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlERetCorrByVol300_100_SW2",
        "ClassName": "FactorPnlERetCorrByVol",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "INFGroup": {
            "SW2": ["LastPrice", "Volume"]
        },
        "Parameters": {
            "Lag1": 300,
            "Lag2": 100,
            "IndexLag": 900,
            "IndexName": "SW2"
        }
    },

    {
        "FactorName": "factorPnlMaxERetWBV30_HS300",
        "ClassName": "FactorPnlMaxERetWBV",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "IndexGroup": ["000300.SH"],
        "DataTypeIndex": "Tick",
        "Parameters": {
            "Lag": 30,
            "IndexLag": 18,
            "TickLag": 20,
            "IndexName": "000300.SH"
        }
    },

    {
        "FactorName": "factorPnlRetDSR100_20_SW2",
        "ClassName": "FactorPnlRetDSR",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "INFGroup": {
            "SW2": ["LastPrice"],
        },
        "Parameters": {
            "Lag1": 100,
            "Lag2": 20,
            "IndexLag": 300,
            "IndexName": "SW2",
        }
    },

    {
        "FactorName": "factorPnlMaxERetRatio30_HS300",
        "ClassName": "FactorPnlMaxERetRatio",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "IndexGroup": ["000300.SH"],
        "DataTypeIndex": "Tick",
        "Parameters": {
            "Lag": 30,
            "IndexLag": 18,
            "TickLag": 20,
            "IndexName": "000300.SH",
        }
    },

    {
        "FactorName": "factorTriplePos30",
        "ClassName": "FactorTriplePos",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "IndexGroup": ["000300.SH"],
        "INFGroup": {
            "SW2": ["LastPrice"],
        },
        "DataTypeIndex": "Tick",
        "Parameters": {
            "Lag": 30,
            "IndIndexLag": 90,
            "WideIndexLag": 18,
            "TickLag": 20,
            "WideIndexName": "000300.SH",
            "IndIndexName": "SW2",
        }
    },

    {
        "FactorName": "factorTripleRel60",
        "ClassName": "FactorTripleRel",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "IndexGroup": ["000300.SH"],
        "INFGroup": {
            "SW2": ["LastPrice"],
        },
        "DataTypeIndex": "Tick",
        "Parameters": {
            "Lag": 60,
            "IndIndexLag": 180,
            "WideIndexLag": 36,
            "TickLag": 20,
            "WideIndexName": "000300.SH",
            "IndIndexName": "SW2",
        }
    },

]


FACTOR_CONFIG_ALGO = [
    {
        "FactorName": "factorBoll",
        "ClassName": "FactorBoll",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Albest",
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "BollLag": 20,
            "Width": 2
        }
    },

    {
        "FactorName": "factorBuyPower",
        "ClassName": "FactorBuyPower",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "Albest",
        "NonFactors": ["OrderEvaluate2"],
        "TickLength": 1,
        "Parameters": {
            "MAAmountLag": 4730
        }
    },

    {
        "FactorName": "factorBuyPowerSpeed",
        "ClassName": "FactorBuyPowerSpeed",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "Albest",
        "NonFactors": ["OrderEvaluate2", "EMA"],
        "TickLength": 1,
        "Parameters": {
            "OrderPressureLag": 5,
            "MAAmountLag": 20
        }
    },

    {
        "FactorName": "factorCrossPriceChangeRatio",
        "ClassName": "FactorCrossPriceChangeRatio",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Albest",
        "NonFactors": ["CrossPoint"],
        "Parameters": {
            "FastLag": 30,
            "SlowLag": 60
        }
    },

    {
        "FactorName": "factorCrossPriceChangeSpeed",
        "ClassName": "FactorCrossPriceChangeSpeed",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Albest",
        "NonFactors": ["CrossPoint"],
        "Parameters": {
            "FastLag": 30,
            "SlowLag": 60
        }
    },

    {
        "FactorName": "factorDistanceBetweenVWAPPrice20",
        "ClassName": "FactorDistanceBetweenVWAPPriceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Albest",
        "NonFactors": ["VWAPPrice"],
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 20
        }
    },

    {
        "FactorName": "factorDistanceBetweenVWAPPrice40",
        "ClassName": "FactorDistanceBetweenVWAPPriceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Albest",
        "NonFactors": ["VWAPPrice"],
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 40
        }
    },

    {
        "FactorName": "factorDistanceBetweenVWAPPrice100",
        "ClassName": "FactorDistanceBetweenVWAPPriceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Albest",
        "NonFactors": ["VWAPPrice"],
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 100
        }
    },

    {
        "FactorName": "factorDistanceBetweenVWAPPrice200",
        "ClassName": "FactorDistanceBetweenVWAPPriceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Albest",
        "NonFactors": ["VWAPPrice"],
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 200
        }
    },

    {
        "FactorName": "factorDistanceToAvePrice",
        "ClassName": "FactorDistanceToAvePriceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Albest",
        "NonFactors": ["AvePrice", "MidPrice"],
    },

    {
        "FactorName": "factorDistanceToHigh40",
        "ClassName": "FactorDistanceToHighModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Albest",
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 40
        }
    },

    {
        "FactorName": "factorDistanceToHigh100",
        "ClassName": "FactorDistanceToHighModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Albest",
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 100
        }
    },

    {
        "FactorName": "factorDistanceToLow40",
        "ClassName": "FactorDistanceToLowModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Albest",
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 40
        }
    },

    {
        "FactorName": "factorDistanceToLow100",
        "ClassName": "FactorDistanceToLowModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Albest",
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 100
        }
    },

    {
        "FactorName": "factorDistanceToVwap20",
        "ClassName": "FactorDistanceToVwapModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Albest",
        "NonFactors": ["VWAPPrice", "MidPrice"],
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorDistanceToVwap40",
        "ClassName": "FactorDistanceToVwapModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Albest",
        "NonFactors": ["VWAPPrice", "MidPrice"],
        "Parameters": {
            "Lag": 40
        }
    },

    {
        "FactorName": "factorDistanceToVwap100",
        "ClassName": "FactorDistanceToVwapModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Albest",
        "NonFactors": ["VWAPPrice", "MidPrice"],
        "Parameters": {
            "Lag": 100
        }
    },

    {
        "FactorName": "factorDistanceToVwapPriceWeighted",
        "ClassName": "FactorDistanceToVwapPriceWeighted",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Albest",
        "NonFactors": ["Volume", "MidPrice", "EMA"],
        "TickLength": 1,
        "Parameters": {
            "MATinyLag": 10,
            "MAShortLag": 20,
            "MALongLag": 100,
            "MASlowLag": 4730
        }
    },

    {
        "FactorName": "factorEmaOrderAmountPressure",
        "ClassName": "FactorEmaOrderAmountPressure",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Albest",
        "NonFactors": ["OrderAmountPressure", "EMA"],
        "Parameters": {
            "NumOrderMax": 1,
            "NumOrderMin": 1,
            "EMAOrderAmountPressureLag": 5,
            "WeightDecay": 0.8
        }
    },

    {
        "FactorName": "factorEmaOrderVolumePressure",
        "ClassName": "FactorEmaOrderVolumePressure",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Albest",
        "NonFactors": ["OrderVolumePressure", "EMA"],
        "Parameters": {
            "NumOrderMax": 10,
            "NumOrderMin": 1,
            "EMAOrderVolumePressureLag": 10,
            "WeightDecay": 0.8
        }
    },

    {
        "FactorName": "factorMAVolumeDistance3",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Albest",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 3,
            "MASlowLag": 4730
        }
    },

    {
        "FactorName": "factorMAVolumeDistance20",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Albest",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 20,
            "MASlowLag": 4730
        }
    },

    {
        "FactorName": "factorMAVolumeDistance40",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Albest",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 40,
            "MASlowLag": 4730
        }
    },

    {
        "FactorName": "factorMAVolumeDistance100",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Albest",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 100,
            "MASlowLag": 4730
        }
    },

    {
        "FactorName": "factorMAVolumeDistance200",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Albest",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 200,
            "MASlowLag": 4730
        }
    },

    {
        "FactorName": "factorMAVolumeDistance10_20",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Albest",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 10,
            "MASlowLag": 20
        }
    },

    {
        "FactorName": "factorMAVolumeDistance10_40",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Albest",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 10,
            "MASlowLag": 40
        }
    },

    {
        "FactorName": "factorMAVolumeDistance10_100",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Albest",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 10,
            "MASlowLag": 100
        }
    },

    {
        "FactorName": "factorMAVolumeDistance20_40",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Albest",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 20,
            "MASlowLag": 40
        }
    },

    {
        "FactorName": "factorMAVolumeDistance40_80",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Albest",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 40,
            "MASlowLag": 80
        }
    },

    {
        "FactorName": "factorMAVolumeDistance100_200",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Albest",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 100,
            "MASlowLag": 200
        }
    },

    {
        "FactorName": "factorMomentum",
        "ClassName": "FactorMomentumModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "Albest",
        "NonFactors": ["MidPrice", "EMA"],
        "TickLength": 1,
        "Parameters": {
            "Lag": 3,
            "EMAMidPriceLag": 5,
            "MAAmountLag": 4730
        }
    },

    {
        "FactorName": "factorOrderMomentum",
        "ClassName": "FactorOrderMomentum",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Albest",
        "NonFactors": ["MidPrice"],
    },

    {
        "FactorName": "factorOrderPressure",
        "ClassName": "FactorOrderPressureModified2",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Albest",
        "NonFactors": ["OrderEvaluate2", "EMA"],
        "Parameters": {
            "OrderPressureLag": 15
        }
    },

    {
        "FactorName": "factorSellPower",
        "ClassName": "FactorSellPower",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "Albest",
        "NonFactors": ["OrderEvaluate2"],
        "TickLength": 1,
        "Parameters": {
            "MAAmountLag": 4730
        }
    },

    {
        "FactorName": "factorSellPowerSpeed",
        "ClassName": "FactorSellPowerSpeed",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "Albest",
        "NonFactors": ["OrderEvaluate2", "EMA"],
        "TickLength": 1,
        "Parameters": {
            "OrderPressureLag": 5,
            "MAAmountLag": 20
        }
    },

    {
        "FactorName": "factorSpeed",
        "ClassName": "FactorSpeedModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Albest",
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 5,
            "EMAMidPriceLag": 10
        }
    },

    {
        "FactorName": "factorTransBuyVolumeDistance5_10",
        "ClassName": "FactorTransBuyVolumeDistance",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Albest",
        "NonFactors": ["TradeVolumeWeighted", "EMA"],
        "Parameters": {
            "MAFastLag": 5,
            "MASlowLag": 10,
            "MALag": 40,
            "DecayNum": 15
        }
    },

    {
        "FactorName": "factorTransBuyVolumeDistance5_40",
        "ClassName": "FactorTransBuyVolumeDistance",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Albest",
        "NonFactors": ["TradeVolumeWeighted", "EMA"],
        "Parameters": {
            "MAFastLag": 5,
            "MASlowLag": 40,
            "MALag": 40,
            "DecayNum": 15
        }
    },

    {
        "FactorName": "factorTransPressure",
        "ClassName": "FactorTransPressureModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Albest",
        "NonFactors": ["TradeNumWeighted"],
        "Parameters": {
            "MALag": 40,
            "DecayNum": 15
        }
    },

    {
        "FactorName": "factorTransPressureVol",
        "ClassName": "FactorTransPressureVolModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Albest",
        "NonFactors": ["TradeVolumeWeighted"],
        "Parameters": {
            "MALag": 40,
            "DecayNum": 15
        }
    },

    {
        "FactorName": "factorTransSellBuy5",
        "ClassName": "FactorTransSellBuy",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P", "TR"],
        "Owner": "Albest",
        "NonFactors": ["TransactionDistribution"],
        "Parameters": {
            "Lag": 5,
            "DecayNum": 40
        }
    },

    {
        "FactorName": "factorTransSellBuy10",
        "ClassName": "FactorTransSellBuy",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P", "TR"],
        "Owner": "Albest",
        "NonFactors": ["TransactionDistribution"],
        "Parameters": {
            "Lag": 10,
            "DecayNum": 40
        }
    },

    {
        "FactorName": "factorTransSellVolumeDistance5_10",
        "ClassName": "FactorTransSellVolumeDistance",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Albest",
        "NonFactors": ["TradeVolumeWeighted", "EMA"],
        "Parameters": {
            "MAFastLag": 5,
            "MASlowLag": 10,
            "MALag": 40,
            "DecayNum": 15
        }
    },

    {
        "FactorName": "factorTransSellVolumeDistance5_40",
        "ClassName": "FactorTransSellVolumeDistance",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Albest",
        "NonFactors": ["TradeVolumeWeighted", "EMA"],
        "Parameters": {
            "MAFastLag": 5,
            "MASlowLag": 40,
            "MALag": 40,
            "DecayNum": 15
        }
    },

    {
        "FactorName": "factorTransVolumeWeightedSwing5_10",
        "ClassName": "FactorTransVolumeWeightedSwing",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Albest",
        "NonFactors": ["TransVolumeWeighted", "TransVolumeWeightedDiff", "EMA"],
        "Parameters": {
            "DiffLag": 5,
            "VolumeLag": 10,
            "MALag": 40,
            "DecayNum": 15
        }
    },

    {
        "FactorName": "factorTransVolumeWeightedSwing5_40",
        "ClassName": "FactorTransVolumeWeightedSwing",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Albest",
        "NonFactors": ["TransVolumeWeighted", "TransVolumeWeightedDiff", "EMA"],
        "Parameters": {
            "DiffLag": 5,
            "VolumeLag": 40,
            "MALag": 40,
            "DecayNum": 15
        }
    },

    {
        "FactorName": "factorVolumeMagnification",
        "ClassName": "FactorVolumeMagnificationModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Albest",
        "NonFactors": ["Volume", "EMA"],
        "Parameters": {
            "FastLag": 10
        }
    },
]


FACTOR_CONFIG_EASY = [

    {
        "FactorName": "factortradeAskBidNumber",
        "ClassName": "FactortradeAskBidNumber",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Everest",
        "NonFactors": ["TradeNumWeightedEasy"],
        "Parameters": {
            "MALag": 40,
            "DecayNum": 15
        }
    },

    {
        "FactorName": "factortradeAskBidVolume",
        "ClassName": "FactortradeAskBidVolume",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Everest",
        "NonFactors": ["TradeVolumeWeightedEasy"],
        "Parameters": {
            "MALag": 40,
            "DecayNum": 15
        }
    },

    {
        "FactorName": "factorActiveBuyVolGrowth10",
        "ClassName": "FactorActiveBuyVolGrowth",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Everest",
        "NonFactors": ["TradeVolumeWeightedEasy", "EMA"],
        "Parameters": {
            "DecayNum": 15,
            "MALag": 40,
            "FastLag": 5,
            "SlowLag": 10
        }
    },

    {
        "FactorName": "factorActiveBuyVolGrowth40",
        "ClassName": "FactorActiveBuyVolGrowth",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Everest",
        "NonFactors": ["TradeVolumeWeightedEasy", "EMA"],
        "Parameters": {
            "DecayNum": 15,
            "MALag": 40,
            "FastLag": 5,
            "SlowLag": 40
        }
    },

    {
        "FactorName": "factorActiveSellVolGrowth10",
        "ClassName": "FactorActiveSellVolGrowth",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Everest",
        "NonFactors": ["TradeVolumeWeightedEasy", "EMA"],
        "Parameters": {
            "DecayNum": 15,
            "MALag": 40,
            "FastLag": 5,
            "SlowLag": 10
        }
    },

    {
        "FactorName": "factorActiveSellVolGrowth40",
        "ClassName": "FactorActiveSellVolGrowth",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Everest",
        "NonFactors": ["TradeVolumeWeightedEasy", "EMA"],
        "Parameters": {
            "DecayNum": 15,
            "MALag": 40,
            "FastLag": 5,
            "SlowLag": 40
        }
    },

    {
        "FactorName": "factorActiveVolRatio10",
        "ClassName": "FactorActiveVolRatio",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Everest",
        "NonFactors": ["TradeVolumeWeightedEasy", "EMA"],
        "Parameters": {
            "DecayNum": 15,
            "MALag": 40,
            "FastLag": 5,
            "SlowLag": 10
        }
    },

    {
        "FactorName": "factorActiveVolRatio40",
        "ClassName": "FactorActiveVolRatio",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "Everest",
        "NonFactors": ["TradeVolumeWeightedEasy", "EMA"],
        "Parameters": {
            "DecayNum": 15,
            "MALag": 40,
            "FastLag": 5,
            "SlowLag": 40
        }
    },

    {
        "FactorName": "factorPriceChangeRate",
        "ClassName": "FactorPriceChangeRate",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Everest",
        "NonFactors": ["PriceChange"],
        "Parameters": {
            "FastLag": 30,
            "SlowLag": 60
        }
    },

    {
        "FactorName": "factorPriceChangeSpeed",
        "ClassName": "FactorPriceChangeSpeed",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Everest",
        "NonFactors": ["PriceChange", "BoardPoint"],
        "Parameters": {
            "FastLag": 30,
            "SlowLag": 60
        }
    },

    {
        "FactorName": "factorAccBuyAmountRatio",
        "ClassName": "FactorAccBuyAmountRatio",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Everest",
        "NonFactors": ["OrderEvaluate2"],
        "TickLength": 1,
        "Parameters": {
            "MALag": 20,
            "OrderEvaluateLag": 5
        }
    },

    {
        "FactorName": "factorAccSellAmountRatio",
        "ClassName": "FactorAccSellAmountRatio",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Everest",
        "NonFactors": ["OrderEvaluate2"],
        "TickLength": 1,
        "Parameters": {
            "MALag": 20,
            "OrderEvaluateLag": 5
        }
    },

    {
        "FactorName": "factorTickBuyAmountRatio",
        "ClassName": "FactorTickBuyAmountRatio",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Everest",
        "NonFactors": ["OrderEvaluate2"],
        "TickLength": 1,
        "Parameters": {
            "LookBack": 4730
        }
    },

    {
        "FactorName": "factorTickSellAmountRatio",
        "ClassName": "FactorTickSellAmountRatio",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Everest",
        "NonFactors": ["OrderEvaluate2"],
        "TickLength": 1,
        "Parameters": {
            "LookBack": 4730
        }
    },

    {
        "FactorName": "factorAvePrice20Growth",
        "ClassName": "FactorAvePriceGrowth",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Everest",
        "NonFactors": ["VWAPPrice"],
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 20
        }
    },

    {
        "FactorName": "factorAvePrice40Growth",
        "ClassName": "FactorAvePriceGrowth",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Everest",
        "NonFactors": ["VWAPPrice"],
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 40
        }
    },

    {
        "FactorName": "factorAvePrice100Growth",
        "ClassName": "FactorAvePriceGrowth",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Everest",
        "NonFactors": ["VWAPPrice"],
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 100
        }
    },

    {
        "FactorName": "factorAvePrice200Growth",
        "ClassName": "FactorAvePriceGrowth",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "Everest",
        "NonFactors": ["VWAPPrice"],
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 200
        }
    },

    {
        "FactorName": "factorAveVolume3Growth",
        "ClassName": "FactorAveVolumeGrowth",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Everest",
        "TickLength": 1,
        "Parameters": {
            "MALag": 3
        }
    },

    {
        "FactorName": "factorAveVolume20Growth",
        "ClassName": "FactorAveVolumeGrowth",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Everest",
        "TickLength": 1,
        "Parameters": {
            "MALag": 20
        }
    },

    {
        "FactorName": "factorAveVolume40Growth",
        "ClassName": "FactorAveVolumeGrowth",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Everest",
        "TickLength": 1,
        "Parameters": {
            "MALag": 40
        }
    },

    {
        "FactorName": "factorAveVolume100Growth",
        "ClassName": "FactorAveVolumeGrowth",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Everest",
        "TickLength": 1,
        "Parameters": {
            "MALag": 100
        }
    },

    {
        "FactorName": "factorAveVolume200Growth",
        "ClassName": "FactorAveVolumeGrowth",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Everest",
        "TickLength": 1,
        "Parameters": {
            "MALag": 200
        }
    },

    {
        "FactorName": "factorVolumeMAGrowthFixed20",
        "ClassName": "FactorVolumeMAGrowthFixed",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Everest",
        "Parameters": {
            "MALag": 10,
            "LookBack": 20
        }
    },

    {
        "FactorName": "factorVolumeMAGrowthFixed40",
        "ClassName": "FactorVolumeMAGrowthFixed",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Everest",
        "Parameters": {
            "MALag": 10,
            "LookBack": 40
        }
    },

    {
        "FactorName": "factorVolumeMAGrowthFixed100",
        "ClassName": "FactorVolumeMAGrowthFixed",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Everest",
        "Parameters": {
            "MALag": 10,
            "LookBack": 100
        }
    },

    {
        "FactorName": "factorVolumeMAGrowthFlexible20",
        "ClassName": "FactorVolumeMAGrowthFlexible",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Everest",
        "TickLength": 1,
        "Parameters": {
            "MALag": 20
        }
    },

    {
        "FactorName": "factorVolumeMAGrowthFlexible40",
        "ClassName": "FactorVolumeMAGrowthFlexible",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Everest",
        "TickLength": 1,
        "Parameters": {
            "MALag": 40
        }
    },

    {
        "FactorName": "factorVolumeMAGrowthFlexible100",
        "ClassName": "FactorVolumeMAGrowthFlexible",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Everest",
        "TickLength": 1,
        "Parameters": {
            "MALag": 100
        }
    },

    {
        "FactorName": "factorEMAPressureRatio",
        "ClassName": "FactorEMAPressureRatio",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Everest",
        "NonFactors": ["OrderEvaluate2", "EMA"],
        "Parameters": {
            "OrderEvaluateEMALag": 15
        }
    },

    {
        "FactorName": "factorOrderBookVolumePressure",
        "ClassName": "FactorOrderBookVolumePressure",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Everest",
        "Parameters": {
            "EMALag": 10,
            "DecayRatio": 0.8
        }
    },

    {
        "FactorName": "factorOrderBookLv1Pressure",
        "ClassName": "FactorOrderBookLv1Pressure",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "Everest",
        "Parameters": {
            "EMALag": 5
        }
    },

    {
        "FactorName": "factorVolumeAmp",
        "ClassName": "FactorVolumeAmp",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "Everest",
        "Parameters": {
            "Lag": 10
        }
    },

    {
        "FactorName": "factorReversal",
        "ClassName": "FactorReversal",
        "FactorSource": "Easy",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "Everest",
        "NonFactors": ["MidPrice", "Volume", "EMA"],
        "TickLength": 1,
        "Parameters": {
            "ShortLag": 20,
            "LongLag": 100,
            "EMALag": 10,
            "LookBack": 4730
        }
    },

]


FACTOR_CONFIG_MDF = [
    {
        "FactorName": "factorAsk1ConsumptionRate_5",
        "ClassName": "FactorAsk1ConsumptionRate",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["BidPVolume"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 5,
        }
    },

    {
        "FactorName": "factorBidDealMaxRatio_20",
        "ClassName": "FactorBidDealMaxRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["BidDealVolume"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorMidpwLLTsGapMax_40",
        "ClassName": "FactorMidpwLLTsGapMax",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["LLTFilter", "MidPriceWeighted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 40,
            "LLTLag": 5,
        }
    },

    {
        "FactorName": "factorMdfMidpwToLLTs",
        "ClassName": "FactorMdfMidpwToLLTs",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["LLTFilter", "MidPriceWeighted"],
        "Owner": "015619(LST)",
        "Parameters": {
            "LLTLag": 1,
        }
    },

    {
        "FactorName": "factorSpeedToVwap_1",
        "ClassName": "FactorSpeedToVwap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPrice", "VWAPPrice"],
        "Owner": "015619(LST)",
        "Parameters": {
            "MinLag": 1,
            "MinVwapLag": 1
        }
    },

    {
        "FactorName": "factorAskIncremtActiveVolume_5",
        "ClassName": "FactorAskIncremtActiveVolume",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P", "TR"],
        "NonFactors": ["AskVolumeDeltaSelfSide", "AskVolumeDeltaOtherSide"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 5,
        }
    },

    {
        "FactorName": "factorBid1ConsumptionRate_5",
        "ClassName": "FactorBid1ConsumptionRate",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["AskPVolume"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 5,
        }
    },

    {
        "FactorName": "factorMdfBidDriveForceQuantile",
        "ClassName": "FactorMdfBidDriveForceQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 3,
            "Lag": 100,
            "SLag": 5
        }
    },

    {
        "FactorName": "factorMdfAskDriveForceQuantile",
        "ClassName": "FactorMdfAskDriveForceQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 3,
            "Lag": 100,
            "SLag": 5
        }
    },

    {
        "FactorName": "factorAskDriveForce_10",
        "ClassName": "FactorAskDriveForce",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 5,
            "Lag": 10
        }
    },

    {
        "FactorName": "factorBidDriveForce_10",
        "ClassName": "FactorBidDriveForce",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 5,
            "Lag": 10
        }
    },

    {
        "FactorName": "factorBidDriveForceSharpe_5",
        "ClassName": "FactorBidDriveForceSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 5,
            "Lag": 20
        }
    },

    {
        "FactorName": "factorAskDriveForceSharpe_5",
        "ClassName": "FactorAskDriveForceSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 5,
            "Lag": 20
        }
    },

    {
        "FactorName": "factorPVolumeStdRatio_60",
        "ClassName": "FactorPVolumeStdRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 60
        }
    },

    {
        "FactorName": "factorTradeAskSuccessRatio_10",
        "ClassName": "FactorTradeAskSuccessRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 10
        }
    },

    {
        "FactorName": "factorPVolumeRatioQuantile_60",
        "ClassName": "FactorPVolumeRatioQuantile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 60,
            "EMALag": 2
        }
    },

    {
        "FactorName": "factorRiseVolumeSharpe_20",  # 重复因子，历史遗留问题
        "ClassName": "FactorRiseVolumeSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorMdf40RealReverseAskAmt",
        "ClassName": "FactorMdf40RealReverseAskAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["AskAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015629(YJP)",
        "Parameters": {
            "Window": 60
        }
    },
    {
        "FactorName": "factorAskVolumeSharpe_60",
        "ClassName": "FactorAskVolumeSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 60
        }
    },

    {
        "FactorName": "factorTransBidChip_10",
        "ClassName": "FactorTransBidChip",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 10
        }
    },

    {
        "FactorName": "factorMdfOrderPressureConsistency",
        "ClassName": "FactorMdfOrderPressureConsistency",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderEvaluate2", "EMA"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 10,
            "SmoothLag": 5
        }
    },

    {
        "FactorName": "factorMdfAskVolumeRatioAngle",
        "ClassName": "FactorMdfAskVolumeRatioAngle",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 256,
            "SmoothLag": 16
        }
    },

    {
        "FactorName": "factorMdfBidVolumeRatioAngle",
        "ClassName": "FactorMdfBidVolumeRatioAngle",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 256,
            "SmoothLag": 16
        }
    },

    {
        "FactorName": "factorMdf40RealReverseBidAmt",
        "ClassName": "FactorMdf40RealReverseBidAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": [
            "BidAmtPerTrade"
        ],
        "Owner": "013544(HZQ)",
        "Successor": "015629(YJP)",
        "Parameters": {
            "Window": 60
        }
    },

    {
        "FactorName": "factorMdfFlex20BidAmtPerTradeZScore",
        "ClassName": "FactorMdfFlex20BidAmtPerTradeZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "013544(HZQ)",
        "Successor": "015629(YJP)",
        "TickLength": 1,
        "Parameters": {
            "Window": 10,
            "LongWindow": 100
        }
    },

    {
        "FactorName": "factorMdf20BidAmtPerTradeZScore",
        "ClassName": "FactorMdf20BidAmtPerTradeZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["MdfBidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "Parameters": {
            "Window": 20
        }
    },

    {
        "FactorName": "factorMdf100IlliqAskAmt",
        "ClassName": "FactorMdf100IlliqAskAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["MdfAskAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "Parameters": {
            "Window": 100
        }
    },
    {
        "FactorName": "factorMdf200AskAmtPerTrade",
        "ClassName": "FactorMdf200AskAmtPerTrade",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["MdfAskAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "Parameters": {
            "Window": 200
        }
    },
    {
        "FactorName": "factor200PVMove10",
        "ClassName": "Factor200PVMove",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "Parameters": {
            "WindowLong": 200,
            "WindowShort": 10
        },
    },

    {
        "FactorName": "factorMdfAskBidNumRatioStd",
        "ClassName": "FactorMdfAskBidNumRatioStd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "Parameters": {
            "Window": 20
        }
    },

    {
        "FactorName": "factorMdfFlex100RelBidAmtPerTrade1000",
        "ClassName": "FactorMdfFlex100RelBidAmtPerTrade",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["MdfBidAmtPerTrade"],
        "Owner": "013544(HZQ)",
        "Successor": "015390(HXJ)",
        "TickLength": 1,
        "Parameters": {
            "Window": 100,
            "LongWindow": 1000
        },
    },

    {
        "FactorName": "factorMdfABStrength10",
        "ClassName": "FactorMdfABStrength",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap", "BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag1": 300,
            "Lag2": 10
        }
    },

    {
        "FactorName": "factorMdfPricePer5",
        "ClassName": "FactorMdfPricePer",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["M", "T"],
        "Owner": "011668(JS)",
        "MinuteLength": 5,
        "DataType": "Both",
        "SplitAdjusted": True,
        "Parameters": {
            "DayLag": 5
        }
    },

    {
        "FactorName": "factorMdfBidMaxMin",
        "ClassName": "FactorMdfBidMaxMin",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwapAdj"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 200,
        }
    },

    {
        "FactorName": "factorMdfShortStrength30",
        "ClassName": "FactorMdfShortStrength",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30
        }
    },

    {
        "FactorName": "factor150TickAmtChangePct",
        "ClassName": "FactorTickAmtChangePct",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["TickBidAmt"],
        "Owner": "013544(HZQ)",
        "Successor": "011668(JS)",
        "Parameters": {
            "Window": 150
        },
    },

    {
        "FactorName": "factorHighRatio300",
        "ClassName": "FactorHighRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "T"],
        "Owner": "011668(JS)",
        "DailyLength": 20,
        "SplitAdjusted": True,
        "Parameters": {
            "Lag": 60,
            "DayLag": 20
        }
    },

    {
        "FactorName": "factorMdfBidDistanceMulRet30",
        "ClassName": "FactorMdfBidDistanceMulRet",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwapAdj"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60
        }
    },

    {
        "FactorName": "factorMdfBidDisToMean",
        "ClassName": "FactorMdfBidDisToMean",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwapAdj"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60,
        }
    },

]


IFACTOR_CONFIG_ZEUS = [
    # TIME SERIES
    # Submitted by 013544(HZQ)
    {
        "FactorName": "factor240PredRetBaseAmt",
        "ClassName": "Factor40PredRetBaseAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        'DailyLength': 1,
        'SplitAdjusted': True,
        "Parameters": {
            "WindowLong": 240,
            "WindowShort": 60
        },
    },

    {
        "FactorName": "factor1200PredRetBaseAmt",
        "ClassName": "Factor200PredRetBaseAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        'DailyLength': 1,
        'SplitAdjusted': True,
        "Parameters": {
            "WindowLong": 1200,
            "WindowShort": 60,
        },
    },

    {
        "FactorName": "factor240PVMove",
        "ClassName": "Factor40PVMove",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Parameters": {
            "WindowLong": 240,
            "WindowShort": 120,
        },
    },

    {
        "FactorName": "factor1200PVMove",
        "ClassName": "Factor200PVMove",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Parameters": {
            "WindowLong": 1200,
            "WindowShort": 600
        },
    },

    {
        "FactorName": "factor120Reverse",
        "ClassName": "Factor20Reverse",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        'SplitAdjusted': True,
        "Parameters": {
            "WindowLong": 120,
            "WindowShort": 60
        },
    },

    {
        "FactorName": "factor1200Reverse",
        "ClassName": "Factor200Reverse",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        'SplitAdjusted': True,
        "Parameters": {
            "WindowLong": 1200,
            "WindowShort": 600
        },
    },

    {
        "FactorName": "factorPriceVolumeRatio_2400",
        "ClassName": "FactorPriceVolumeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        'TickLength': 1,
        'SplitAdjusted': True,
        "Parameters": {
            "WindowShort": 1200,
            "WindowLong": 2400,
        }
    },

    {
        "FactorName": "factorPriceRatio_120",
        "ClassName": "FactorPriceRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "SplitAdjusted": True,
        "Parameters": {
            "Window": 120,
            "AvgWindow": 10,
        }
    },

    {
        "FactorName": "factorPredPrice_120",
        "ClassName": "FactorPredPrice",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "SplitAdjusted": True,
        "Parameters": {
            "Window": 120,
            "AvgWindow": 10
        }
    },

    {
        "FactorName": "factorLongRetWithHighVol_1200",
        "ClassName": "FactorLongRetWithHighVol",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Parameters": {
            "Window": 1200,
            "RelWindow": 120
        }
    },

    {
        "FactorName": "factorRetWithHighVol_240",
        "ClassName": "FactorRetWithHighVol",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Parameters": {
            "Window": 240,
            "RelWindow": 120
        }
    },

    {
        "FactorName": "factorPVCorr_1800",
        "ClassName": "FactorPVCorr",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Parameters": {
            "Window": 1800,
            "ShortWindow": 600
        }
    },

    {
        "FactorName": "factorScaleVolumePCorr_1800",
        "ClassName": "FactorScaleVolumePCorr",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Parameters": {
            "Window": 1800,
            "ShortWindow": 360
        }
    },

    # Submitted by 015619(LST)
    {
        "FactorName": "factorTrackVolatility_30",
        "ClassName": "FactorTrackVolatility",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Parameters": {
            "MinLag": 30
        }
    },

    {
        "FactorName": "factorWeightedReturns_60",
        "ClassName": "FactorWeightedReturns",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Parameters": {
            "Tags": [6, 12, 30, 60]
        }
    },

    {
        "FactorName": "factorVolumeOutbreakCurrent_30",
        "ClassName": "FactorVolumeOutbreakCurrent",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Parameters": {
            "VolumeMLag": 30,
            "CompLag": 60,
            "MidPriceThrd": 0.3
        }
    },


    {
        "FactorName": "factorDistanceToVwapVolume_60",
        "ClassName": "FactorDistanceToVwapVolume",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPrice", "VWAPPrice"],
        "Parameters": {
            "VolumeShortLag": 6,
            "VolumeLongLag": 60,
            "DistMinLag": 12
        }
    },

    {
        "FactorName": "factorSpeedToVwap_30",
        "ClassName": "FactorSpeedToVwap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPrice", "VWAPPrice"],
        "Parameters": {
            "MinLag": 30,
            "MinVwapLag": 30
        }
    },

    {
        "FactorName": "factorSR_1200",
        "ClassName": "FactorSR",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Parameters": {
            "Lag": 1200
        }
    },

    {
        "FactorName": "factorTickJump_900",
        "ClassName": "FactorTickJump",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "Parameters": {
            "Lag": 900
        }
    },

    {
        "FactorName": "factorAskPVolumeMaxChg_30",
        "ClassName": "FactorAskPVolumeMaxChg",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Parameters": {
            "MinLag": 30
        }
    },

    {
        "FactorName": "factorBidPVolumeMaxChg_30",
        "ClassName": "FactorBidPVolumeMaxChg",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Parameters": {
            "MinLag": 30
        }
    },

    {
        "FactorName": "factorVolumeToReturnsDoD_600",
        "ClassName": "FactorVolumeToReturnsDoD",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "Parameters": {
            "VolumeLag": 240,
            "ReturnsForw": 600
        }
    },

    {
        "FactorName": "factorVolumeReturnsMap_240",
        "ClassName": "FactorVolumeReturnsMap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "Parameters": {
            "Lag": 240,
            "ReturnsLag": 120
        }
    },

    {
        "FactorName": "factorBidWeightedVolumeRatio_120_30",
        "ClassName": "FactorBidWeightedVolumeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Parameters": {
            "ShortVolumeLag": 30,
            "LongVolumeLag": 120
        }
    },

    {
        "FactorName": "factorAskWeightedVolumeRatio_120_30",
        "ClassName": "FactorAskWeightedVolumeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Parameters": {
            "ShortVolumeLag": 30,
            "LongVolumeLag": 120
        }
    },

    {
        "FactorName": "factorAskPVolumeMaxChgUpd_120",
        "ClassName": "FactorAskPVolumeMaxChgUpd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Parameters": {
            "MinLag": 120,
        }
    },

    {
        "FactorName": "factorBidPVolumeMaxChgUpd_120",
        "ClassName": "FactorBidPVolumeMaxChgUpd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Parameters": {
            "MinLag": 120
        }
    },

    {
        "FactorName": "factorPositionChangeRatio_60",
        "ClassName": "FactorPositionChangeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Parameters": {
            "Lag": 60
        }
    },

    {
        "FactorName": "factorCandleReturnsMax_1200_120",
        "ClassName": "FactorCandleReturnsMax",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPriceWeighted"],
        "Parameters": {
            "Lag": 1200,
            "Window": 120
        }
    },

    {
        "FactorName": "factorCandleReturnsMin_1200_120",
        "ClassName": "FactorCandleReturnsMin",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPriceWeighted"],
        "Parameters": {
            "Lag": 1200,
            "Window": 120
        }
    },

    {
        "FactorName": "factorCandleUpDownwardVolatilityRatio_1200_120",
        "ClassName": "FactorCandleUpDownwardVolatilityRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPriceWeighted"],
        "Parameters": {
            "Lag": 1200,
            "Window": 120
        }
    },

    {
        "FactorName": "factorMountValleyReturns_120",
        "ClassName": "FactorMountValleyReturns",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPriceWeighted", "MountValleyMidpW"],
        "Parameters": {
            "Window": 120
        }
    },

    {
        "FactorName": "factorMountValleyReturnsLocal_120",
        "ClassName": "FactorMountValleyReturnsLocal",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPriceWeighted", "MountValleyMidpW"],
        "Parameters": {
            "Window": 120
        }
    },

    {
        "FactorName": "factorMountValleyContinuity_180",
        "ClassName": "FactorMountValleyContinuity",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPriceWeighted", "MountValleyMidpW"],
        "Parameters": {
            "Window": 180,
        }
    },

    {
        "FactorName": "factorReturnsMagnification_90_8",
        "ClassName": "FactorReturnsMagnification",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "NonFactors": ["KLineHighLive", "KLineLowLive", "MidPriceWeighted"],
        "Parameters": {
            "KLineLag": 90,
            "KLineNumber": 8,
        }
    },

    # Submitted by 016688(JS)
    {
        "FactorName": "factorAmtRatioPerPrice360",
        "ClassName": "FactorAmtRatioPerPrice",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag1": 60,
            "Lag2": 360
        }
    },

    {
        "FactorName": "factorEntrustRatio1200",
        "ClassName": "FactorEntrustRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag1": 1200,
            "Lag2": 120
        }
    },

    {
        "FactorName": "factorHighDistance3600",
        "ClassName": "FactorHighDistance",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 3600
        }
    },

    {
        "FactorName": "factorMidPriceSkew1800",
        "ClassName": "FactorMidPriceSkew",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 1800
        }
    },

    {
        "FactorName": "factorRet120Max720",
        "ClassName": "FactorRetMax",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag1": 720,
            "Lag2": 120
        }
    },

    {
        "FactorName": "factorRet360Max1800",
        "ClassName": "FactorRetMax",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag1": 1800,
            "Lag2": 360
        }
    },

    {
        "FactorName": "factorRet120MaxMinSum720",
        "ClassName": "FactorRetMaxMinSum",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag1": 720,
            "Lag2": 120
        }
    },

    {
        "FactorName": "factorRet360MaxMinSum1800",
        "ClassName": "FactorRetMaxMinSum",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag1": 1800,
            "Lag2": 360
        }
    },

    {
        "FactorName": "factorRiseCo360MulRoc240",
        "ClassName": "FactorRiseCoMulRoc",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 360,
            "LagRoc": 240
        }
    },

    {
        "FactorName": "factorRiseCoordination540",
        "ClassName": "FactorRiseCoordination",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 540
        }
    },

    {
        "FactorName": "factorRet120Mean1200",
        "ClassName": "FactorRetMean",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag1": 1200,
            "Lag2": 120
        }
    },

    {
        "FactorName": "factorRet180SR1800",
        "ClassName": "FactorRetSR",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag1": 1800,
            "Lag2": 180
        }
    },

    {
        "FactorName": "factorRet120Std1200",
        "ClassName": "FactorRetStd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag1": 1200,
            "Lag2": 120
        }
    },

    {
        "FactorName": "factorRet120Range1800",
        "ClassName": "FactorRet2Range",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag1": 1800,
            "Lag2": 120
        }
    },

    {
        "FactorName": "factorRetMulVol1200",
        "ClassName": "FactorRetMulVol",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag1": 1200,
            "Lag2": 120
        }
    },

    {
        "FactorName": "factorDistance2MAMulRet360",
        "ClassName": "FactorDistance2MAMulRet",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "T", "P"],
        "NonFactors": ["MidPrice"],
        "DailyLength": 20,
        "SplitAdjusted": True,
        "Parameters": {
            "Lag1": 1800,
            "Lag2": 360,
            "DayLag": 20
        }
    },

    {
        "FactorName": "factorPVPercentile1800_60",
        "ClassName": "FactorPVPercentile",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Parameters": {
            "Lag1": 1800,
            "Lag2": 60
        }
    },


    {
        "FactorName": "factorRetWeightedByVol60_360",
        "ClassName": "FactorRetWeightedByVol",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Parameters": {
            "Lag1": 60,
            "Lag2": 360
        }
    },

    {
        "FactorName": "factorPricePercentileAdjByVol360",
        "ClassName": "FactorPricePercentileAdjByVol",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "T"],
        "NonFactors": ["VolDailyRatio"],
        "DailyLength": 20,
        "SplitAdjusted": True,
        "Parameters": {
            "DayLag": 20,
            "TickLag": 360
        }
    },

    {
        "FactorName": "factorHighRatio_600",
        "ClassName": "FactorHighRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "T"],
        "DailyLength": 20,
        "SplitAdjusted": True,
        "Parameters": {
            "Lag": 600,
            "DayLag": 20
        }
    },

    {
        "FactorName": "factorLowRatio_600",
        "ClassName": "FactorLowRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "T"],
        "DailyLength": 20,
        "SplitAdjusted": True,
        "Parameters": {
            "Lag": 600,
            "DayLag": 20
        }
    },

    {
        "FactorName": "factorAvgClose2Vwap1200",
        "ClassName": "FactorAvgClose2Vwap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Parameters": {
            "Lag": 1200
        }
    },

    {
        "FactorName": "factorAmtPressure120",
        "ClassName": "FactorAmtPressure",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Parameters": {
            "Lag": 120
        }
    },

    {
        "FactorName": "factorAmtMag1200_360",
        "ClassName": "FactorAmtMag",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Parameters": {
            "Lag1": 1200,
            "Lag2": 360
        }
    },

    {
        "FactorName": "factorVolStrong360_120",
        "ClassName": "FactorVolStrong",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Parameters": {
            "Lag1": 360,
            "Lag2": 120
        }
    },

    {
        "FactorName": "factorABPriceRatioSR180",
        "ClassName": "FactorABPriceRatioSR",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap", "BidVwap"],
        "Parameters": {
            "Lag": 180
        }
    },

    {
        "FactorName": "factorABStrength180_60",
        "ClassName": "FactorABStrength",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Parameters": {
            "Lag1": 180,
            "Lag2": 60
        }
    },

    {
        "FactorName": "factorABChangeRatio180",
        "ClassName": "FactorABChangeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap", "BidVwap"],
        "Parameters": {
            "Lag": 180
        }
    },

    {
        "FactorName": "factorABPriceRatio600",
        "ClassName": "FactorABPriceRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap", "BidVwap"],
        "Parameters": {
            "Lag": 600
        }
    },

    {
        "FactorName": "factorAskDistance360",
        "ClassName": "FactorAskDistance",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Parameters": {
            "Lag": 360
        }
    },

    {
        "FactorName": "factorBidDistance360",
        "ClassName": "FactorBidDistance",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Parameters": {
            "Lag": 360
        }
    },

    {
        "FactorName": "factorAskTrend360",
        "ClassName": "FactorAskTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Parameters": {
            "Lag": 360
        }
    },

    {
        "FactorName": "factorBidTrend180",
        "ClassName": "FactorBidTrend",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Parameters": {
            "Lag": 180
        }
    },

    {
        "FactorName": "factorABTrendSum240",
        "ClassName": "FactorABTrendSum",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap", "BidVwap"],
        "Parameters": {
            "Lag": 240
        }
    },

    {
        "FactorName": "factorLongStrength180",
        "ClassName": "FactorLongStrength",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Parameters": {
            "Lag": 180
        }
    },

    {
        "FactorName": "factorShortStrength180",
        "ClassName": "FactorShortStrength",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Parameters": {
            "Lag": 180
        }
    },

    {
        "FactorName": "factorSellDisSR180",
        "ClassName": "FactorSellDisSR",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Parameters": {
            "Lag": 180
        }
    },

    {
        "FactorName": "factorSellDistanceStd120",
        "ClassName": "FactorSellDistanceStd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Parameters": {
            "Lag": 120
        }
    },

    {
        "FactorName": "factorBuyDistanceStd120",
        "ClassName": "FactorBuyDistanceStd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Parameters": {
            "Lag": 120
        }
    },

    {
        "FactorName": "factorAskDistanceMulRet360",
        "ClassName": "FactorAskDistanceMulRet",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Parameters": {
            "Lag": 360
        }
    },

    {
        "FactorName": "factorBidDistanceMulRet360",
        "ClassName": "FactorBidDistanceMulRet",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Parameters": {
            "Lag": 360
        }
    },

    {
        "FactorName": "factorMACross_180_60",
        "ClassName": "FactorMACross",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MAPrice", "MidPrice"],
        "Parameters": {
            "LagShort": 60,
            "LagLong": 180
        }
    },

    {
        "FactorName": "factorMACrossStd_180_60",
        "ClassName": "FactorMACrossStd",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MAPrice", "MidPrice"],
        "Parameters": {
            "LagShort": 60,
            "LagLong": 180,
            "Lag": 30
        }
    },

    {
        "FactorName": "factorVWAPCross_180_60",
        "ClassName": "FactorVWAPCross",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["VWAPPrice", "MidPrice"],
        "Parameters": {
            "LagShort": 60,
            "LagLong": 180,
            "Lag": 60
        }
    },

    {
        "FactorName": "factorAskVolPower_1800_360",
        "ClassName": "FactorAskVolPower",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["AskVwap"],
        "Parameters": {
            "Lag": 360,
            "LagShort": 360,
            "LagLong": 1800,
        }
    },

    {
        "FactorName": "factorBidVolPower_1800_180",
        "ClassName": "FactorBidVolPower",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["BidVwap"],
        "Parameters": {
            "Lag": 360,
            "LagShort": 180,
            "LagLong": 1800,
        }
    },

    {
        "FactorName": "factorDistance2BuyVwap_60",
        "ClassName": "FactorDistance2BuyVwap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Parameters": {
            "Lag": 60,
        }
    },

    {
        "FactorName": "factorDistance2SellVwap_120",
        "ClassName": "FactorDistance2SellVwap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Parameters": {
            "Lag": 120,
        }
    },

    # Submitted by 015629(YJP)
    {
        "FactorName": "factorPankouBidPressure_3",
        "ClassName": "FactorPankouBidPressure",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Parameters": {
            "SliceNum": 3
        }
    },

    {
        "FactorName": "factorPankouPressure_3",
        "ClassName": "FactorPankouPressure",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Parameters": {
            "SliceNum": 3
        }
    },

]


IFACTOR_CONFIG_ALGO = [
    {
        "FactorName": "factorBoll_120",
        "ClassName": "FactorBoll",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "BollLag": 120,
            "Width": 2
        }
    },

    {
        "FactorName": "factorBuyPowerSpeed_120",
        "ClassName": "FactorBuyPowerSpeed",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["OrderEvaluate2", "EMA"],
        "TickLength": 1,
        "Parameters": {
            "OrderPressureLag": 5,
            "MAAmountLag": 120
        }
    },

    {
        "FactorName": "factorCrossPriceChangeRatio_360_180",
        "ClassName": "FactorCrossPriceChangeRatio",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["CrossPoint"],
        "Parameters": {
            "FastLag": 180,
            "SlowLag": 360
        }
    },

    {
        "FactorName": "factorCrossPriceChangeSpeed_360_180",
        "ClassName": "FactorCrossPriceChangeSpeed",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["CrossPoint"],
        "Parameters": {
            "FastLag": 180,
            "SlowLag": 360
        }
    },

    {
        "FactorName": "factorDistanceBetweenVWAPPrice_40_20",
        "ClassName": "FactorDistanceBetweenVWAPPriceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["VWAPPrice"],
        "Parameters": {
            "FastLag": 20,
            "SlowLag": 40
        }
    },

    {
        "FactorName": "factorDistanceBetweenVWAPPrice_100_20",
        "ClassName": "FactorDistanceBetweenVWAPPriceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["VWAPPrice"],
        "Parameters": {
            "FastLag": 20,
            "SlowLag": 100
        }
    },

    {
        "FactorName": "factorDistanceBetweenVWAPPrice_200_20",
        "ClassName": "FactorDistanceBetweenVWAPPriceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["VWAPPrice"],
        "Parameters": {
            "FastLag": 20,
            "SlowLag": 200
        }
    },

    {
        "FactorName": "factorDistanceBetweenVWAPPrice_600_20",
        "ClassName": "FactorDistanceBetweenVWAPPriceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["VWAPPrice"],
        "Parameters": {
            "FastLag": 20,
            "SlowLag": 600
        }
    },

    {
        "FactorName": "factorDistanceBetweenVWAPPrice_1200_20",
        "ClassName": "FactorDistanceBetweenVWAPPriceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["VWAPPrice"],
        "Parameters": {
            "FastLag": 20,
            "SlowLag": 1200
        }
    },

    {
        "FactorName": "factorDistanceToHigh300",
        "ClassName": "FactorDistanceToHighModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 300
        }
    },

    {
        "FactorName": "factorDistanceToHigh600",
        "ClassName": "FactorDistanceToHighModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 600
        }
    },

    {
        "FactorName": "factorDistanceToLow300",
        "ClassName": "FactorDistanceToLowModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 300
        }
    },

    {
        "FactorName": "factorDistanceToLow600",
        "ClassName": "FactorDistanceToLowModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 600
        }
    },

    {
        "FactorName": "factorDistanceToVwap300",
        "ClassName": "FactorDistanceToVwapModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["VWAPPrice", "MidPrice"],
        "Parameters": {
            "Lag": 300
        }
    },

    {
        "FactorName": "factorDistanceToVwap600",
        "ClassName": "FactorDistanceToVwapModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["VWAPPrice", "MidPrice"],
        "Parameters": {
            "Lag": 600
        }
    },

    {
        "FactorName": "factorDistanceToVwapPriceWeighted600",
        "ClassName": "FactorDistanceToVwapPriceWeighted",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["Volume", "MidPrice", "EMA"],
        "TickLength": 1,
        "Parameters": {
            "MATinyLag": 60,
            "MAShortLag": 120,
            "MALongLag": 600,
            "MASlowLag": 4730 * 6
        }
    },

    {
        "FactorName": "factorEmaOrderAmountPressure_30",
        "ClassName": "FactorEmaOrderAmountPressure",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderAmountPressure", "EMA"],
        "Parameters": {
            "NumOrderMax": 1,
            "NumOrderMin": 1,
            "EMAOrderAmountPressureLag": 30,
            "WeightDecay": 0.8
        }
    },

    {
        "FactorName": "factorEmaOrderVolumePressure_60",
        "ClassName": "FactorEmaOrderVolumePressure",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderVolumePressure", "EMA"],
        "Parameters": {
            "NumOrderMax": 10,
            "NumOrderMin": 1,
            "EMAOrderVolumePressureLag": 60,
            "WeightDecay": 0.8
        }
    },

    {
        "FactorName": "factorMAVolumeDistanceA60",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 60,
            "MASlowLag": 4730 * 6
        }
    },

    {
        "FactorName": "factorMAVolumeDistanceA120",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 120,
            "MASlowLag": 4730 * 6
        }
    },

    {
        "FactorName": "factorMAVolumeDistanceA240",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 240,
            "MASlowLag": 4730 * 6
        }
    },

    {
        "FactorName": "factorMAVolumeDistanceA600",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 600,
            "MASlowLag": 4730 * 6
        }
    },

    {
        "FactorName": "factorMAVolumeDistanceA1200",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 1200,
            "MASlowLag": 4730 * 6
        }
    },

    {
        "FactorName": "factorMAVolumeDistance60_120",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 60,
            "MASlowLag": 120
        }
    },

    {
        "FactorName": "factorMAVolumeDistance120_240",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 120,
            "MASlowLag": 240
        }
    },

    {
        "FactorName": "factorMAVolumeDistance240_480",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 240,
            "MASlowLag": 480
        }
    },

    {
        "FactorName": "factorMAVolumeDistance600_1200",
        "ClassName": "FactorMAVolumeDistanceModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 600,
            "MASlowLag": 1200
        }
    },

    {
        "FactorName": "factorMomentum_18_30",
        "ClassName": "FactorMomentumModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["MidPrice", "EMA"],
        "TickLength": 1,
        "Parameters": {
            "Lag": 18,
            "EMAMidPriceLag": 30,
            "MAAmountLag": 4730 * 6
        }
    },


    {
        "FactorName": "factorOrderPressure_90",
        "ClassName": "FactorOrderPressureModified2",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderEvaluate2", "EMA"],
        "Parameters": {
            "OrderPressureLag": 90
        }
    },

    {
        "FactorName": "factorSellPowerSpeed_120",
        "ClassName": "FactorSellPowerSpeed",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "NonFactors": ["OrderEvaluate2", "EMA"],
        "TickLength": 1,
        "Parameters": {
            "OrderPressureLag": 30,
            "MAAmountLag": 120
        }
    },

    {
        "FactorName": "factorSpeed_30",
        "ClassName": "FactorSpeedModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 30,
            "EMAMidPriceLag": 10
        }
    },

    {
        "FactorName": "factorSpeed_60",
        "ClassName": "FactorSpeedModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Lag": 60,
            "EMAMidPriceLag": 10
        }
    },

    {
        "FactorName": "factorVolumeMagnification_60",
        "ClassName": "FactorVolumeMagnificationModified",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T"],
        "NonFactors": ["Volume", "EMA"],
        "Parameters": {
            "FastLag": 60
        }
    },
]

# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/27
FACTOR_CONFIG = [
    {
        "FactorName": "factorMSupportBreakBand",
        "ClassName": "FactorMSupportBreakBand",
        "FactorType": "TS",
        "DataSource": ["D", "T", "P"],
        "NonFactors": ["MidPrice"],
        "Owner": "015619(LST)",
        "DailyLength": 10,
        "Parameters": {
            "Lag": 10,
            "SupportScale": 0.6,
            "BreakScale": 0.8
        },
    },
    {
        "FactorName": "factorExtremeBand",
        "ClassName": "FactorExtremeBand",
        "FactorType": "TS",
        "DataSource": ["D", "T"],
        "Owner": "015619(LST)",
        "DailyLength": 10,
        "Parameters": {
            "Lag": 10,
            "Scale": 0.6,
        },
    },
    {
        "FactorName": "factorMDToMidPBand_5",
        "ClassName": "FactorMDToMidPBand",
        "FactorType": "TS",
        "DataSource": ["M", "T", "P"],
        "Owner": "015619(LST)",
        "MinuteLength": 5,
        "Parameters": {
            "MinuteLag": 5,
            "DayLag": 5,
            "Scale": 0.75,
        },
    },
    {
        "FactorName": "factorMDToMidPBand_10",
        "ClassName": "FactorMDToMidPBand",
        "FactorType": "TS",
        "DataSource": ["M", "T", "P"],
        "Owner": "015619(LST)",
        "MinuteLength": 5,
        "Parameters": {
            "MinuteLag": 10,
            "DayLag": 5,
            "Scale": 0.75,
        },
    },
    {
        "FactorName": "factorConsumptionRAsk_10",
        "ClassName": "FactorConsumptionRAsk",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["TR", "P"],
        "Parameters": {
            "Lag": 10,
        },
    },
    {
        "FactorName": "factorConsumptionRBid_5",
        "ClassName": "FactorConsumptionRBid",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["TR", "P"],
        "Parameters": {
            "Lag": 5,
        },
    },
    {
        "FactorName": "factorAskPToActiveVWBidPL_400",
        "ClassName": "FactorAskPToActiveVWBidPL",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["P", "TR"],
        "Parameters": {
            "Lag": 400
        },
    },
    {
        "FactorName": "factorBidPToActiveVWAskPL_400",
        "ClassName": "FactorBidPToActiveVWAskPL",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["P", "TR"],
        "Parameters": {
            "Lag": 400
        },
    },
    {
        "FactorName": "factorAskPToActiveVMBidPL_200",
        "ClassName": "FactorAskPToActiveVMBidPL",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["P", "TR"],
        "NonFactors": ["ActiveTradeBidPV"],
        "Parameters": {
            "Lag": 200
        },
    },
    {
        "FactorName": "factorBidPToActiveVMAskPL_200",
        "ClassName": "FactorBidPToActiveVMAskPL",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["P", "TR"],
        "NonFactors": ["ActiveTradeAskPV"],
        "Parameters": {
            "Lag": 200
        },
    },
    {
        "FactorName": "factorQuoteVMAskPChg_400",
        "ClassName": "FactorQuoteVMAskPChg",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["P"],
        "Parameters": {
            "Lag": 400
        },
    },
    {
        "FactorName": "factorQuoteVMBidPChg_400",
        "ClassName": "FactorQuoteVMBidPChg",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["P"],
        "Parameters": {
            "Lag": 400
        },
    },
    {
        "FactorName": "factorACTNetTopQ",
        "ClassName": "FactorACTNetTopQ",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["M", "TR"],
        "NonFactors": ["ActiveTradeBidIdxM", "ActiveTradeAskIdxM"],
        "MinuteLength": 1,
        "Parameters": {
            "Lag": 4730,
        },
    },
    {
        "FactorName": "factorACTNetTailQ",
        "ClassName": "FactorACTNetTailQ",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["M", "TR"],
        "NonFactors": ["ActiveTradeBidIdxM", "ActiveTradeAskIdxM"],
        "MinuteLength": 1,
        "Parameters": {
            "Lag": 4730,
        },
    },
    {
        "FactorName": "factorACTAskTailQ",
        "ClassName": "FactorACTAskTailQ",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["M", "TR"],
        "NonFactors": ["ActiveTradeAskIdxM"],
        "MinuteLength": 1,
        "Parameters": {
            "Lag": 4730,
        },
    },
    {
        "FactorName": "factorActiveTradeBidAmtQ_600",
        "ClassName": "FactorActiveTradeBidAmtQ",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["TR"],
        "Parameters": {
            "Lag": 600,
        },
    },
    {
        "FactorName": "factorActiveTradeAskAmtQ_600",
        "ClassName": "FactorActiveTradeAskAmtQ",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["TR"],
        "Parameters": {
            "Lag": 600,
        },
    },
    {
        "FactorName": "factorActiveTradeAmtABR_2",
        "ClassName": "FactorActiveTradeAmtABR",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["TR"],
        "Parameters": {
            "Lag": 2,
            "EMALag": 10,
        },
    },
    {
        "FactorName": "factorActiveTradeNumABR_1",
        "ClassName": "FactorActiveTradeNumABR",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["TR"],
        "Parameters": {
            "Lag": 1,
            "EMALag": 10,
        },
    },
    {
        "FactorName": "factorActiveTradeNumABR_5",
        "ClassName": "FactorActiveTradeNumABR",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["TR"],
        "Parameters": {
            "Lag": 5,
            "EMALag": 10,
        },
    },
    {
        "FactorName": "factorIncremtBidQuoteAmtQ",
        "ClassName": "FactorIncremtBidQuoteAmtQ",
        "FactorType": "TS",
        "DataSource": ["O", "P", "T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 4730,
        }
    },
    {
        "FactorName": "factorIncremtAskQuoteAmtQ",
        "ClassName": "FactorIncremtAskQuoteAmtQ",
        "FactorType": "TS",
        "DataSource": ["O", "P", "T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 4730,
        }
    },
    {
        "FactorName": "factorAggrOrderABR_1",
        "ClassName": "FactorOrderABR",
        "FactorType": "TS",
        "DataSource": ["O", "P", "T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 1,
            "EMALag": 10,
            "R": 0.0002,
        }
    },
    {
        "FactorName": "factorOrderABR_1",
        "ClassName": "FactorOrderABR",
        "FactorType": "TS",
        "DataSource": ["O", "P", "T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 1,
            "EMALag": 5,
            "R": 0.1,
        }
    },
    {
        "FactorName": "factorMildOrderBidAmtR",
        "ClassName": "FactorOrderBidAmtR",
        "FactorType": "TS",
        "DataSource": ["O", "P", "T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 4730,
            "R": 0.005,
        }
    },
    {
        "FactorName": "factorMildOrderBidAmtR_20",
        "ClassName": "FactorOrderBidAmtR",
        "FactorType": "TS",
        "DataSource": ["O", "P", "T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 20,
            "R": 0.005,
        }
    },
    {
        "FactorName": "factorMildOrderAskAmtR",
        "ClassName": "FactorOrderAskAmtR",
        "FactorType": "TS",
        "DataSource": ["O", "P", "T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 4730,
            "R": 0.005,
        }
    },
    {
        "FactorName": "factorMildOrderAskAmtR_20",
        "ClassName": "FactorOrderAskAmtR",
        "FactorType": "TS",
        "DataSource": ["O", "P", "T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 20,
            "R": 0.005,
        }
    },
    {
        "FactorName": "factorAskTrKM_20",
        "ClassName": "FactorAskTrKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 20}
    },
    {
        "FactorName": "factorAskTrKM_30",
        "ClassName": "FactorAskTrKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 30}
    },
    {
        "FactorName": "factorBidTrKM_20",
        "ClassName": "FactorBidTrKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 20}
    },
    {
        "FactorName": "factorBidTrKM_30",
        "ClassName": "FactorBidTrKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 30}
    },
    {
        "FactorName": "factorPanFlowKM_5",
        "ClassName": "FactorPanFlowKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 5}
    },
    {
        "FactorName": "factorVwapPriceGapRatioM",
        "ClassName": "FactorVwapPriceGapRatioM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "018187(YY)",
    },
    {
        "FactorName": "factorAskNumKM_10",
        "ClassName": "FactorAskNumKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 10}
    },
    {
        "FactorName": "factorAskNumKM_30",
        "ClassName": "FactorAskNumKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 30}
    },
    {
        "FactorName": "factorBidNumKM_10",
        "ClassName": "FactorBidNumKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 10}
    },
    {
        "FactorName": "factorBidNumKM_30",
        "ClassName": "FactorBidNumKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 30}
    },
    {
        "FactorName": "factorAskOrderKM_10",
        "ClassName": "FactorAskOrderKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 10}
    },
    {
        "FactorName": "factorAskOrderKM_20",
        "ClassName": "FactorAskOrderKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 20}
    },
    {
        "FactorName": "factorBidOrderKM_10",
        "ClassName": "FactorBidOrderKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 10}
    },
    {
        "FactorName": "factorBidOrderKM_20",
        "ClassName": "FactorBidOrderKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 20}
    },
    {
        "FactorName": "factorBidNumRatioM_10",
        "ClassName": "FactorBidNumRatioM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 10}
    },
    {
        "FactorName": "factorOrderFlowKM_15",
        "ClassName": "FactorOrderFlowKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 15}
    },
    {
        "FactorName": "factorOrderFlowKM_30",
        "ClassName": "FactorOrderFlowKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 30}
    },
    {
        "FactorName": "factor40PVMoveM",
        "ClassName": "Factor40PVMoveM",
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
        "FactorName": "factorMdfFlex20BidAmtPerTradeZScore",
        "ClassName": "FactorMdfFlex20BidAmtPerTradeZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "013544(HZQ)",
        "Successor": "018106(LYH)",
        "TickLength": 1,
        "Parameters": {
            "Window": 10,
            "LongWindow": 100
        }
    },
    {
        "FactorName": "factorAskDriveForceX",
        "ClassName": "FactorAskDriveForceX",
        "TickLength": 1,
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
        "FactorName": "factorAskDriveForceSharpeM_5",
        "ClassName": "FactorAskDriveForceSharpeM",
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
        "FactorName": "factorBidDriveForceX",
        "ClassName": "FactorBidDriveForceX",
        "TickLength": 1,
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
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
        "FactorName": "factorPriceToAskMaxM",
        "ClassName": "FactorPriceToAskMaxM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 200
        }
    },
    {
        "FactorName": "factorPriceToBidMaxM",
        "ClassName": "FactorPriceToBidMaxM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 300
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
        "FactorName": "factorOrdAskOrderVolumeTrendM",
        "ClassName": "FactorOrdAskOrderVolumeTrendM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorOrdAskNumTrendM",
        "ClassName": "FactorOrdAskNumTrendM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorOrderBookBidVolumeShiftX",
        "ClassName": "FactorOrderBookBidVolumeShiftX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Window": 20,
            "Decay": 0.8,
            "Lag": 20
        }
    },
    {
        "FactorName": "factorOrderBookAskVolumeShiftX",
        "ClassName": "FactorOrderBookAskVolumeShiftX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Window": 20,
            "Decay": 0.8,
            "Lag": 20
        }
    },
    {
        "FactorName": "factorVolumeTopTailVwapRatioX",
        "ClassName": "FactorVolumeTopTailVwapRatioX",
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
        "FactorName": "factorOrdAskBidNetAggressiveTrendX40",
        "ClassName": "FactorOrdAskBidNetAggressiveTrendX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "O", "T"],
        "NonFactors": ["OrdAskBidNetAggressive"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Window": 40
        }
    },
    {
        "FactorName": "factorOrdAskBidNetAggressiveQuantileX",
        "ClassName": "FactorOrdAskBidNetAggressiveQuantileX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "O", "T"],
        "NonFactors": ["OrdAskBidNetAggressive"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Window": 60,
            "Lag": 10
        }
    },
    {
        "FactorName": "factorOrdBidNumQuantileX",
        "ClassName": "FactorOrdBidNumQuantileX",
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
        "FactorName": "factorBidDriveForceQuantileX",
        "ClassName": "FactorBidDriveForceQuantileX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 3,
            "Window": 100,
            "Lag": 5
        }
    },
    {
        "FactorName": "factorAskDriveForceQuantileX",
        "ClassName": "FactorAskDriveForceQuantileX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["OrderDriveForce"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 3,
            "Window": 100,
            "Lag": 5
        }
    },
    {
        "FactorName": "factorBidDriveForceConsistencyX",
        "ClassName": "FactorBidDriveForceConsistencyX",
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
        "FactorName": "factorRiseVolumeTrendX",
        "ClassName": "FactorRiseVolumeTrendX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorRiseVolumeQuantileX",
        "ClassName": "FactorRiseVolumeQuantileX",
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
        "FactorName": "factorOrdAskNumQuantileX",
        "ClassName": "FactorOrdAskNumQuantileX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Window": 100,
            "Lag": 5
        }
    },
    {
        "FactorName": "factorRiseVolumeSharpeX",
        "ClassName": "FactorRiseVolumeSharpeX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Window": 20
        }
    },
    {
        "FactorName": "factorRet20SR200M",
        "ClassName": "FactorRetSRM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "TickLength": 1,
        "Parameters": {
            "Lag1": 300,
            "Lag2": 30
        }
    },
    {
        "FactorName": "factorRetMulVol200M",
        "ClassName": "FactorRetMulVolM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "TickLength": 1,
        "Parameters": {
            "Lag1": 200,
            "Lag2": 20
        }
    },
    {
        "FactorName": "factorDistance2MA20M",
        "ClassName": "FactorDistance2MAM",
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
        "FactorName": "factorRet20MaxMinSum120M",
        "ClassName": "FactorRetMaxMinSumM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "TickLength": 1,
        "Parameters": {
            "Lag1": 120,
            "Lag2": 20
        }
    },
    {
        "FactorName": "factorRet60MaxMinSum300M",
        "ClassName": "FactorRetMaxMinSumM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "TickLength": 1,
        "Parameters": {
            "Lag1": 300,
            "Lag2": 60
        }
    },
    {
        "FactorName": "factorRet20Mean200M",
        "ClassName": "FactorRetMeanM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "TickLength": 1,
        "Parameters": {
            "Lag1": 200,
            "Lag2": 20
        }
    },
    {
        "FactorName": "factorDistance2MAMulRet60M",
        "ClassName": "FactorDistance2MAMulRetM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "T", "P"],
        "NonFactors": ["MidPrice"],
        "TickLength": 1,
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
        "FactorName": "factorAvgClose2Vwap200Mdf",
        "ClassName": "FactorAvgClose2VwapMdf",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 200
        }
    },
    {
        "FactorName": "factorRetWeightedByVol10_60M",
        "ClassName": "FactorRetWeightedByVolM",
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
        "FactorName": "factorBidDistanceMulRet60Mdf",
        "ClassName": "FactorBidDistanceMulRetMdf",
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
        "FactorName": "factorAskDisAllM",
        "ClassName": "FactorAskDisAllM",
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
        "FactorName": "factorAskPerVal30Mdf",
        "ClassName": "FactorAskPerValMdf",
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
        "FactorName": "factorBidPerVal35Mdf",
        "ClassName": "FactorBidPerValMdf",
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
        "FactorName": "factorAskPerVal120Mdf",
        "ClassName": "FactorAskPerValMdf",
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
        "FactorName": "factorBidPerVal120Mdf",
        "ClassName": "FactorBidPerValMdf",
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
        "FactorName": "factorRet20Max120M",
        "ClassName": "FactorRetMaxM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "TickLength": 1,
        "Parameters": {
            "Lag1": 120,
            "Lag2": 20
        }
    },
    {
        "FactorName": "factorRet60Max300M",
        "ClassName": "FactorRetMaxM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "011668(JS)",
        "TickLength": 1,
        "Parameters": {
            "Lag1": 300,
            "Lag2": 60
        }
    },
    {
        "FactorName": "factorAskDisMaxMinSum",
        "ClassName": "FactorAskDisMaxMinSum",
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
        "FactorName": "factorBidDisMaxMinSum",
        "ClassName": "FactorBidDisMaxMinSum",
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
        "FactorName": "factorBidDisMaxM",
        "ClassName": "FactorBidDisMaxM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60,
            "Lag2": 300,
        }
    },
    {
        "FactorName": "factorAskDisMaxM",
        "ClassName": "FactorAskDisMaxM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwap"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60,
            "Lag2": 200,
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
        "FactorName": "factorAskDisToAdjVwapM",
        "ClassName": "FactorAskDisToAdjVwapM",
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
        "FactorName": "factorABChangeRatio60M",
        "ClassName": "FactorABChangeRatioM",
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
        "FactorName": "factorTORatioBuyR",
        "ClassName": "FactorTORatioBuyR",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["P", "O", "TR"],
        "Parameters": {
            "Lag1": 5,
            "Lag2": 20
        }
    },
    {
        "FactorName": "factorTORatioSellR",
        "ClassName": "FactorTORatioSellR",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["P", "O", "TR"],
        "Parameters": {
            "Lag1": 5,
            "Lag2": 20
        }
    },
    {
        "FactorName": "factorDistanceZScore",
        "ClassName": "FactorDistanceZScore",
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
        "FactorName": "factorDistance2MaxStdR",
        "ClassName": "FactorDistance2MaxStdR",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["TR", "P"],
        "NonFactors": ["MidPrice"],
        "Parameters": {
            "Window": 200
        }
    },
    {
        "FactorName": "factorNetOrderContR",
        "ClassName": "FactorNetOrderContR",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["O"],
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorDistance2ResBuy",
        "ClassName": "FactorDistance2ResBuy",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["T", "P"],
        "NonFactors": ["ResPrice"],
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorDistance2ResSell",
        "ClassName": "FactorDistance2ResSell",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["T", "P"],
        "NonFactors": ["ResPrice"],
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorBuyActiveVolumeRatioR",
        "ClassName": "FactorBuyActiveVolumeRatioR",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["P", "TR", "T"],
        "NonFactors": ["BuyActiveVolumeW"],
        "Parameters": {
            "Lag": 5
        }
    },
    {
        "FactorName": "factorSellActiveVolumeRatioR",
        "ClassName": "FactorSellActiveVolumeRatioR",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["P", "TR", "T"],
        "NonFactors": ["SellActiveVolume"],
        "Parameters": {
            "Lag": 5
        }
    },
    {
        "FactorName": "factorPassiveQtyRatioBuy",
        "ClassName": "FactorPassiveQtyRatioBuy",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["P", "TR"],
        "NonFactors": ["AggressiveOrderQty"],
    },
    {
        "FactorName": "factorPassiveQtyRatioSell",
        "ClassName": "FactorPassiveQtyRatioSell",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["P", "TR"],
        "NonFactors": ["AggressiveOrderQty"],
    },
    {
        "FactorName": "factorPassiveQtyRatioZScore",
        "ClassName": "FactorPassiveQtyRatioZScore",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["TR"],
    },
    {
        "FactorName": "factorAggressiveQtyRatioZScore",
        "ClassName": "FactorAggressiveQtyRatioZScore",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["TR"],
    },
    {
        "FactorName": "factorBuyActiveUpVolumeZScoreR",
        "ClassName": "FactorBuyActiveUpVolumeZScoreR",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["O", "P", "T"],
        "NonFactors": ["BuyActiveUpVolume"],
        "Parameters": {
            "Lag": 5,
        }
    },
    {
        "FactorName": "factorSellActiveDownVolumeZScoreR",
        "ClassName": "FactorSellActiveDownVolumeZScoreR",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["O", "P", "T"],
        "NonFactors": ["SellActiveDownVolume"],
        "Parameters": {
            "Lag": 5,
        }
    },
    {
        "FactorName": "factorOrderVolumeBigR",
        "ClassName": "FactorOrderVolumeBigR",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["P", "O", "T"],
        "Parameters": {
            "Lag": 5
        }
    },
    {
        "FactorName": "factorMountValleyReturnsM_20",
        "ClassName": "FactorMountValleyReturnsM",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactor": ["MidPriceWeighted", "MountValleyMidpWM"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Window": 20,
        }
    },
    {
        "FactorName": "factorMountValleyReturnsM_40",
        "ClassName": "FactorMountValleyReturnsM",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactor": ["MidPriceWeighted", "MountValleyMidpWM"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Window": 40,
        }
    },
    {
        "FactorName": "factorMountValleyReturnsS_20",
        "ClassName": "FactorMountValleyReturnsS",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactor": ["MidPriceWeighted", "MountValleyMidpWM"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Window": 20,
        }
    },
    {
        "FactorName": "factorMountValleyReturnsS_40",
        "ClassName": "FactorMountValleyReturnsS",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "NonFactor": ["MidPriceWeighted", "MountValleyMidpWM"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Window": 40,
        }
    },
    {
        "FactorName": "factorPriceRatioM",
        "ClassName": "FactorPriceRatioM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "018106(LYH)",
        "TickLength": 1,
        "SplitAdjusted": True,
        "Parameters": {
            "Window": 20,
            "AvgWindow": 5,
        }
    },
    {
        "FactorName": "factorPredPriceM",
        "ClassName": "FactorPredPriceM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "018106(LYH)",
        "TickLength": 1,
        "SplitAdjusted": True,
        "Parameters": {
            "Window": 20,
            "AvgWindow": 5
        }
    },
    {
        "FactorName": "factor200ReverseM",
        "ClassName": "Factor200ReverseM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "013544(HZQ)",
        "Successor": "018106(LYH)",
        'SplitAdjusted': True,
        "Parameters": {
            "WindowLong": 200,
            "WindowShort": 100,
        },
    },
    {
        "FactorName": "factorAskVolumeTrendX",
        "ClassName": "FactorAskVolumeTrendX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorAskNumSharpeX",
        "ClassName": "FactorAskNumSharpeX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorOrderAvgOfferBidPriceRetX",
        "ClassName": "FactorOrderAvgOfferBidPriceRetX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)"
    },
    {
        "FactorName": "factorOrderBidOfferQtyRatioTrendX",
        "ClassName": "FactorOrderBidOfferQtyRatioTrendX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorTransAskNumTrendX",
        "ClassName": "FactorTransAskNumTrendX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorTransBidNumTrendX",
        "ClassName": "FactorTransBidNumTrendX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorPankouPressureX",
        "ClassName": "FactorPankouPressureX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "SliceNum": 4
        }
    },
    {
        "FactorName": "factorBOPriceGap",
        "ClassName": "FactorBOPriceGap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)"
    },
    {
        "FactorName": "factorBOVwapGap",
        "ClassName": "FactorBOVwapGap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)"
    },
    {
        "FactorName": "factorBidOfferQtyRatioInc",
        "ClassName": "FactorBidOfferQtyRatioInc",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorBATNumRatioInc",
        "ClassName": "FactorBATNumRatioInc",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorPBVShiftInc",
        "ClassName": "FactorPBVShiftInc",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Window": 20,
            "Decay": 0.8,
            "Lag": 20
        }
    },
    {
        "FactorName": "factorPAVShiftInc",
        "ClassName": "FactorPAVShiftInc",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Window": 20,
            "Decay": 0.8,
            "Lag": 20
        }
    },
    {
        "FactorName": "factorEmaOrderAmountPressureM_1_5",
        "ClassName": "FactorEmaOrderAmountPressure",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "017023(HZW)",
        "NonFactors": ["OrderAmountPressure", "EMA"],
        "Parameters": {
            "NumOrderMax": 10,
            "NumOrderMin": 1,
            "EMAOrderAmountPressureLag": 1,
            "WeightDecay": 0.5
        }
    },
    {
        "FactorName": "factorEmaOrderAmountPressureM_1_10",
        "ClassName": "FactorEmaOrderAmountPressure",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "017023(HZW)",
        "NonFactors": ["OrderAmountPressure", "EMA"],
        "Parameters": {
            "NumOrderMax": 10,
            "NumOrderMin": 1,
            "EMAOrderAmountPressureLag": 1,
            "WeightDecay": 1
        }
    },
    {
        "FactorName": "factorEmaOrderVolumePressureM_1_10",
        "ClassName": "FactorEmaOrderVolumePressure",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "017023(HZW)",
        "NonFactors": ["OrderVolumePressure", "EMA"],
        "Parameters": {
            "NumOrderMax": 10,
            "NumOrderMin": 1,
            "EMAOrderVolumePressureLag": 1,
            "WeightDecay": 1
        }
    },
    {
        "FactorName": "factorBuyPowerSpeedM_5_200",
        "ClassName": "FactorBuyPowerSpeedM",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["OrderEvaluate2", "EMA"],
        "TickLength": 1,
        "Parameters": {
            "OrderPressureLag": 5,
            "MAAmountLag": 200
        }
    },
    {
        "FactorName": "factorBuyPowerM",
        "ClassName": "FactorBuyPowerM",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["OrderEvaluate2"],
        "TickLength": 1,
        "Parameters": {
            "MAAmountLag": 4730
        }
    },
    {
        "FactorName": "factorOrderPressureM",
        "ClassName": "FactorOrderPressureM",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "017023(HZW)",
        "NonFactors": ["OrderEvaluate2", "EMA"],
        "Parameters": {
            "OrderPressureLag": 15
        }
    },
    {
        "FactorName": "factorSellPowerM",
        "ClassName": "FactorSellPowerM",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["OrderEvaluate2"],
        "TickLength": 1,
        "Parameters": {
            "MAAmountLag": 4730
        }
    },
    {
        "FactorName": "factorOrderAmountAboveAve_200",
        "ClassName": "FactorOrderAmountAboveAve",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["OrderAmountPressure"],
        "Parameters": {
            "NumOrderMax": 10,
            "NumOrderMin": 1,
            "WeightDecay": 1,
            "Lag": 200,
        },
    },
    {
        "FactorName": "factorOrderAmountAboveAve_1000",
        "ClassName": "FactorOrderAmountAboveAve",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["OrderAmountPressure"],
        "Parameters": {
            "NumOrderMax": 10,
            "NumOrderMin": 1,
            "WeightDecay": 1,
            "Lag": 1000,
        },
    },
    {
        "FactorName": "factorOrderVolumeAboveAve_20",
        "ClassName": "FactorOrderVolumeAboveAve",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["OrderVolumePressure"],
        "Parameters": {
            "NumOrderMax": 10,
            "NumOrderMin": 1,
            "WeightDecay": 1,
            "Lag": 20,
        },
    },
    {
        "FactorName": "factorOrderVolumeAboveAve_500",
        "ClassName": "FactorOrderVolumeAboveAve",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["OrderVolumePressure"],
        "Parameters": {
            "NumOrderMax": 10,
            "NumOrderMin": 1,
            "WeightDecay": 0.5,
            "Lag": 500,
        },
    },
    {
        "FactorName": "factorNetNumKM_10",
        "ClassName": "FactorNetNumKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 10}
    },
    {
        "FactorName": "factorNetNumKM_40",
        "ClassName": "FactorNetNumKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 40}
    },
    {
        "FactorName": "factorQuoteBidWVR_400",
        "ClassName": "FactorQuoteBidWVR",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "R": 0.1,
            "Lag": 400,
        }
    },
    {
        "FactorName": "factorQuoteBidWVR_20",
        "ClassName": "FactorQuoteBidWVR",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "R": 0.1,
            "Lag": 20,
        }
    },
    {
        "FactorName": "factorQuoteAskWVR_400",
        "ClassName": "FactorQuoteAskWVR",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "R": 0.1,
            "Lag": 400,
        }
    },
    {
        "FactorName": "factorQuoteAskWVR_20",
        "ClassName": "FactorQuoteAskWVR",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "R": 0.1,
            "Lag": 20,
        }
    },
    {
        "FactorName": "factorQuoteVolumeWABRSpd",
        "ClassName": "FactorQuoteVolumeWABRSpd",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "R": 0.1,
            "EMALag": 5,
        }
    },
    {
        "FactorName": "factorQuoteVolumeMildWABRSpd",
        "ClassName": "FactorQuoteVolumeWABRSpd",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "R": 0.005,
            "EMALag": 5,
        }
    },
    {
        "FactorName": "factorQuoteNumWABRSpd",
        "ClassName": "FactorQuoteNumWABRSpd",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "R": 0.1,
            "EMALag": 5,
        }
    },
    {
        "FactorName": "factorQuoteNumMildWABRSpd",
        "ClassName": "FactorQuoteNumWABRSpd",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "R": 0.005,
            "EMALag": 5,
        }
    },
    {
        "FactorName": "factorQuoteAllQtyABRSpd",
        "ClassName": "FactorQuoteAllQtyABRSpd",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "EMALag": 5,
        }
    },
    {
        "FactorName": "factorMdfPricePer2_5",
        "ClassName": "FactorMdfPricePer2",
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
        "FactorName": "factorMdfPVPer5",
        "ClassName": "FactorMdfPVPer",
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
        "FactorName": "factorAvgClose2Vwap200Mdf",
        "ClassName": "FactorAvgClose2VwapMdf",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 200
        }
    },
    {
        "FactorName": "factorMdfAskMaxMin",
        "ClassName": "FactorMdfAskMaxMin",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwapAdj"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 100,
        }
    },
    {
        "FactorName": "factorRet20Max120Adj",
        "ClassName": "FactorRetMaxAdj",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPriceHistorical"],
        "Owner": "011668(JS)",
        "TickLength": 1,
        "Parameters": {
            "Lag1": 120,
            "Lag2": 20
        }
    },
    {
        "FactorName": "factorMdfShortStrength30M",
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
        "FactorName": "factorAskDisAll30",
        "ClassName": "FactorAskDisAllM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwapAdj"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30,
        }
    },
    {
        "FactorName": "factorAskDisAll100Diff2",
        "ClassName": "FactorAskDisAllDiff2",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwapAdj"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 100,
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
        "FactorName": "factorTradeAmtOncePriceAsk",
        "ClassName": "FactorTradeAmtOncePriceAsk",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR", "P", "T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 300,
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
            "Lag": 300,
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
        "FactorName": "factorMdf20BidAmtPerTradeZScore",
        "ClassName": "FactorMdf20BidAmtPerTradeZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["MdfBidAmtPerTrade"],
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
        "Parameters": {
            "Window": 20
        }
    },
    {
        "FactorName": "factorAskBidAmtPct",
        "ClassName": "FactorAskBidAmtPct",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
        "TickLength": 1,
        "Parameters": {
            "Window": 10,
        }
    },
    {
        "FactorName": "factorLongRetWithHighVolM",
        "ClassName": "FactorLongRetWithHighVolM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
        "Parameters": {
            "Window": 200,
            "RelWindow": 20
        }
    },
    {
        "FactorName": "factor20BidAmtPerTradeZScore",
        "ClassName": "Factor20BidAmtPerTradeZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "NonFactors": ["BidAmtPerTrade"],
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
        "Parameters": {
            "Window": 20
        }
    },
    {
        "FactorName": "factorPVCorrM",
        "ClassName": "FactorPVCorrM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
        "Parameters": {
            "Window": 300,
            "ShortWindow": 100
        }
    },
    {
        "FactorName": "factor20TickAmtChangePct",
        "ClassName": "FactorTickAmtChangePct",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["TickBidAmt"],
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
        "Parameters": {
            "Window": 20
        },
    },
    {
        "FactorName": "factor150TickAmtChangePct",
        "ClassName": "FactorTickAmtChangePct",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["TickBidAmt"],
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
        "Parameters": {
            "Window": 150
        },
    },
    {
        "FactorName": "factorPriceVolumeRatio",
        "ClassName": "FactorPriceVolumeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
        'TickLength': 1,
        'SplitAdjusted': True,
        "Parameters": {
            "WindowShort": 200,
            "WindowLong": 400,
        }
    },
    {
        "FactorName": "factorMaxQuoteVNAskPToMidP",
        "ClassName": "FactorMaxQuoteVNAskPToMidP",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015619(LST)",
    },
    {
        "FactorName": "factorMaxQuoteVNBidPToMidP",
        "ClassName": "FactorMaxQuoteVNBidPToMidP",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015619(LST)",
    },
    {
        "FactorName": "factorMaxQuoteVBidPToMidP",
        "ClassName": "FactorMaxQuoteVBidPToMidP",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015619(LST)",
    },
    {
        "FactorName": "factorMaxQuoteVAskPToMidP",
        "ClassName": "FactorMaxQuoteVAskPToMidP",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015619(LST)",
    },
    {
        "FactorName": "factorActiveTradeBidPAmtR",
        "ClassName": "FactorActiveTradeBidPAmtR",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 4730,
        }
    },
    {
        "FactorName": "factorTradeOnceRatioBidMdf",
        "ClassName": "FactorTradeOnceRatioBidMdf",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30,
        }
    },
    {
        "FactorName": "factorTradeOnceRatioAskMdf",
        "ClassName": "FactorTradeOnceRatioAskMdf",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30,
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
        "FactorName": "factorTradeAmtOnceRatioAskMdf10",
        "ClassName": "FactorTradeAmtOnceRatioAskMdf",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "TR", "T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 100,
        }
    },
    {
        "FactorName": "factorTradeAmtOnceRatioBidMdf10",
        "ClassName": "FactorTradeAmtOnceRatioBidMdf",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "TR", "T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 100,
        }
    },
    {
        "FactorName": "factorTradeOnceRatioMdf",
        "ClassName": "FactorTradeOnceRatioMdf",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20,
        }
    },
    {
        "FactorName": "factorTradeOnceRatioMdf2",
        "ClassName": "FactorTradeOnceRatioMdf2",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 30,
        }
    },
    {
        "FactorName": "factorTradeAmtOnceRatioAskMdf2",
        "ClassName": "FactorTradeAmtOnceRatioAskMdf2",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 40,
        }
    },
    {
        "FactorName": "factorTradeMultiRatioAskMdf",
        "ClassName": "FactorTradeMultiRatioAskMdf",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 60,
        }
    },
    {
        "FactorName": "factorTradeMultiRatioAskMdf2",
        "ClassName": "FactorTradeMultiRatioAskMdf2",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 150,
        }
    },
    {
        "FactorName": "factorTradeMultiRatioBidMdf2",
        "ClassName": "FactorTradeMultiRatioBidMdf2",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 150,
        }
    },
    {
        "FactorName": "factorTradeCompletionAskSRMdf",
        "ClassName": "FactorTradeCompletionAskSRMdf",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 20,
        }
    },
    {
        "FactorName": "factorMdf40RealReverseAskAmt",
        "ClassName": "FactorMdf40RealReverseAskAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["AskAmtPerTrade", "MidPrice"],
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
        "Parameters": {
            "Window": 60
        }
    },
    {
        "FactorName": "factorMdf40RealReverseBidAmt",
        "ClassName": "FactorMdf40RealReverseBidAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": [
            "BidAmtPerTrade", "MidPrice"
        ],
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
        "Parameters": {
            "Window": 60
        }
    },

    {
        "FactorName": "factor40RealReverseAskAmt",
        "ClassName": "Factor40RealReverseAskAmt",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["AskAmtPerTrade", "MidPrice"],
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
        'SplitAdjusted': True,
        "Parameters": {
            "Window": 40
        },
    },

    {
        "FactorName": "factorScaleVolumePCorrM",
        "ClassName": "FactorScaleVolumePCorrM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
        "Parameters": {
            "Window": 300,
            "ShortWindow": 60
        }
    },

    {
        "FactorName": "factorRetWithHighVolM",
        "ClassName": "FactorRetWithHighVolM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
        "Parameters": {
            "Window": 40,
            "RelWindow": 20
        }
    },

    {
        "FactorName": "factorFlex20BidAmtPerTradeZScore",
        "ClassName": "FactorFlex20BidAmtPerTradeZScore",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
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
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
        "TickLength": 1,
        "Parameters": {
            "Window": 200,
            "LongWindow": 4730
        },
    },

    {
        "FactorName": "factorMdf100IlliqAskAmtM",
        "ClassName": "FactorMdf100IlliqAskAmtM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "TR"],
        "NonFactors": ["MdfAskAmtPerTrade"],
        "Owner": "018106(LYH)",
        "Successor": "018106(LYH)",
        "Parameters": {
            "Window": 100
        }
    },
    {
        "FactorName": "factorAskNumKM_20",
        "ClassName": "FactorAskNumKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 20}
    },
    {
        "FactorName": "factorBidOrderKM_30",
        "ClassName": "FactorBidOrderKM",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 30}
    },
    {
        "FactorName": "factorAggressiveQtyRatioZScore2",
        "ClassName": "FactorAggressiveQtyRatioZScore2",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["TR"],
        "NonFactors": ["AggressiveOrderQty"],
    },
    {
        "FactorName": "factorAggressiveQtyRatioZScore3",
        "ClassName": "FactorAggressiveQtyRatioZScore3",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["TR"],
        "NonFactors": ["AggressiveOrderQty"],
    },
    {
        "FactorName": "factorAskTopGap",
        "ClassName": "FactorAskTopGap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 2,
            "Lag": 10
        }
    },
    {
        "FactorName": "factorBidTopGap",
        "ClassName": "FactorBidTopGap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Level": 2,
            "Lag": 10
        }
    },
    {
        "FactorName": "factorBuyVolAmp20_5",
        "ClassName": "FactorBuyVolAmp",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "sLag": 5,
            "Lag": 20
        }
    },
    {
        "FactorName": "factorBuyVolAmp100_10",
        "ClassName": "FactorBuyVolAmp",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "sLag": 10,
            "Lag": 100
        }
    },
    {
        "FactorName": "factorSellVolAmp60_5",
        "ClassName": "FactorSellVolAmp",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "sLag": 5,
            "Lag": 60
        }
    },
    {
        "FactorName": "factorTransBuyVolAmp100_5",
        "ClassName": "FactorTransBuyVolAmp",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "sLag": 5,
            "Lag": 100
        }
    },
    {
        "FactorName": "factorTransSellVolAmp60_5",
        "ClassName": "FactorTransSellVolAmp",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "sLag": 5,
            "Lag": 60
        }
    },
    {
        "FactorName": "factorOrderAskPressureX",
        "ClassName": "FactorOrderAskPressureX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "SliceNum": 4
        }
    },
    {
        "FactorName": "factorOrderBidOfferQtyRatioQuantileX",
        "ClassName": "FactorOrderBidOfferQtyRatioQuantileX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 60,
            "sLag": 5
        }
    },
    {
        "FactorName": "factorOrderAskBidTNumRatioX",
        "ClassName": "FactorOrderAskBidTNumRatioX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "sLag": 5,
            "Lag": 60
        }
    },
    {
        "FactorName": "factorOrderAvgOfferPriceBounceStdRatioX",
        "ClassName": "FactorOrderAvgOfferPriceBounceStdRatioX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 40
        }
    },
    {
        "FactorName": "factorOrderAvgBidPriceBounceZscoreX",
        "ClassName": "FactorOrderAvgBidPriceBounceZscoreX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 200,
            "sLag": 10
        }
    },
    {
        "FactorName": "factorOrderAvgOfferPriceBounceZscoreX",
        "ClassName": "FactorOrderAvgOfferPriceBounceZscoreX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 200,
            "sLag": 20
        }
    },
    {
        "FactorName": "factorCMCorrX",
        "ClassName": "FactorCMCorrX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 200,
            "sLag": 20
        }
    },
    {
        "FactorName": "factorMaPriceBollingUpX",
        "ClassName": "FactorMaPriceBollingUpX",
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
        "FactorName": "factorTranAskQtyCRTrendX",
        "ClassName": "FactorTranAskQtyCRTrendX",
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
        "FactorName": "factorOrdAskQtyCRTrendX",
        "ClassName": "FactorOrdAskQtyCRTrendX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 10,
            "Window": 20
        }
    },
    {
        "FactorName": "factorAskVolumeStableX",
        "ClassName": "FactorAskVolumeStableX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 100,
            "sLag": 10
        }
    },
    {
        "FactorName": "factorBidVolumeStableX",
        "ClassName": "FactorBidVolumeStableX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 200,
            "sLag": 20
        }
    },
    {
        "FactorName": "factorTransBidChipX",
        "ClassName": "FactorTransBidChipX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 10
        }
    },
    {
        "FactorName": "factorTransNetAmountTrendX",
        "ClassName": "FactorTransNetAmountTrendX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 60,
            "sLag": 5
        }
    },
    {
        "FactorName": "factorAggressiveTradeAmp",
        "ClassName": "FactorAggressiveTradeAmp",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "TR"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 200,
            "sLag": 10
        }
    },

    {
        "FactorName": "factorOrderOfferQtyAmp60_5",
        "ClassName": "FactorOrderOfferQtyAmp",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 60,
            "sLag": 5
        }
    },

    {
        "FactorName": "factorOrderBidQtyAmp60_5",
        "ClassName": "FactorOrderBidQtyAmp",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 60,
            "sLag": 5
        }
    },

    {
        "FactorName": "factorOrderOfferQtyAmp200_10",
        "ClassName": "FactorOrderOfferQtyAmp",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 200,
            "sLag": 10
        }
    },

    {
        "FactorName": "factorOrderBidQtyAmp200_10",
        "ClassName": "FactorOrderBidQtyAmp",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 200,
            "sLag": 10
        }
    },

    {
        "FactorName": "factorAskNumStableX",
        "ClassName": "FactorAskNumStableX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 200,
            "sLag": 10
        }
    },

    {
        "FactorName": "factorBidNumStableX",
        "ClassName": "FactorBidNumStableX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 200,
            "sLag": 10
        }
    },
    {
        "FactorName": "factorWeightedVolumeRatioX",
        "ClassName": "FactorWeightedVolumeRatioX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 60
        }
    },
    {
        "FactorName": "factorOrdAskBidNetAggressiveRatioX",
        "ClassName": "FactorOrdAskBidNetAggressiveRatioX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P", "O", "T"],
        "NonFactors": ["OrdAskBidNetAggressive"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 60,
            "sLag": 5
        }
    },
    {
        "FactorName": "factorOrdBidOrderSkewX",
        "ClassName": "FactorOrdBidOrderSkewX",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["O"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 10
        }
    },
    {
        "FactorName": "factorMOrderBidNumR",
        "ClassName": "FactorMOrderBidNumR",
        "MinuteLength": 1,
        "FactorType": "TS",
        "DataSource": ["O", "P", "T", "M"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 4730,
        }
    },
    {
        "FactorName": "factorMOrderAskNumR",
        "ClassName": "FactorMOrderAskNumR",
        "MinuteLength": 1,
        "FactorType": "TS",
        "DataSource": ["O", "P", "T", "M"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 4730,
        }
    },
    {
        "FactorName": "factorTOrderAskNumR",
        "ClassName": "FactorTOrderAskNumR",
        "MinuteLength": 1,
        "FactorType": "TS",
        "DataSource": ["O", "P", "T", "M"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 4730,
        }
    },
    {
        "FactorName": "factorTOrderBidNumR",
        "ClassName": "FactorTOrderBidNumR",
        "MinuteLength": 1,
        "FactorType": "TS",
        "DataSource": ["O", "P", "T", "M"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 4730,
        }
    },
    {
        "FactorName": "factorActiveTradeBidAmtDoD",
        "ClassName": "FactorActiveTradeBidAmtDoD",
        "MinuteLength": 10,
        "FactorType": "TS",
        "DataSource": ["TR", "T", "M"],
        "Owner": "015619(LST)",
    },
    {
        "FactorName": "factorOrderBidVDoD",
        "ClassName": "FactorOrderBidVDoD",
        "MinuteLength": 10,
        "FactorType": "TS",
        "DataSource": ["O", "T", "M"],
        "Owner": "015619(LST)",
    },
    {
        "FactorName": "factorOrderAskVDoD",
        "ClassName": "FactorOrderAskVDoD",
        "MinuteLength": 10,
        "FactorType": "TS",
        "DataSource": ["O", "T", "M"],
        "Owner": "015619(LST)",
    },
    {
        "FactorName": "factorOrderBidVToAllBV",
        "ClassName": "FactorOrderBidVToAllBV",
        "FactorType": "TS",
        "DataSource": ["O", "T"],
        "Owner": "015619(LST)",
    },
    {
        "FactorName": "factorPassiveOrderRatioBuyR",
        "ClassName": "FactorPassiveOrderRatioBuyR",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["P", "O", "T"],
    },
    {
        "FactorName": "factorPassiveOrderRatioSellR",
        "ClassName": "FactorPassiveOrderRatioSellR",
        "FactorType": "TS",
        "Owner": "015390(HXJ)",
        "DataSource": ["P", "O", "T"],
    },
    {
        "FactorName": "factorTransVolumeNumBuyPressureMZScore10_200",
        "ClassName": "FactorTransVolumeNumBuyPressureMZScore",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["TR", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["TradeVolumeWeightedM"],
        "Parameters": {
            "DecayNum": 10,
            "NumLag": 10,
            "Lag": 200,
            "MALag": 20,
        }
    },
    {
        "FactorName": "factorTransVolumeNumSellPressureMZScore10_200",
        "ClassName": "FactorTransVolumeNumSellPressureMZScore",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["TR", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["TradeVolumeWeightedM"],
        "Parameters": {
            "DecayNum": 10,
            "NumLag": 10,
            "Lag": 200,
            "MALag": 20,
        }
    },
    {
        "FactorName": "factorTransNumBuyPressureMZScore10_200",
        "ClassName": "FactorTransNumBuyPressureMZScore",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["TR", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["TradeNumWeightedM"],
        "Parameters": {
            "DecayNum": 10,
            "NumLag": 10,
            "Lag": 200,
            "MALag": 20,
        }
    },
    {
        "FactorName": "factorTransNumSellPressureMZScore10_200",
        "ClassName": "FactorTransNumSellPressureMZScore",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["TR", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["TradeNumWeightedM"],
        "Parameters": {
            "DecayNum": 10,
            "NumLag": 10,
            "Lag": 200,
            "MALag": 20,
        }
    },
    {
        "FactorName": "factorTransNumBuyPressureMZScore20_50",
        "ClassName": "FactorTransNumBuyPressureMZScore",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["TR", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["TradeNumWeightedM"],
        "Parameters": {
            "DecayNum": 5,
            "NumLag": 20,
            "Lag": 50,
            "MALag": 20,
        }
    },
    {
        "FactorName": "factorTransNumSellPressureMZScore20_50",
        "ClassName": "FactorTransNumSellPressureMZScore",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["TR", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["TradeNumWeightedM"],
        "Parameters": {
            "DecayNum": 5,
            "NumLag": 20,
            "Lag": 50,
            "MALag": 20,
        }
    },
    {
        "FactorName": "factorTransVolumeNumBuySellPressureMZScore10_200",
        "ClassName": "FactorTransVolumeNumBuySellPressureMZScore",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["TR", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["TradeVolumeWeightedM"],
        "Parameters": {
            "DecayNum": 10,
            "NumLag": 10,
            "Lag": 200,
            "MALag": 20,
        }
    },
    {
        "FactorName": "factorTransNumBuySellPressureMZScore10_200",
        "ClassName": "FactorTransNumBuySellPressureMZScore",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["TR", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["TradeNumWeightedM"],
        "Parameters": {
            "DecayNum": 10,
            "NumLag": 10,
            "Lag": 200,
            "MALag": 20,
        }
    },
    {
        "FactorName": "factorAskSideGap",
        "ClassName": "FactorAskSideGap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 10
        }
    },
    {
        "FactorName": "factorBidSideGap",
        "ClassName": "FactorBidSideGap",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 10
        }
    },
    {
        "FactorName": "factorPatternRecogProbA",
        "ClassName": "FactorPatternRecogProbA",
        "FactorType": "TS",
        "DataSource": ["M", "T"],
        "Owner": "015619(LST)",
        "NonFactors": ["PatternRecogProb"],
        "SplitAdjusted": True,
        "MinuteLength": 5,
        "TickLength": 1,
        "Parameters": {
            "DayLag": 5,
            "PredictFwd": 5
        }
    },
    {
        "FactorName": "factorPatternRecogProbD",
        "ClassName": "FactorPatternRecogProbD",
        "FactorType": "TS",
        "DataSource": ["M", "T"],
        "Owner": "015619(LST)",
        "NonFactors": ["PatternRecogProb"],
        "SplitAdjusted": True,
        "MinuteLength": 5,
        "TickLength": 1,
        "Parameters": {
            "DayLag": 5,
            "PredictFwd": 5
        }
    },
    {
        "FactorName": "factorCandleMLow",
        "ClassName": "FactorCandleMLow",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lags": [20, 100, 200, 400],
        }
    },
    {
        "FactorName": "factorCandleMHigh",
        "ClassName": "FactorCandleMHigh",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lags": [20, 100, 200, 400],
        }
    },
    {
        "FactorName": "factorCandleHL_40",
        "ClassName": "FactorCandleHL",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015619(LST)",
        "NonFactors": ["MidPriceWeighted"],
        "Parameters": {
            "Lag": 40,
        }
    },
    {
        "FactorName": "factorCandleRMax_200",
        "ClassName": "FactorCandleRMax",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 200,
            "RLag": 20,
        }
    },
    {
        "FactorName": "factorCandleRMax_100",
        "ClassName": "FactorCandleRMax",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 100,
            "RLag": 10,
        }
    },
    {
        "FactorName": "factorActiveTradeNABSTD_100",
        "ClassName": "FactorActiveTradeNABSTD",
        "FactorType": "TS",
        "DataSource": ["TR"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 100,
        }
    },
    {
        "FactorName": "factorOrderNABSTD_100",
        "ClassName": "FactorOrderNABSTD",
        "FactorType": "TS",
        "DataSource": ["O", "T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Lag": 100,
        }
    },
    {
        "FactorName": "factorQuoteINABSTD",
        "ClassName": "FactorQuoteINABSTD",
        "FactorType": "TS",
        "DataSource": ["P"],
        "Owner": "015619(LST)",
    },
    {
        "FactorName": "factorQuoteBidPWToMidPW",
        "ClassName": "FactorQuoteBidPWToMidPW",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Grade": 10,
        },
    },
    {
        "FactorName": "factorQuoteAskPWToMidPW",
        "ClassName": "FactorQuoteAskPWToMidPW",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Grade": 10,
        },
    },
    {
        "FactorName": "factorQuoteBidPWToMidPWH",
        "ClassName": "FactorQuoteBidPWToMidPW",
        "FactorType": "TS",
        "DataSource": ["P", "T"],
        "Owner": "015619(LST)",
        "Parameters": {
            "Grade": 3,
        },
    },
    {
        "FactorName": "factorQuoteAskPWToMidPWH",
        "ClassName": "FactorQuoteAskPWToMidPW",
        "FactorType": "TS",
        "Owner": "015619(LST)",
        "DataSource": ["P", "T"],
        "Parameters": {
            "Grade": 3,
        },
    },

]

# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
CBFACTOR_CONFIG = [
    # submitted by 015619(LST)
    {
        "FactorName": "factorCBConvPremiumRatio",
        "ClassName": "FactorCBConvPremiumRatio",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": {"D", "P", "T"},
        "NonFactors": {"MidPrice"},
        "Owner": "015619(LST)",
        "DailyLength": 1,
        "DataTypeUA": "Tick",
        "UnderlyingAsset": True,
    },

    {
        "FactorName": "factorCBRelativeReturns_5",
        "ClassName": "FactorCBRelativeReturns",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": {"P", "T"},
        "NonFactors": {"MidPrice", "MidPriceHistorical"},
        "Owner": "015619(LST)",
        "TickLength": 1,
        "TickLengthIndex": 1,
        "DataTypeIndex": "Tick",
        "IndexGroup": ["000832.SH"],
        "Parameters": {
            "ReturnsMinLag": 5,
            "RegressionLag": 600,
            "UpdateLag": 600
        }
    },

    {
        "FactorName": "factorCBSelfVolumeRatio",
        "ClassName": "FactorCBSelfVolumeRatio",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": {"T"},
        "Owner": "015619(LST)",
        "DailyLength": 5,
        "DailyLengthIndex": 5,
        "DataTypeIndex": "Tick",
        "IndexGroup": ["000832.SH"],
        "Parameters": {
            "DayLag": 5
        }
    },

    {
        "FactorName": "factorCBRelativeReturnsUA_12",
        "ClassName": "FactorCBRelativeReturnsUA",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": {"P", "T"},
        "NonFactors": {"MidPrice", "MidPriceHistorical"},
        "Owner": "015619(LST)",
        "UnderlyingAsset": True,
        "TickLength": 1,
        "TickLengthUA": 1,
        "DataTypeUA": "Tick",
        "Parameters": {
            "ReturnsMinLag": 12,
            "RegressionLag": 600,
            "UpdateLag": 600
        }
    },

    {
        "FactorName": "factorCBHighDistanceUA_100",
        "ClassName": "FactorCBHighDistanceUA",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": {"P"},
        "NonFactors": {"MidPrice", "MidPriceUA"},
        "Owner": "015619(LST)",
        "DataTypeUA": "Tick",
        "UnderlyingAsset": True,
        "Parameters": {
            "Lag": 100,
        }
    },

    {
        "FactorName": "factorCBLowDistanceUA_100",
        "ClassName": "FactorCBLowDistanceUA",
        "FactorSource": "Zeus",
        "FactorType": "IPANEL",
        "DataSource": {"P"},
        "NonFactors": {"MidPrice", "MidPriceUA"},
        "Owner": "015619(LST)",
        "DataTypeUA": "Tick",
        "UnderlyingAsset": True,
        "Parameters": {
            "Lag": 100,
        }
    },

    # submitted by 015629(YJP)
    {
        "FactorName": "factorCBTransPriceAngle",
        "ClassName": "FactorCBTransPriceAngle",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": {"TR"},
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 100
        }
    },

    {
        "FactorName": "factorCBTransPriceAngleMean",
        "ClassName": "FactorCBTransPriceAngleMean",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": {"TR"},
        "Owner": "015629(YJP)",
        "Parameters": {
            "Lag": 100
        }
    },

]
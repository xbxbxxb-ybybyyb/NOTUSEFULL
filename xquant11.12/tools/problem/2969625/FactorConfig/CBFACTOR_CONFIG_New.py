factor_config = [
    {
        "FactorName": "factorAvgQtyRatio",
        "ClassName": "FactorAvgQtyRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "018187(YY)",
    },
    {
        'ClassName': 'FactorAskDriveForceSharpe_MDF',
        'DataSource': ['P'],
        'FactorName': 'factorAskDriveForceSharpe_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'NonFactors': ['OrderDriveForce'],
        'Owner': '018187(YY)',
        'Parameters': {'Lag': 10, 'Level': 5}
    },
    {
        'FactorName': 'factorOrderPressure_MDF',
        'ClassName': 'FactorOrderPressure_MDF',
        'FactorSource': 'Algo',
        'FactorType': 'TS',
        'DataSource': ['P'],
        "Owner": "020334(QY)",
        'NonFactors': ['OrderEvaluate2', 'EMA'],
        'Parameters': {'OrderPressureLag': 40}
    },
    {
        "FactorName": "factorPriceWeightedVolumeRatio",
        "ClassName": "FactorPriceWeightedVolumeRatio",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "Owner": "020334(QY)",
    },
    {
        'FactorName': 'factorAggressiveOrderRatioSell_MDF',
        'ClassName': 'FactorAggressiveOrderRatioSell_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'Owner': '020334(QY)',
        'DataSource': ['TR', 'P'],
        'NonFactors': ['AggressiveOrderNum'],
        'Parameters': {'Window': 10}
    },
    {
        'FactorName': 'factorDistanceToLowOri400_MDF',
        'ClassName': 'FactorDistanceToLowModifiedOri_MDF',
        'FactorSource': 'Algo',
        'FactorType': 'TS',
        'DataSource': ['P'],
        'Owner': '020334(QY)',
        'NonFactors': ['MidPrice'],
        'Parameters': {'Lag': 400}
    },
    {
        'FactorName': 'factorLastPriceTrend',
        'ClassName': 'FactorLastPriceTrend',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'DataSource': ['T', 'D'],
        'DailyLength': 20,
        "Owner": "020334(QY)",
        'TickLength': 1,
        'Parameters': {'Window': 100, 'DayLag': 20}
    },

    {
        'FactorName': 'factorPriceVolumeRatio2',
        'ClassName': 'FactorPriceVolumeRatio2',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'DataSource': ['T', 'D'],
        'DailyLength': 20,
        "Owner": "020334(QY)",
        'TickLength': 1,
        'Parameters': {'Window': 300, 'DayLag': 20}
    },
    {
        "FactorName": "factorAskBelow",
        "ClassName": "FactorAskBelow",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 300,
        }
    },
    {
        "FactorName": "factorBidBelow",
        "ClassName": "FactorBidBelow",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 300,
        }
    },
    {
        "FactorName": "factorAskDisMax_MDF10_30",
        "ClassName": "FactorAskDisMax_MDF",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwapZT"],
        "Owner": "017023(HZW)",
        "Parameters": {
            "Lag": 10,
            "Lag2": 30,
        }
    },
    {
        "FactorName": "factorRet8MaxMinSum_MDF30",
        "ClassName": "FactorRetMaxMinSum_MDF",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "017023(HZW)",
        "Parameters": {
            "Lag1": 30,
            "Lag2": 8
        }
    },
    {
        "FactorName": "factorRet20MaxMinSum_MDF80",
        "ClassName": "FactorRetMaxMinSum_MDF",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["MidPrice"],
        "Owner": "017023(HZW)",
        "Parameters": {
            "Lag1": 80,
            "Lag2": 20
        }
    },
    {
        "FactorName": "factorOfferMaxAmtCurrentCumRatioDmean20",
        "ClassName": "FactorOfferMaxAmtCurrentCumRatioDmean",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "017023(HZW)",
        "Parameters": {
            "Lag": 20,
        }
    },

    {
        'ClassName': 'FactorOrdAskBidNumRatio_MDF',
        'DataSource': ['O'],
        'FactorName': 'factorOrdAskBidNumRatio_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'Owner': '018187(YY)',
        'Parameters': {'Lag': 1}
    },
    {
        "FactorName": "factorOCNC10",
        "ClassName": "FactorOCNC",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "O", "C"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 10}
    },
    {
        'ClassName': 'FactorAskBidMildOrderRatio_MDF',
        'DataSource': ['P', 'T', 'O', 'TR'],
        'FactorName': 'factorAskBidMildOrderRatio_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'NonFactors': ['Bid1PriceTransAdjusted_MDF', 'Ask1PriceTransAdjusted_MDF'],
        "Owner": "011668(JS)",
        'Parameters': {'Lag': 5}
    },
    {
        'ClassName': 'FactorAskOrderVolumeQuantile_MDF',
        'DataSource': ['O'],
        'FactorName': 'factorAskOrderVolumeQuantile_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        "Owner": "011668(JS)",
        "Parameters": {
            "Lag": 100,
        }
    },

    {
        'ClassName': 'FactorAskDriveForceQuantile_MDF2',
        'DataSource': ['P'],
        'FactorName': 'factorAskDriveForceQuantile_MDF1',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'NonFactors': ['OrderDriveForce'],
        'Owner': '018187(YY)',
        'Parameters': {'Lag': 100, 'Level': 5}
    },
    {
        'ClassName': 'FactorAskDriveForce_MDF',
        'DataSource': ['T', 'P'],
        'FactorName': 'factorAskDriveForce_MDF1',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'NonFactors': ['OrderDriveForce'],
        'Owner': '018187(YY)',
        'Parameters': {'Lag': 5, 'Level': 5}
    },
    {
        'ClassName': 'FactorBidDriveForceConsistency_MDF',
        'DataSource': ['P'],
        'FactorName': 'factorBidDriveForceConsistency_MDF5',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'NonFactors': ['OrderDriveForce'],
        'Owner': '018187(YY)',
        'Parameters': {'Lag': 5, 'Level': 5}
    },
    {
        "FactorName": "factorTRPC5",
        "ClassName": "FactorTRPC",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "P", "TR"],
        "Parameters": {"Lag": 5},
        "Owner": "018187(YY)",
    },
    {
        "ClassName": "FactorTradeVolBS",
        "DataSource": ["TR", "P"],
        "FactorName": "factorTradeVolBS5",
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        "Owner": "011668(JS)",
        'Parameters': {'Lag': 5}
    },

    {
        "ClassName": "FactorTradeVolBS",
        "DataSource": ["TR", "P"],
        "FactorName": "factorTradeVolBS20",
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        "Owner": "011668(JS)",
        'Parameters': {'Lag': 20}
    },

    {
        "ClassName": "FactorTradeVolB",
        "DataSource": ["TR", "P"],
        "FactorName": "factorTradeVolB60",
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        "Owner": "011668(JS)",
        'Parameters': {'Lag': 60}
    },

    {
        "ClassName": "FactorDis2Bid",
        "DataSource": ["P", "T"],
        "FactorName": "factorDis2Bid",
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        "Owner": "011668(JS)",
        "NonFactors": ["MidPriceWeighted"],
    },

    {
        "ClassName": "FactorDis2Offer",
        "DataSource": ["P", "T"],
        "FactorName": "factorDis2Offer",
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        "Owner": "011668(JS)",
        "NonFactors": ["MidPriceWeighted"],
    },
    {
        "ClassName": "FactorTradeVolS",
        "DataSource": ["TR", "P"],
        "FactorName": "factorTradeVolS60",
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        "Owner": "011668(JS)",
        'Parameters': {'Lag': 60}
    },
    {
        "FactorName": "factorAvgTotalPriceToP0",
        "ClassName": "FactorAvgTotalPriceToP0",
        "DataSource": ["P"],
        "Owner": "020334(QY)",
        "Parameters": {
            'Lag': 20
        }
    },
    {
        "FactorName": "factorAskDepth",
        "ClassName": "FactorAskDepth",
        "DataSource": ["P"],
        "Owner": "020334(QY)",
        "Parameters": {
        }
    },
    {
        "FactorName": "factorMidAvgToLastPrice",
        "ClassName": "FactorMidAvgToLastPrice",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        "Parameters": {
            "Lag": 15
        },
        "Owner": "020334(QY)",
    },
    {
        'FactorName': 'factorPriceVolumeRatioScale',
        'ClassName': 'FactorPriceVolumeRatioScale',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'DataSource': ['T', 'D'],
        'DailyLength': 20,
        "Owner": "020334(QY)",
        'TickLength': 1,
        'Parameters': {'Window': 200, 'DayLag': 20}
    },
    {
        "FactorName": "factorBidDepth",
        "ClassName": "FactorBidDepth",
        "DataSource": ["P"],
        "Owner": "020334(QY)",
        "Parameters": {
        }
    },
    {
        "FactorName": "factorBidAskDepthRatio",
        "ClassName": "FactorBidAskDepthRatio",
        "DataSource": ["P"],
        "Owner": "020334(QY)",
        "Parameters": {
        }
    },
    {
        'FactorName': 'factorAskDepthTrend',
        'ClassName': 'FactorAskDepthTrend',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'DataSource': ['T', 'D'],
        'Owner': '020334(QY)',
        'DailyLength': 20,
        'Parameters': {"DayLag": 20}
    },
    {
        "FactorName": "factorAvgOrderToTrade",
        "ClassName": "FactorAvgOrderToTrade",
        "DataSource": ["P"],
        "Owner": "020334(QY)",
        "Parameters": {
            'Lag': 20
        }
    },
    {
        "FactorName": "factorBuyPowerSpeedModified_5_200",
        "ClassName": "FactorBuyPowerSpeed",
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
        "FactorName": "factorBuyPowerModified",
        "ClassName": "FactorBuyPowerModified",
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
        "FactorName": "factorOrderPressure",
        "ClassName": "FactorOrderPressureModified2",
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
        "FactorName": "factorTransVolumeNumBuyPressureMZScore5_20",
        "ClassName": "FactorTransVolumeNumBuyPressureMZScore",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["TR", "T"],
        "Owner": "017023(HZW)",
        "NonFactors": ["TradeVolumeWeightedM"],
        "Parameters": {
            "DecayNum": 3,
            "NumLag": 5,
            "Lag": 20,
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
        "FactorName": "factorOCVC10",
        "ClassName": "FactorOCVC",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "O", "C"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 10}
    },
    {
        "FactorName": "factorOCVC20",
        "ClassName": "FactorOCVC",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T", "O", "C"],
        "Owner": "018187(YY)",
        "Parameters": {"Lag": 20}
    },

    {
        "FactorName": "factorLongStrength_MDF10",
        "ClassName": "FactorLongStrength_MDF",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["AskVwapZT"],
        "Owner": "017023(HZW)",
        "Parameters": {
            "Lag": 10
        }
    },
    {
        "FactorName": "factorOfferMaxAmtCurrentCumRatioDmean100",
        "ClassName": "FactorOfferMaxAmtCurrentCumRatioDmean",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "Owner": "017023(HZW)",
        "Parameters": {
            "Lag": 100,
        }
    },
    {
        "FactorName": "factorPricePercentileAdjByVol_MDF20_10",
        "ClassName": "FactorPricePercentileAdjByVol_MDF",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "T"],
        "NonFactors": ["VolDailyRatio"],
        "Owner": "017023(HZW)",
        "DailyLength": 20,
        "SplitAdjusted": True,
        "Parameters": {
            "DayLag": 20,
            "TickLag": 10
        }
    },
    {
        "FactorName": "factorPricePercentileAdjByVol_MDF20_60",
        "ClassName": "FactorPricePercentileAdjByVol_MDF",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["D", "T"],
        "NonFactors": ["VolDailyRatio"],
        "Owner": "017023(HZW)",
        "DailyLength": 20,
        "SplitAdjusted": True,
        "Parameters": {
            "DayLag": 20,
            "TickLag": 60
        }
    },
    {
        "FactorName": "factorShortStrength10",
        "ClassName": "FactorShortStrength_MDF",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["P"],
        "NonFactors": ["BidVwapZT"],
        "Owner": "017023(HZW)",
        "Parameters": {
            "Lag": 10
        }
    },
    {
        "FactorName": "factorUpDownPower50",
        "ClassName": "FactorUpDownPower",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "017023(HZW)",
        "NonFactors": [],
        "TickLength": 1,
        "Parameters": {
            "MALag": 50,
        }
    },
    {
        "FactorName": "factorUpDownPower200",
        "ClassName": "FactorUpDownPower",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "017023(HZW)",
        "NonFactors": [],
        "TickLength": 1,
        "Parameters": {
            "MALag": 200,
        }
    },
    {
        "FactorName": "factorUpDownPower2_200",
        "ClassName": "FactorUpDownPower2",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "017023(HZW)",
        "NonFactors": [],
        "TickLength": 1,
        "Parameters": {
            "MALag": 200,
        }
    },
    {
        "FactorName": "factorUpDownPower2_500",
        "ClassName": "FactorUpDownPower2",
        "FactorSource": "Algo",
        "FactorType": "TS",
        "DataSource": ["T", "P"],
        "Owner": "017023(HZW)",
        "NonFactors": [],
        "TickLength": 1,
        "Parameters": {
            "MALag": 500,
        }
    },

    {
        'ClassName': 'FactorFFTLoc_MDF',
        'DailyLength': 1,
        'DataSource': ['T', 'D'],
        'FactorName': 'factorFFTLoc_1024_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        "Owner": "011668(JS)",
        'Parameters': {
            'Lag': 1024
        },
        'SplitAdjusted': True,
        'TickLength': 1
    },

    {
        "FactorName": "factorMidAvgToP0",
        "ClassName": "FactorMidAvgToP0",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        'Owner': '020334(QY)',
    },
    {
        "FactorName": "factorPriceWeightedVolumeRatio_30",
        "ClassName": "FactorPriceWeightedVolumeRatio_30",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": ["T"],
        "TickLength": 1,
        'Owner': '020334(QY)',
        "Parameters": {
            "Bias": 0.3
        }
    },
    {
        'FactorName': 'factorDistanceToHigh40_MDF',
        'ClassName': 'FactorDistanceToHighModified_MDF',
        'FactorSource': 'Algo',
        'FactorType': 'TS',
        'DataSource': ['P'],
        'Owner': '020334(QY)',
        'NonFactors': ['MidPrice'],
        'Parameters': {
            'Lag': 40
        }
    },
    {
        'FactorName': 'factorDistanceToLow40_MDF',
        'ClassName': 'FactorDistanceToLowModified_MDF',
        'FactorSource': 'Algo',
        'FactorType': 'TS',
        'DataSource': ['P'],
        'Owner': '020334(QY)',
        'NonFactors': ['MidPrice'],
        'Parameters': {
            'Lag': 40
        }
    },
    {
        'FactorName': 'factorAveVolumeGrowth300_MDF',
        'ClassName': 'FactorAveVolumeGrowth_MDF',
        'FactorSource': 'Easy',
        'FactorType': 'TS',
        'DataSource': ['T'],
        'Owner': '020334(QY)',
        'TickLength': 1,
        'Parameters': {
            'MALag': 300
        }
    },
    {
        'FactorName': 'factorAskDriveForceQuantile_MDF',
        'ClassName': 'FactorAskDriveForceQuantile_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'DataSource': ['P'],
        'NonFactors': ['OrderDriveForce'],
        'Owner': '020334(QY)',
        'Parameters': {
            'Level': 5,
            'Lag': 300,
            'SLag': 10
        }
    },
    {
        'FactorName': 'factorIlliqAskAmt_MDF',
        'ClassName': 'FactorIlliqAskAmt_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'Owner': '020334(QY)',
        'DataSource': ['T', 'TR'],
        'NonFactors': ['MdfAskAmtPerTrade'],
        'Parameters': {
            'Window': 300
        }
    },
    {
        'FactorName': 'factorFlexRelBidAmtPerTrade_MDF',
        'ClassName': 'FactorFlexRelBidAmtPerTrade_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'Owner': '020334(QY)',
        'DataSource': ['T', 'D'],
        'DailyLength': 20,
        'TickLength': 1,
        'Parameters': {
            'Window': 100,
            'DayLag': 20
        }
    },
    {
        'FactorName': 'factorMomentum_MDF',
        'ClassName': 'FactorMomentum_MDF',
        'FactorSource': 'Algo',
        'FactorType': 'TS',
        'DataSource': ['P', 'T', 'D'],
        'DailyLength': 20,
        'Owner': '020334(QY)',
        'NonFactors': ['MidPrice', 'EMA'],
        'TickLength': 1,
        'Parameters': {
            'Lag': 5,
            'EMAMidPriceLag': 10,
            'MAAmountLag': 4730
        }
    },
    {
        'FactorName': 'factorBuyPowerSpeed_MDF',
        'ClassName': 'FactorBuyPowerSpeed_MDF',
        'FactorSource': 'Algo',
        'FactorType': 'TS',
        'DataSource': ['P', 'T'],
        'Owner': '020334(QY)',
        'NonFactors': ['OrderEvaluate2', 'EMA'],
        'TickLength': 1,
        'Parameters': {
            'OrderPressureLag': 10,
            'MAAmountLag': 60
        }
    },
    {
        'FactorName': 'factorDriveForce_MDF',
        'ClassName': 'FactorDriveForce_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'DataSource': ['P'],
        'NonFactors': ['OrderDriveForce'],
        'Owner': '020334(QY)',
        'Parameters': {
            'Level': 5,
            'Lag': 300,
            'SLag': 20
        }
    },

    {
        'ClassName': 'FactorVOI_MDF',
        'DataSource': ['P'],
        'FactorName': 'factorVOI_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'Owner': '018187(YY)',
        'Parameters': {
            'Lag': 10
        }
    },
    {
        'ClassName': 'FactorAskDriveForceSharpe_MDF',
        'DataSource': ['P'],
        'FactorName': 'factorAskDriveForceSharpe_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'NonFactors': ['OrderDriveForce'],
        'Owner': '018187(YY)',
        'Parameters': {
            'Lag': 10,
            'Level': 5
        }
    },
    {
        'ClassName': 'FactorDistance2MaxStd_MDF',
        'DataSource': ['TR', 'P'],
        'FactorName': 'factorDistance2MaxStd_MDF1000',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'NonFactors': ['MidPrice'],
        'Owner': '018187(YY)',
        'Parameters': {
            'Window': 1000
        }
    },
    {
        'ClassName': 'FactorPriceDiffSharpe_MDF',
        'DataSource': ['T', 'P'],
        'FactorName': 'factorPriceDiffSharpe_MDF200',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'NonFactors': ['AvePrice', 'MidPrice'],
        'Owner': '018187(YY)',
        'Parameters': {
            'Lag': 200
        }
    },
    {
        'ClassName': 'FactorVolumeRatioQuantile_MDF',
        'DataSource': ['TR'],
        'FactorName': 'factorVolumeRatioQuantile_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'Owner': '018187(YY)',
        'Parameters': {
            'Lag': 500
        }
    },
    {
        'ClassName': 'FactorOrderAvgBidPriceBounceMax_MDF',
        'DataSource': ['T'],
        'FactorName': 'factorOrderAvgBidPriceBounceMax_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'Owner': '018187(YY)',
        'Parameters': {
            'Lag': 200
        }
    },
    {
        'ClassName': 'FactorPriceDiffAngle_MDF',
        'DataSource': ['T', 'P'],
        'FactorName': 'factorPriceDiffAngle_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'NonFactors': ['MidPrice', 'AvePrice'],
        'Owner': '018187(YY)',
        'Parameters': {
            'Lag': 10
        }
    },
    {
        'ClassName': 'FactorVolumeTopTailVwapRatio_MDF',
        'DataSource': ['T'],
        'FactorName': 'factorVolumeTopTailVwapRatio_MDF',
        'FactorSource': 'Zeus',
        'FactorType': 'TS',
        'NonFactors': ['AvePrice'],
        'Owner': '018187(YY)',
        'Parameters': {
            'Window': 100
        },
        'TickLength': 1},
]
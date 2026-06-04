FACTOR_CONFIG = [

    {
        "FactorName": "factorBoll",
        "ClassName": "FactorBoll",
        "Parameters": {
            "BollLag": 20,
            "Width": 2
        }
    },
    {
        "FactorName": "factorBuyPower",
        "ClassName": "FactorBuyPower",
        "TickLength": 1,
        "Parameters": {
            "MAAmountLag": 4730
        }
    },
    {
        "FactorName": "factorBuyPowerSpeed",
        "ClassName": "FactorBuyPowerSpeed",
        "TickLength": 1,
        "Parameters": {
            "OrderPressureLag": 5,
            "MAAmountLag": 20
        }
    },
    {
        "FactorName": "factorCrossPriceChangeRatio",
        "ClassName": "FactorCrossPriceChangeRatio",
        "Parameters": {
            "FastLag": 30,
            "SlowLag": 60
        }
    },
    {
        "FactorName": "factorCrossPriceChangeSpeed",
        "ClassName": "FactorCrossPriceChangeSpeed",
        "Parameters": {
            "FastLag": 30,
            "SlowLag": 60
        }
    },
    {
        "FactorName": "factorDistanceBetweenVWAPPrice20",
        "ClassName": "FactorDistanceBetweenVWAPPriceModified",
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 20
        }
    },
    {
        "FactorName": "factorDistanceBetweenVWAPPrice40",
        "ClassName": "FactorDistanceBetweenVWAPPriceModified",
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 40
        }
    },
    {
        "FactorName": "factorDistanceBetweenVWAPPrice100",
        "ClassName": "FactorDistanceBetweenVWAPPriceModified",
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 100
        }
    },
    {
        "FactorName": "factorDistanceBetweenVWAPPrice200",
        "ClassName": "FactorDistanceBetweenVWAPPriceModified",
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 200
        }
    },
    {
        "FactorName": "factorDistanceToAvePrice",
        "ClassName": "FactorDistanceToAvePriceModified",
    },
    {
        "FactorName": "factorDistanceToHigh40",
        "ClassName": "FactorDistanceToHighModified",
        "Parameters": {
            "Lag": 40
        }
    },
    {
        "FactorName": "factorDistanceToHigh100",
        "ClassName": "FactorDistanceToHighModified",
        "Parameters": {
            "Lag": 100
        }
    },
    {
        "FactorName": "factorDistanceToLow40",
        "ClassName": "FactorDistanceToLowModified",
        "Parameters": {
            "Lag": 40
        }
    },
    {
        "FactorName": "factorDistanceToLow100",
        "ClassName": "FactorDistanceToLowModified",
        "Parameters": {
            "Lag": 100
        }
    },
    {
        "FactorName": "factorDistanceToVwap20",
        "ClassName": "FactorDistanceToVwapModified",
        "Parameters": {
            "Lag": 20
        }
    },
    {
        "FactorName": "factorDistanceToVwap40",
        "ClassName": "FactorDistanceToVwapModified",
        "Parameters": {
            "Lag": 40
        }
    },
    {
        "FactorName": "factorDistanceToVwap100",
        "ClassName": "FactorDistanceToVwapModified",
        "Parameters": {
            "Lag": 100
        }
    },
    {
        "FactorName": "factorDistanceToVwapPriceWeighted",
        "ClassName": "FactorDistanceToVwapPriceWeighted",
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
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 3,
            "MASlowLag": 4730
        }
    },
    {
        "FactorName": "factorMAVolumeDistance20",
        "ClassName": "FactorMAVolumeDistanceModified",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 20,
            "MASlowLag": 4730
        }
    },
    {
        "FactorName": "factorMAVolumeDistance40",
        "ClassName": "FactorMAVolumeDistanceModified",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 40,
            "MASlowLag": 4730
        }
    },
    {
        "FactorName": "factorMAVolumeDistance100",
        "ClassName": "FactorMAVolumeDistanceModified",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 100,
            "MASlowLag": 4730
        }
    },
    {
        "FactorName": "factorMAVolumeDistance200",
        "ClassName": "FactorMAVolumeDistanceModified",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 200,
            "MASlowLag": 4730
        }
    },
    {
        "FactorName": "factorMAVolumeDistance10_20",
        "ClassName": "FactorMAVolumeDistanceModified",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 10,
            "MASlowLag": 20
        }
    },
    {
        "FactorName": "factorMAVolumeDistance10_40",
        "ClassName": "FactorMAVolumeDistanceModified",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 10,
            "MASlowLag": 40
        }
    },
    {
        "FactorName": "factorMAVolumeDistance10_100",
        "ClassName": "FactorMAVolumeDistanceModified",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 10,
            "MASlowLag": 100
        }
    },
    {
        "FactorName": "factorMAVolumeDistance20_40",
        "ClassName": "FactorMAVolumeDistanceModified",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 20,
            "MASlowLag": 40
        }
    },
    {
        "FactorName": "factorMAVolumeDistance40_80",
        "ClassName": "FactorMAVolumeDistanceModified",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 40,
            "MASlowLag": 80
        }
    },
    {
        "FactorName": "factorMAVolumeDistance100_200",
        "ClassName": "FactorMAVolumeDistanceModified",
        "TickLength": 1,
        "Parameters": {
            "MAFastLag": 100,
            "MASlowLag": 200
        }
    },
    {
        "FactorName": "factorMomentum",
        "ClassName": "FactorMomentumModified",
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
    },
    {
        "FactorName": "factorOrderPressure",
        "ClassName": "FactorOrderPressureModified2",
        "Parameters": {
            "OrderPressureLag": 15
        }
    },
    {
        "FactorName": "factorSellPower",
        "ClassName": "FactorSellPower",
        "TickLength": 1,
        "Parameters": {
            "MAAmountLag": 4730
        }
    },
    {
        "FactorName": "factorSellPowerSpeed",
        "ClassName": "FactorSellPowerSpeed",
        "TickLength": 1,
        "Parameters": {
            "OrderPressureLag": 5,
            "MAAmountLag": 20
        }
    },
    {
        "FactorName": "factorSpeed",
        "ClassName": "FactorSpeedModified",
        "Parameters": {
            "Lag": 5,
            "EMAMidPriceLag": 10
        }
    },
    {
        "FactorName": "factorTransBuyVolumeDistance5_10",
        "ClassName": "FactorTransBuyVolumeDistance",
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
        "Parameters": {
            "MALag": 40,
            "DecayNum": 15
        }
    },
    {
        "FactorName": "factorTransPressureVol",
        "ClassName": "FactorTransPressureVolModified",
        "Parameters": {
            "MALag": 40,
            "DecayNum": 15
        }
    },
    {
        "FactorName": "factorTransSellBuy5",
        "ClassName": "FactorTransSellBuy",
        "Parameters": {
            "Lag": 5,
            "DecayNum": 40
        }
    },
    {
        "FactorName": "factorTransSellBuy10",
        "ClassName": "FactorTransSellBuy",
        "Parameters": {
            "Lag": 10,
            "DecayNum": 40
        }
    },
    {
        "FactorName": "factorTransSellVolumeDistance5_10",
        "ClassName": "FactorTransSellVolumeDistance",
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
        "Parameters": {
            "FastLag": 10
        }
    },

]

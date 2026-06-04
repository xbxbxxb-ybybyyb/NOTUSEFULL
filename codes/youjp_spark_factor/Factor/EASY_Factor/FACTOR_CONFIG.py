FACTOR_CONFIG = [

    {
        "FactorName": "factortradeAskBidNumber",
        "ClassName": "FactortradeAskBidNumber",
        "FactorSource": "Easy",
        "Parameters": {
            "MALag": 40,
            "DecayNum": 15
        }
    },

    {
        "FactorName": "factortradeAskBidVolume",
        "ClassName": "FactortradeAskBidVolume",
        "FactorSource": "Easy",
        "Parameters": {
            "MALag": 40,
            "DecayNum": 15
        }
    },

    {
        "FactorName": "factorActiveBuyVolGrowth10",
        "ClassName": "FactorActiveBuyVolGrowth",
        "FactorSource": "Easy",
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
        "Parameters": {
            "FastLag": 30,
            "SlowLag": 60
        }
    },

    {
        "FactorName": "factorPriceChangeSpeed",
        "ClassName": "FactorPriceChangeSpeed",
        "FactorSource": "Easy",
        "Parameters": {
            "FastLag": 30,
            "SlowLag": 60
        }
    },

    {
        "FactorName": "factorAccBuyAmountRatio",
        "ClassName": "FactorAccBuyAmountRatio",
        "FactorSource": "Easy",
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
        "TickLength": 1,
        "Parameters": {
            "LookBack": 4730
        }
    },

    {
        "FactorName": "factorTickSellAmountRatio",
        "ClassName": "FactorTickSellAmountRatio",
        "FactorSource": "Easy",
        "TickLength": 1,
        "Parameters": {
            "LookBack": 4730
        }
    },

    {
        "FactorName": "factorAvePrice20Growth",
        "ClassName": "FactorAvePriceGrowth",
        "FactorSource": "Easy",
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 20
        }
    },

    {
        "FactorName": "factorAvePrice40Growth",
        "ClassName": "FactorAvePriceGrowth",
        "FactorSource": "Easy",
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 40
        }
    },

    {
        "FactorName": "factorAvePrice100Growth",
        "ClassName": "FactorAvePriceGrowth",
        "FactorSource": "Easy",
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 100
        }
    },

    {
        "FactorName": "factorAvePrice200Growth",
        "ClassName": "FactorAvePriceGrowth",
        "Parameters": {
            "FastLag": 3,
            "SlowLag": 200
        }
    },

    {
        "FactorName": "factorAveVolume3Growth",
        "ClassName": "FactorAveVolumeGrowth",
        "FactorSource": "Easy",
        "TickLength": 1,
        "Parameters": {
            "MALag": 3
        }
    },

    {
        "FactorName": "factorAveVolume20Growth",
        "ClassName": "FactorAveVolumeGrowth",
        "FactorSource": "Easy",
        "TickLength": 1,
        "Parameters": {
            "MALag": 20
        }
    },

    {
        "FactorName": "factorAveVolume40Growth",
        "ClassName": "FactorAveVolumeGrowth",
        "FactorSource": "Easy",
        "TickLength": 1,
        "Parameters": {
            "MALag": 40
        }
    },

    {
        "FactorName": "factorAveVolume100Growth",
        "ClassName": "FactorAveVolumeGrowth",
        "FactorSource": "Easy",
        "TickLength": 1,
        "Parameters": {
            "MALag": 100
        }
    },

    {
        "FactorName": "factorAveVolume200Growth",
        "ClassName": "FactorAveVolumeGrowth",
        "FactorSource": "Easy",
        "TickLength": 1,
        "Parameters": {
            "MALag": 200
        }
    },

    {
        "FactorName": "factorVolumeMAGrowthFixed20",
        "ClassName": "FactorVolumeMAGrowthFixed",
        "FactorSource": "Easy",
        "Parameters": {
            "MALag": 10,
            "LookBack": 20
        }
    },

    {
        "FactorName": "factorVolumeMAGrowthFixed40",
        "ClassName": "FactorVolumeMAGrowthFixed",
        "FactorSource": "Easy",
        "Parameters": {
            "MALag": 10,
            "LookBack": 40
        }
    },

    {
        "FactorName": "factorVolumeMAGrowthFixed100",
        "ClassName": "FactorVolumeMAGrowthFixed",
        "FactorSource": "Easy",
        "Parameters": {
            "MALag": 10,
            "LookBack": 100
        }
    },

    {
        "FactorName": "factorVolumeMAGrowthFlexible20",
        "ClassName": "FactorVolumeMAGrowthFlexible",
        "FactorSource": "Easy",
        "TickLength": 1,
        "Parameters": {
            "MALag": 20
        }
    },

    {
        "FactorName": "factorVolumeMAGrowthFlexible40",
        "ClassName": "FactorVolumeMAGrowthFlexible",
        "FactorSource": "Easy",
        "TickLength": 1,
        "Parameters": {
            "MALag": 40
        }
    },

    {
        "FactorName": "factorVolumeMAGrowthFlexible100",
        "ClassName": "FactorVolumeMAGrowthFlexible",
        "FactorSource": "Easy",
        "TickLength": 1,
        "Parameters": {
            "MALag": 100
        }
    },

    {
        "FactorName": "factorDistanceToAvePrice",
        "ClassName": "FactorDistanceToAvePrice",
        "FactorSource": "Easy",
        "Parameters": { }
    },

    {
        "FactorName": "factorEMAPressureRatio",
        "ClassName": "FactorEMAPressureRatio",
        "FactorSource": "Easy",
        "Parameters": {
            "OrderEvaluateEMALag": 15
        }
    },

    {
        "FactorName": "factorOrderBookVolumePressure",
        "ClassName": "FactorOrderBookVolumePressure",
        "FactorSource": "Easy",
        "Parameters": {
            "EMALag": 10,
            "DecayRatio": 0.8
        }
    },

    {
        "FactorName": "factorOrderBookLv1Pressure",
        "ClassName": "FactorOrderBookLv1Pressure",
        "FactorSource": "Easy",
        "Parameters": {
            "EMALag": 5
        }
    },

    {
        "FactorName": "factorVolumeAmp",
        "ClassName": "FactorVolumeAmp",
        "FactorSource": "Easy",
        "Parameters": {
            "Lag": 10
        }
    },

    {
        "FactorName": "factorReversal",
        "ClassName": "FactorReversal",
        "FactorSource": "Easy",
        "TickLength": 1,
        "Parameters": {
            "ShortLag": 20,
            "LongLag": 100,
            "EMALag": 10,
            "LookBack": 4730
        }
    },

    {
        "FactorName": "factorSpeed",
        "ClassName": "FactorSpeed",
        "FactorSource": "Easy",
        "Parameters": {
            "Lag": 10,
            "SpeedLag": 5
        }
    }

]

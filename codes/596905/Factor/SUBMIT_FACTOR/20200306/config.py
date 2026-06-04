FACTOR_CONFIG = [

    {
        "FactorName": "factorOrderBookAskVolumeShift",
        "ClassName": "FactorOrderBookAskVolumeShift",
        "Parameters": {"Lag": 20,
                       "Decay": 0.8}
    },

    {
        "FactorName": "factorOrderBookBidVolumeShift",
        "ClassName": "FactorOrderBookBidVolumeShift",
        "Parameters": {"Lag": 20,
                       "Decay": 0.8}
    },

    {
        "FactorName": "factorPankouBidPressure",
        "ClassName": "FactorPankouBidPressure",
        "Parameters": {"SliceNum": 4}
    },

    {
        "FactorName": "factorPankouPressure",
        "ClassName": "FactorPankouPressure",
        "Parameters": {"SliceNum": 4}
    }

]

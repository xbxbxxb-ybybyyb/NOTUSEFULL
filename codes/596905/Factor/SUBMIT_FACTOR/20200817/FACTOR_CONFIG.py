FACTOR_CONFIG = [

    {
        "FactorName": "factorPriceDiffSharpe",
        "ClassName": "FactorPriceDiffSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": {"T"},
        "NonFactors": {"AvePrice", "MidPrice"},
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
        "DataSource": {"T"},
        "NonFactors": {"AvePrice"},
        "Parameters": {
            "Window": 200
        }
    },

    {
        "FactorName": "factorAskNumSharpe",
        "ClassName": "FactorAskNumSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": {"TR"},
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorBidNumSharpe",
        "ClassName": "FactorBidNumSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": {"TR"},
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorAskVolumeSharpe",
        "ClassName": "FactorAskVolumeSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": {"TR"},
        "Parameters": {
            "Lag": 20
        }
    },

    {
        "FactorName": "factorBidVolumeSharpe",
        "ClassName": "FactorBidVolumeSharpe",
        "FactorSource": "Zeus",
        "FactorType": "TS",
        "DataSource": {"TR"},
        "Parameters": {
            "Lag": 20
        }
    }
]

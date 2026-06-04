{
    "outputDir": "order_pressure/",
    "StrategyName": "AlgoShaolin",
    "TradingUnderlyingCode": [],
    "FactorUnderlyingCode": [],
    "StartDateTime": 20170101093015,
    "EndDateTime": 20190630145659,
    "FactorSet": [{"name": "factorOrderPressure",
                   "className": "FactorOrderPressureModified2",
                   "indexTradingUnderlying": [0],
                   "indexFactorUnderlying": [],
                   "paraOrderPressureLag": 15,
                   "save": true}],

    "Tag": {"indexTradingUnderlying": [0], "indexFactorUnderlying": [], "paraMaxDropHorizon": 0.002,
            "paraEmaMidPriceLag": 4, "paraOrderPressureLag": 4, "paraNumOrderMax": 5, "paraNumOrderMin": 1,
            "paraEmaSlicePressureLag": 8, "paraMaxLose": 0.004, "paraFastLag": 10, "paraSlowLag": 20}
}

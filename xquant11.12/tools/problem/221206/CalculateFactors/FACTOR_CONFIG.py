{
    "outputDir": "output",
    "StrategyName": "AlgoShaolin",
    "LibraryName": "HF_Apple_Alpha",
    "TagNames": ["timestamp", "tag1minLong", "tag1minShort", "tag2minLong", "tag2minShort",
                 "tag5minLong", "tag5minShort", "tag10minLong", "tag10minShort"],
    "UseConfigTradingUnderlyingCode": "false",
    "TradingUnderlyingCode": [],
    "FactorUnderlyingCode": [],
    "StartDateTime": 20161230093015,
    "EndDateTime": 20180101145659,
    "FactorSet":
        [
            {"name": "factorMAVolumeDistance10_20", "className": "FactorMAVolumeDistanceModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAFastLag": 10, "paraMASlowLag": 20, "save": true},

            {"name": "factorTransBuyVolumeDistance5_40", "className": "FactorTransBuyVolumeDistance",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAFastLag": 5, "paraMASlowLag": 40, "paraMALag": 40, "paraDecayNum": 15,
             "save": true},

            {"name": "factorDistanceToHigh100", "className": "FactorDistanceToHighModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraLag": 100, "save": true},

            {"name": "factorDistanceBetweenVWAPPrice40", "className": "FactorDistanceBetweenVWAPPriceModified",
             "indexTradingUnderlying": [0], "indexFactorUnderlying": [], "paraFastLag": 3, "paraSlowLag": 40,
             "save": true},

            {"name": "factorTransVolumeWeightedSwing5_10", "className": "FactorTransVolumeWeightedSwing",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraDiffLag": 5, "paraVolumeLag": 10, "paraMALag": 40, "paraDecayNum": 15,
             "save": true},

            {"name": "factorDistanceToLow40", "className": "FactorDistanceToLowModified", "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraLag": 40, "save": true},

            {"name": "factorBuyPower", "className": "FactorBuyPower", "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAAmountLag": 4730, "save": true},

            {"name": "factorTransSellVolumeDistance5_10", "className": "FactorTransSellVolumeDistance",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAFastLag": 5, "paraMASlowLag": 10, "paraMALag": 40, "paraDecayNum": 15,
             "save": true},

            {"name": "factorDistanceToLow100", "className": "FactorDistanceToLowModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraLag": 100, "save": true},

            {"name": "factorDistanceBetweenVWAPPrice200", "className": "FactorDistanceBetweenVWAPPriceModified",
             "indexTradingUnderlying": [0], "indexFactorUnderlying": [], "paraFastLag": 3, "paraSlowLag": 200,
             "save": true},

            {"name": "factorSellPower", "className": "FactorSellPower", "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAAmountLag": 4730, "save": true},

            {"name": "factorCrossPriceChangeRatio", "className": "FactorCrossPriceChangeRatio",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraFastLag": 30, "paraSlowLag": 60, "save": true},

            {"name": "factorMomentum", "className": "FactorMomentumModified",
             "indexTradingUnderlying": [0], "indexFactorUnderlying": [],
             "paraLag": 3, "paraEmaMidPriceLag": 5, "paraMAAmountLag": 4730, "save": true},

            {"name": "factorEmaOrderVolumePressure", "className": "FactorEmaOrderVolumePressure",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraNumOrderMax": 10, "paraNumOrderMin": 1,
             "paraEmaOrderVolumePressureLag": 10, "weightDecay": 0.8,
             "save": true},

            {"name": "factorTransPressureVol", "className": "FactorTransPressureVolModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMALag": 40, "paraDecayNum": 15, "save": true},

            {"name": "factorDistanceBetweenVWAPPrice100", "className": "FactorDistanceBetweenVWAPPriceModified",
             "indexTradingUnderlying": [0], "indexFactorUnderlying": [], "paraFastLag": 3, "paraSlowLag": 100,
             "save": true},

            {"name": "factorTransPressure", "className": "FactorTransPressureModified", "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMALag": 40, "paraDecayNum": 15, "save": true},

            {"name": "factorOrderMomentum", "className": "FactorOrderMomentum", "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "save": true},

            {"name": "factorSpeed", "className": "FactorSpeedModified", "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [],
             "paraLag": 5.0, "paraEmaMidPriceLag": 10, "save": true},

            {"name": "factorDistanceToVwap100", "className": "FactorDistanceToVwapModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraLag": 100, "save": true},

            {"name": "factorMAVolumeDistance20", "className": "FactorMAVolumeDistanceModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAFastLag": 20, "paraMASlowLag": 4730, "save": true},

            {"name": "factorTransSellBuy5", "className": "FactorTransSellBuy", "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraLag": 5, "paraDecayNum": 40, "save": true},

            {"name": "factorMAVolumeDistance10_100", "className": "FactorMAVolumeDistanceModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAFastLag": 10, "paraMASlowLag": 100, "save": true},

            {"name": "factorDistanceToVwap20", "className": "FactorDistanceToVwapModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraLag": 20, "save": true},

            {"name": "factorBuyPowerSpeed", "className": "FactorBuyPowerSpeed", "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraOrderPressureLag": 5, "paraMAAmountLag": 20, "save": true},

            {"name": "factorSellPowerSpeed", "className": "FactorSellPowerSpeed", "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraOrderPressureLag": 5, "paraMAAmountLag": 20, "save": true},

            {"name": "factorDistanceToAvePrice", "className": "FactorDistanceToAvePriceModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "save": true},

            {"name": "factorDistanceToVwap40", "className": "FactorDistanceToVwapModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraLag": 40, "save": true},

            {"name": "factorMAVolumeDistance3", "className": "FactorMAVolumeDistanceModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAFastLag": 3, "paraMASlowLag": 4730, "save": true},

            {"name": "factorVolumeMagnification", "className": "FactorVolumeMagnificationModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraFastLag": 10, "paraSlowLag": null, "save": true},

            {"name": "factorTransVolumeWeightedSwing5_40", "className": "FactorTransVolumeWeightedSwing",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraDiffLag": 5, "paraVolumeLag": 40, "paraMALag": 40, "paraDecayNum": 15,
             "save": true},

            {"name": "factorMAVolumeDistance40_80", "className": "FactorMAVolumeDistanceModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAFastLag": 40, "paraMASlowLag": 80, "save": true},

            {"name": "factorOrderPressure", "className": "FactorOrderPressureModified2", "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraOrderPressureLag": 15, "save": true},

            {"name": "factorMAVolumeDistance100_200", "className": "FactorMAVolumeDistanceModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAFastLag": 100, "paraMASlowLag": 200, "save": true},

            {"name": "factorDistanceToVwapPriceWeighted", "className": "FactorDistanceToVwapPriceWeighted",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMATinyLag": 10, "paraMAShortLag": 20, "paraMALongLag": 100,
             "paraMASlowLag": 4730, "save": true},

            {"name": "factorDistanceBetweenVWAPPrice20", "className": "FactorDistanceBetweenVWAPPriceModified",
             "indexTradingUnderlying": [0], "indexFactorUnderlying": [], "paraFastLag": 3, "paraSlowLag": 20,
             "save": true},

            {"name": "factorMAVolumeDistance100", "className": "FactorMAVolumeDistanceModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAFastLag": 100, "paraMASlowLag": 4730, "save": true},

            {"name": "factorEmaOrderAmountPressure", "className": "FactorEmaOrderAmountPressure",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraNumOrderMax": 1, "paraNumOrderMin": 1,
             "paraEmaOrderAmountPressureLag": 5, "weightDecay": 0.8,
             "save": true},

            {"name": "factorMAVolumeDistance40", "className": "FactorMAVolumeDistanceModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAFastLag": 40, "paraMASlowLag": 4730, "save": true},

            {"name": "factorCrossPriceChangeSpeed", "className": "FactorCrossPriceChangeSpeed",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraFastLag": 30, "paraSlowLag": 60, "save": true},

            {"name": "factorTransSellBuy10", "className": "FactorTransSellBuy", "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraLag": 10, "paraDecayNum": 40, "save": true},

            {"name": "factorTransBuyVolumeDistance5_10", "className": "FactorTransBuyVolumeDistance",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAFastLag": 5, "paraMASlowLag": 10, "paraMALag": 40, "paraDecayNum": 15,
             "save": true},

            {"name": "factorMAVolumeDistance20_40", "className": "FactorMAVolumeDistanceModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAFastLag": 20, "paraMASlowLag": 40, "save": true},

            {"name": "factorTransSellVolumeDistance5_40", "className": "FactorTransSellVolumeDistance",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAFastLag": 5, "paraMASlowLag": 40, "paraMALag": 40, "paraDecayNum": 15,
             "save": true},

            {"name": "factorMAVolumeDistance10_40", "className": "FactorMAVolumeDistanceModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAFastLag": 10, "paraMASlowLag": 40, "save": true},

            {"name": "factorMAVolumeDistance200", "className": "FactorMAVolumeDistanceModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraMAFastLag": 200, "paraMASlowLag": 4730, "save": true},

            {"name": "factorDistanceToHigh40", "className": "FactorDistanceToHighModified",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraLag": 40, "save": true},

            {"name": "factorBoll", "className": "FactorBoll",
             "indexTradingUnderlying": [0],
             "indexFactorUnderlying": [], "paraBollLag": 20, "paraWidth": 2, "save": true}
        ],

    "Tag": {"indexTradingUnderlying": [0], "indexFactorUnderlying": [], "paraMaxDropHorizon": 0.002,
            "paraEmaMidPriceLag": 4, "paraOrderPressureLag": 4, "paraNumOrderMax": 5, "paraNumOrderMin": 1,
            "paraEmaSlicePressureLag": 8, "paraMaxLose": 0.004, "paraFastLag": 10, "paraSlowLag": 20}

}

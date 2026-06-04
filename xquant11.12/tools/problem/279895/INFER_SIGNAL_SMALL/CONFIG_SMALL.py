import sys
import os


class InferSignalConfig:
    def __init__(self):

        self.test_start_date = "20200101"
        self.test_end_date = "20200117"

        self.model_name = "../test_model"
        self.model_path =  self.model_name + "/"
        self.signal_path = None

        self.library_name = "HF_Apple_Alpha"
        self.factor_names = [
            "factorMAVolumeDistance10_20", "factorTransBuyVolumeDistance5_40", "factorDistanceToHigh100",
            "factorDistanceBetweenVWAPPrice40", "factorTransVolumeWeightedSwing5_10", "factorDistanceToLow40",
            "factorBuyPower", "factorTransSellVolumeDistance5_10", "factorDistanceToLow100",
            "factorDistanceBetweenVWAPPrice200", "factorSellPower", "factorCrossPriceChangeRatio", "factorMomentum",
            "factorEmaOrderVolumePressure", "factorTransPressureVol", "factorDistanceBetweenVWAPPrice100",
            "factorTransPressure", "factorOrderMomentum", "factorSpeed", "factorDistanceToVwap100",
            "factorMAVolumeDistance20", "factorTransSellBuy5", "factorMAVolumeDistance10_100", "factorDistanceToVwap20",
            "factorBuyPowerSpeed", "factorSellPowerSpeed", "factorDistanceToAvePrice",  "factorDistanceToVwap40",
            "factorMAVolumeDistance3", "factorVolumeMagnification", "factorTransVolumeWeightedSwing5_40",
            "factorMAVolumeDistance40_80", "factorOrderPressure", "factorMAVolumeDistance100_200",
            "factorDistanceToVwapPriceWeighted", "factorDistanceBetweenVWAPPrice20", "factorMAVolumeDistance100",
            "factorEmaOrderAmountPressure", "factorMAVolumeDistance40", "factorCrossPriceChangeSpeed",
            "factorTransSellBuy10", "factorTransBuyVolumeDistance5_10", "factorMAVolumeDistance20_40",
            "factorTransSellVolumeDistance5_40", "factorMAVolumeDistance10_40", "factorMAVolumeDistance200",
            "factorDistanceToHigh40", "factorBoll"
        ]
        self.tag_names = [["1minLong", "1minShort"], ["2minLong", "2minShort"], ["5minLong", "5minShort"]]
        self.tag_dict = {
            "1minLong": "tag1minLong",
            "1minShort": "tag1minShort",
            "2minLong": "tag2minLong",
            "2minShort": "tag2minShort",
            "5minLong": "tag5minLong",
            "5minShort": "tag5minShort"
        }



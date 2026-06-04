import os
import pandas as pd
from System.TradingDay import getTradingDay
from xquant.bonddata import BondData

bd = BondData()

class InferSignalConfig:
    def __init__(self):
        self.test_start_date = "20200903"
        self.test_end_date = "20200903"

        self.codes = []
        for date in getTradingDay(int(self.test_start_date), int(self.test_end_date)):
            self.codes.extend(bd.get_bond_set(str(date), "kzz"))
        self.codes = list(set(self.codes))

        # self.model_ver = "big_20191101_universe_ray_cb_stock_new_finetune"
        # self.model_path = "/data/user/666888/chensf/big_20191101_universe_ray_cb_stock_new_finetune/"

        # self.model_ver = "big_cb_stock_20191101_20200413"
        # self.model_path = "/data/user/666888/chensf/big_cb_stock_20191101_20200413/"
        self.model_ver = "big_cb_stock_20200301_20200413"
        self.model_path = "/data/user/666888/chensf/big_cb_stock_20200301_20200413/"

        # self.library_name = ["CBFactor4"]
        # self.library_nameS = ["AlgoFactor48_3"]
        # self.factor_names = [
            # [
                # "factorMAVolumeDistance10_20", "factorTransBuyVolumeDistance5_40", "factorDistanceToHigh100",
                # "factorDistanceBetweenVWAPPrice40", "factorTransVolumeWeightedSwing5_10", "factorDistanceToLow40",
                # "factorBuyPower", "factorTransSellVolumeDistance5_10", "factorDistanceToLow100",
                # "factorDistanceBetweenVWAPPrice200", "factorSellPower", "factorCrossPriceChangeRatio", "factorMomentum",
                # "factorEmaOrderVolumePressure", "factorTransPressureVol", "factorDistanceBetweenVWAPPrice100",
                # "factorTransPressure", "factorOrderMomentum", "factorSpeed", "factorDistanceToVwap100",
                # "factorMAVolumeDistance20", "factorTransSellBuy5", "factorMAVolumeDistance10_100",
                # "factorDistanceToVwap20",
                # "factorBuyPowerSpeed", "factorSellPowerSpeed", "factorDistanceToAvePrice", "factorDistanceToVwap40",
                # "factorMAVolumeDistance3", "factorVolumeMagnification", "factorTransVolumeWeightedSwing5_40",
                # "factorMAVolumeDistance40_80", "factorOrderPressure", "factorMAVolumeDistance100_200",
                # "factorDistanceToVwapPriceWeighted", "factorDistanceBetweenVWAPPrice20", "factorMAVolumeDistance100",
                # "factorEmaOrderAmountPressure", "factorMAVolumeDistance40", "factorCrossPriceChangeSpeed",
                # "factorTransSellBuy10", "factorTransBuyVolumeDistance5_10", "factorMAVolumeDistance20_40",
                # "factorTransSellVolumeDistance5_40", "factorMAVolumeDistance10_40", "factorMAVolumeDistance200",
                # "factorDistanceToHigh40", "factorBoll"
            # ],
        # ]
        # self.factor_namesS = [
            # [
                # "factorMAVolumeDistance10_20", "factorTransBuyVolumeDistance5_40", "factorDistanceToHigh100",
                # "factorDistanceBetweenVWAPPrice40", "factorTransVolumeWeightedSwing5_10", "factorDistanceToLow40",
                # "factorBuyPower", "factorTransSellVolumeDistance5_10", "factorDistanceToLow100",
                # "factorDistanceBetweenVWAPPrice200", "factorSellPower", "factorCrossPriceChangeRatio", "factorMomentum",
                # "factorEmaOrderVolumePressure", "factorTransPressureVol", "factorDistanceBetweenVWAPPrice100",
                # "factorTransPressure", "factorOrderMomentum", "factorSpeed", "factorDistanceToVwap100",
                # "factorMAVolumeDistance20", "factorTransSellBuy5", "factorMAVolumeDistance10_100",
                # "factorDistanceToVwap20",
                # "factorBuyPowerSpeed", "factorSellPowerSpeed", "factorDistanceToAvePrice", "factorDistanceToVwap40",
                # "factorMAVolumeDistance3", "factorVolumeMagnification", "factorTransVolumeWeightedSwing5_40",
                # "factorMAVolumeDistance40_80", "factorOrderPressure", "factorMAVolumeDistance100_200",
                # "factorDistanceToVwapPriceWeighted", "factorDistanceBetweenVWAPPrice20", "factorMAVolumeDistance100",
                # "factorEmaOrderAmountPressure", "factorMAVolumeDistance40", "factorCrossPriceChangeSpeed",
                # "factorTransSellBuy10", "factorTransBuyVolumeDistance5_10", "factorMAVolumeDistance20_40",
                # "factorTransSellVolumeDistance5_40", "factorMAVolumeDistance10_40", "factorMAVolumeDistance200",
                # "factorDistanceToHigh40", "factorBoll"
            # ],
        # ]

        self.library_name = ["CBFactor_Zeus_Super"]
        self.library_nameS = ["Factor_Zeus_Plus"]
        self.factor_names = [
            ['factorMAVolumeDistance10_20', 'factorTransBuyVolumeDistance5_40', 'factorDistanceToHigh100',
            'factorDistanceBetweenVWAPPrice40', 'factorTransVolumeWeightedSwing5_10', 'factorDistanceToLow40', 'factorBuyPower',
            'factorTransSellVolumeDistance5_10', 'factorDistanceToLow100', 'factorDistanceBetweenVWAPPrice200',
            'factorSellPower', 'factorCrossPriceChangeRatio', 'factorMomentum', 'factorEmaOrderVolumePressure',
            'factorTransPressureVol', 'factorDistanceBetweenVWAPPrice100', 'factorTransPressure', 'factorOrderMomentum',
            'factorSpeed', 'factorDistanceToVwap100', 'factorMAVolumeDistance20', 'factorTransSellBuy5',
            'factorMAVolumeDistance10_100', 'factorDistanceToVwap20', 'factorBuyPowerSpeed', 'factorSellPowerSpeed',
            'factorDistanceToAvePrice', 'factorDistanceToVwap40', 'factorMAVolumeDistance3', 'factorVolumeMagnification',
            'factorTransVolumeWeightedSwing5_40', 'factorMAVolumeDistance40_80', 'factorOrderPressure',
            'factorMAVolumeDistance100_200', 'factorDistanceToVwapPriceWeighted', 'factorDistanceBetweenVWAPPrice20',
            'factorMAVolumeDistance100', 'factorEmaOrderAmountPressure', 'factorMAVolumeDistance40',
            'factorCrossPriceChangeSpeed', 'factorTransSellBuy10', 'factorTransBuyVolumeDistance5_10',
            'factorMAVolumeDistance20_40', 'factorTransSellVolumeDistance5_40', 'factorMAVolumeDistance10_40',
            'factorMAVolumeDistance200', 'factorDistanceToHigh40', 'factorBoll', 'factorFlex40AskAmtPerTradeZScore', 'factorRet20SR200', 'factorRet20MaxMinSum120', 'factor20BidAmtPerTradeZScore', 'factorTrackVolatility', 'factorRet20Std200', 'factorSR', 'factor200PVMove', 'factor200AskAmtPerTrade', 'factorPVPercentile300_10', 'factorWeightedReturns', 'factorRet60Max300', 'factorTickJump', 'factorRiseCo60MulRoc40', 'factorDistanceToVwapVolume', 'factor40PVMove', 'factorOrderBookAskVolumeShift', 'factorOrderBookBidVolumeShift', 'factorPankouPressure', 'factorFlex200AskAmtPerTradeZScore', 'factorSpeedToVwap', 'factorFlex20RelAskAmtPerTrade', 'factorRet60MaxMinSum300', 'factor40BidAmtPerTradeZScore', 'factor20AskAmtPerTrade', 'factorAmtRatioPerPrice60', 'factor100RelBidAmtPerTrade', 'factorRet2Range300', 'factorFlex20BidAmtPerTradeZScore', 'factorFlex100RelBidAmtPerTrade', 'factorAskBidOrderNumberVolatility', 'factorRetWeightedByVol10_60', 'factor20BidAmtPerTrade', 'factorAskBidNumRatioStd', 'factorRetMulVol200', 'factor40BidAmtPerTradeStd', 'factorRet20Mean200', 'factorRiseCoordination90', 'factorPankouBidPressure', 'factor200BidAmtPerTrade', 'factorMidPriceSkew300', 'factorFlex20RelBidAmtPerTrade', 'factor40AskAmtPerTradeStd', 'factorRet20Max120', 'factorHighDistance600', 'factor100RelAskAmtPerTrade', 'factorVolumeOutbreakCurrent', 'factorEntrustRatio200']
        ]
        self.factor_namesS = [
            ["factorMAVolumeDistance10_20", "factorTransBuyVolumeDistance5_40", "factorDistanceToHigh100",
            "factorDistanceBetweenVWAPPrice40", "factorTransVolumeWeightedSwing5_10", "factorDistanceToLow40", "factorBuyPower",
            "factorTransSellVolumeDistance5_10", "factorDistanceToLow100", "factorDistanceBetweenVWAPPrice200",
            "factorSellPower", "factorCrossPriceChangeRatio", "factorMomentum", "factorEmaOrderVolumePressure",
            "factorTransPressureVol", "factorDistanceBetweenVWAPPrice100", "factorTransPressure", "factorOrderMomentum",
            "factorSpeed", "factorDistanceToVwap100", "factorMAVolumeDistance20", "factorTransSellBuy5",
            "factorMAVolumeDistance10_100", "factorDistanceToVwap20", "factorBuyPowerSpeed", "factorSellPowerSpeed",
            "factorDistanceToAvePrice", "factorDistanceToVwap40", "factorMAVolumeDistance3", "factorVolumeMagnification",
            "factorTransVolumeWeightedSwing5_40", "factorMAVolumeDistance40_80", "factorOrderPressure",
            "factorMAVolumeDistance100_200", "factorDistanceToVwapPriceWeighted", "factorDistanceBetweenVWAPPrice20",
            "factorMAVolumeDistance100", "factorEmaOrderAmountPressure", "factorMAVolumeDistance40",
            "factorCrossPriceChangeSpeed", "factorTransSellBuy10", "factorTransBuyVolumeDistance5_10",
            "factorMAVolumeDistance20_40", "factorTransSellVolumeDistance5_40", "factorMAVolumeDistance10_40",
            "factorMAVolumeDistance200", "factorDistanceToHigh40", "factorBoll", 'factorFlex40AskAmtPerTradeZScore', 'factorRet20SR200', 'factorRet20MaxMinSum120', 'factor20BidAmtPerTradeZScore', 'factorTrackVolatility', 'factorRet20Std200', 'factorSR', 'factor200PVMove', 'factor200AskAmtPerTrade', 'factorPVPercentile300_10', 'factorWeightedReturns', 'factorRet60Max300', 'factorTickJump', 'factorRiseCo60MulRoc40', 'factorDistanceToVwapVolume', 'factor40PVMove', 'factorOrderBookAskVolumeShift', 'factorOrderBookBidVolumeShift', 'factorPankouPressure', 'factorFlex200AskAmtPerTradeZScore', 'factorSpeedToVwap', 'factorFlex20RelAskAmtPerTrade', 'factorRet60MaxMinSum300', 'factor40BidAmtPerTradeZScore', 'factor20AskAmtPerTrade', 'factorAmtRatioPerPrice60', 'factor100RelBidAmtPerTrade', 'factorRet2Range300', 'factorFlex20BidAmtPerTradeZScore', 'factorFlex100RelBidAmtPerTrade', 'factorAskBidOrderNumberVolatility', 'factorRetWeightedByVol10_60', 'factor20BidAmtPerTrade', 'factorAskBidNumRatioStd', 'factorRetMulVol200', 'factor40BidAmtPerTradeStd', 'factorRet20Mean200', 'factorRiseCoordination90', 'factorPankouBidPressure', 'factor200BidAmtPerTrade', 'factorMidPriceSkew300', 'factorFlex20RelBidAmtPerTrade', 'factor40AskAmtPerTradeStd', 'factorRet20Max120', 'factorHighDistance600', 'factor100RelAskAmtPerTrade', 'factorVolumeOutbreakCurrent', 'factorEntrustRatio200']
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

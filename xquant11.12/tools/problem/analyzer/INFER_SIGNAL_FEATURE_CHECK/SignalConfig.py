import sys
import pandas as pd
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
from xquant.factordata import FactorData
from INFER_SIGNAL_FEATURE.STOCK_LIST import STOCK_LIST

class InferSignalConfig:
    def __init__(self):
        self.fa = FactorData()
        self.test_start_date = "20200816"
        self.test_end_date = "20200831"
        self.next_trading_day = self.test_end_date

        self.model_name = "20200313"
        self.model_path = "/data/user/015629/chensf/new_easy_20201001_20201019/"
        self.signal_library = "EasySeparate1019Features"
        self.signal_path = "EasySignal/" + self.model_name + "/"
        self.log_path = "/data/user/015629/EasyInferSignal"

        self.code_list = self.get_missing_code_list()

        self.is_multiprocess = True

        self.library_name = "Factor_Zeus_Plus"

        self.tag_names = [["1minLong", "1minShort"], ["2minLong", "2minShort"], ["5minLong", "5minShort"]]
        self.factor_names, self.factorIndex = self.get_factor_names_indexes()
        self.factor_name_list = self.factor_names

        self.tag_dict = {
            "1minLong": "tag1minLong",
            "1minShort": "tag1minShort",
            "2minLong": "tag2minLong",
            "2minShort": "tag2minShort",
            "5minLong": "tag5minLong",
            "5minShort": "tag5minShort"
        }

    def get_factor_names_indexes(self):
        factor_name_dict = {}
        model_factor_set = set()
        for tagNameList in self.tag_names:
            for tag in tagNameList:
                tag_file_name = "/data/user/015629/chensf/new_easy_20201001_20201019/" + "{}_corr_label_be_nf.csv".format(tag)
                tag_factor_list = pd.read_csv(tag_file_name, index_col=0).iloc[:, 0].tolist()
                factor_name_dict.update({tag: tag_factor_list})
                model_factor_set = model_factor_set.union(tag_factor_list)

        model_factor_list = sorted(list(model_factor_set))
        print(" Model Total Factor Number: {}".format(len(model_factor_list)))

        libraryInfo = self.fa.get_library_info()
        libraryFactor = libraryInfo[self.library_name]
        factor_names = sorted(list(set(model_factor_list).intersection(libraryFactor)))
        factor_names = ['factorMAVolumeDistance10_20', 'factorTransBuyVolumeDistance5_40', 'factorDistanceToHigh100',
                      'factorDistanceBetweenVWAPPrice40', 'factorTransVolumeWeightedSwing5_10', 'factorDistanceToLow40',
                      'factorBuyPower',
                      'factorTransSellVolumeDistance5_10', 'factorDistanceToLow100',
                      'factorDistanceBetweenVWAPPrice200', 'factorSellPower',
                      'factorCrossPriceChangeRatio', 'factorMomentum', 'factorEmaOrderVolumePressure',
                      'factorTransPressureVol',
                      'factorDistanceBetweenVWAPPrice100', 'factorTransPressure', 'factorOrderMomentum', 'factorSpeed',
                      'factorDistanceToVwap100', 'factorMAVolumeDistance20', 'factorTransSellBuy5',
                      'factorMAVolumeDistance10_100',
                      'factorDistanceToVwap20', 'factorBuyPowerSpeed', 'factorSellPowerSpeed',
                      'factorDistanceToAvePrice',
                      'factorDistanceToVwap40', 'factorMAVolumeDistance3', 'factorVolumeMagnification',
                      'factorTransVolumeWeightedSwing5_40',
                      'factorMAVolumeDistance40_80', 'factorOrderPressure', 'factorMAVolumeDistance100_200',
                      'factorDistanceToVwapPriceWeighted',
                      'factorDistanceBetweenVWAPPrice20', 'factorMAVolumeDistance100', 'factorEmaOrderAmountPressure',
                      'factorMAVolumeDistance40', 'factorCrossPriceChangeSpeed', 'factorTransSellBuy10',
                      'factorTransBuyVolumeDistance5_10',
                      'factorMAVolumeDistance20_40', 'factorTransSellVolumeDistance5_40', 'factorMAVolumeDistance10_40',
                      'factorMAVolumeDistance200', 'factorDistanceToHigh40', 'factorBoll', 'factor40PredRetBaseAmt',
                      'factor200PredRetBaseAmt',
                      'factor40IlliqBidAmt', 'factor100IlliqBidAmt', 'factor100IlliqAskAmt', 'factor200IlliqAskAmt',
                      'factorFlex20RelAskAmtPerTrade', 'factorFlex200AskAmtPerTradeZScore',
                      'factorFlex40AskAmtPerTradeZScore',
                      'factorFlex20BidAmtPerTradeZScore', 'factorFlex100RelBidAmtPerTrade',
                      'factorFlex20RelBidAmtPerTrade',
                      'factor40BidAmtPerTradeZScore', 'factor20BidAmtPerTradeZScore', 'factor100RelBidAmtPerTrade',
                      'factor100RelAskAmtPerTrade', 'factor40AskAmtPerTradeStd', 'factor40BidAmtPerTradeStd',
                      'factor20BidAmtPerTrade',
                      'factor20AskAmtPerTrade', 'factor200AskAmtPerTrade', 'factor200BidAmtPerTrade',
                      'factorAskBidNumRatioStd',
                      'factor40PVMove', 'factor200PVMove', 'factor20Reverse', 'factor200Reverse',
                      'factor40RealReverseAskAmt',
                      'factor40RealReverseBidAmt', 'factor200RealReverseAskAmt', 'factor200RealReverseBidAmt',
                      'factorPriceVolumeRatio',
                      'factorPriceRatio', 'factorPredPrice', 'factorLongRetWithHighVol', 'factorRetWithHighVol',
                      'factorPVCorr',
                      'factorScaleVolumePCorr', 'factorDistanceToMidPBand', 'factorDistanceToMidPBandTwoSides',
                      'factorVolumePaceRatio',
                      'factorSupportBreakBand', 'factorTrackVolatility', 'factorWeightedReturns',
                      'factorVolumeOutbreakCurrent',
                      'factorAdjVolumeOutbreak', 'factorAskBidOrderNumberVolatility', 'factorDistanceToVwapVolume',
                      'factorSpeedToVwap',
                      'factorPatternRecogProb', 'factorJumpPointBand', 'factorPositionVolatility', 'factorSR',
                      'factorTickJump',
                      'factorAskBidWeightedPriceDiff', 'factorAskPVolumeMaxChg', 'factorBidPVolumeMaxChg',
                      'factorVolumeToReturnsDoD',
                      'factorVolumeReturnsMap', 'factorAskBidOrderVolumeVolatility', 'factorBidDealMaxRatio',
                      'factorAskDealMaxRatio',
                      'factorAskDealVolumeVolatility', 'factorBidDealDiff', 'factorAskDealDiff',
                      'factorBidWeightedVolumeRatio_20_5',
                      'factorAskWeightedVolumeRatio_20_5', 'factorAskDealPVolumeMaxChg_20',
                      'factorBidDealPVolumeMaxChg_20',
                      'factorAskPVolumeMaxChgUpd_20', 'factorBidPVolumeMaxChgUpd_20', 'factorBidIncremtActiveVolume_10',
                      'factorAskIncremtActiveVolume_10', 'factorAskBidVolumeRatioOtherSides_10',
                      'factorAmtRatioPerPrice60',
                      'factorEntrustRatio200', 'factorHighDistance600', 'factorMidPriceSkew300', 'factorRet20Max120',
                      'factorRet60Max300',
                      'factorRet20MaxMinSum120', 'factorRet60MaxMinSum300', 'factorRiseCo60MulRoc40',
                      'factorRiseCoordination90',
                      'factorSqrtTurnPerPrice60', 'factorRet20Mean200', 'factorRet20SR200', 'factorRet20Std200',
                      'factorRet2Range300',
                      'factorRetMulVol200', 'factorDistance2MA20', 'factorDistance2MAMulRet60',
                      'factorPVPercentile300_10',
                      'factorRetWeightedByVol10_60', 'factorPricePercentileAdjByVol20', 'factorHighRatio',
                      'factorLowRatio', 'factorPricePer5',
                      'factorAvgClose2Vwap200', 'factorVolPer5', 'factorAmtPressure20', 'factorAmtMag200_60',
                      'factorVolStrong60_20',
                      'factorABPriceRatioSR30', 'factorABStrength30_10', 'factorABChangeRatio60',
                      'factorABPriceRatio100', 'factorAskDistance60',
                      'factorBidDistance60', 'factorAskTrend60', 'factorBidTrend30', 'factorABTrendSum40',
                      'factorLongStrength30',
                      'factorShortStrength30', 'factorSellDisSR30', 'factorSellDistanceStd20', 'factorBuyDistanceStd20',
                      'factorAskDistanceMulRet60', 'factorBidDistanceMulRet60', 'factorMACross', 'factorMACrossStd',
                      'factorVWAPCross',
                      'factorOrderBookAskVolumeShift', 'factorOrderBookBidVolumeShift', 'factorPankouBidPressure',
                      'factorPankouPressure',
                      'factorVOI']
        factor_name_list = factor_names

        factorIndex = {}
        for tag, factorList in factor_name_dict.items():
            indexList = []
            for factor in factorList:
                indexList.append(factor_name_list.index(factor))
            factorIndex.update({tag: indexList})

        return factor_names, factorIndex

    def get_missing_code_list(self):
        date_list = self.fa.tradingday(self.test_start_date, self.test_end_date)
        code_list = []
        for date in date_list:
            missing_stock_list = self.get_missing_signal_stock(date)
            print(" Check Date: {}, {} ".format(date, len(missing_stock_list)))
            if len(missing_stock_list) > 0:
                for stock in missing_stock_list:
                    code_list.append((stock, date))
        print(" Total Missing Stock/Date: {} ".format(len(code_list)))
        return code_list

    def get_missing_signal_stock(self, date):
        stock_list = STOCK_LIST
        trade_status = self.fa.get_factor_value("Basic_factor", stock_list, [str(date)], ["trade_status"]).droplevel(0)
        traded_stock_list = trade_status[trade_status["trade_status"].isin(["交易", "N"])].index.tolist()
        valid_stock_list = self.fa.search_by_date(self.signal_library, str(date), traded_stock_list)
        missing_stock_list = list(set(traded_stock_list).difference(valid_stock_list))
        return missing_stock_list


if __name__=="__main__":
    config = InferSignalConfig()
    print(config.factor_name_list)






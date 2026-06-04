import numpy as np
import xgboost as xgb
import pickle
import pandas as pd
import time
import sys
import os
class XgbV1():
    
    def __init__(self,params):

        self._label_name = params['label_name']
        self._random_seed = 1990
        self._modelname =  params['modelname']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']
        self._test_splits = [120,160,200]
    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed

    def get_model(self, sample, factor_list):
        
        dates = sample['date'].unique().tolist()
        n = 5
        import numpy as np
        np.random.seed(self._random_seed)
#         np.random.shuffle(dates)
    
        for j in range(len(self._test_splits)):
            train_dates = dates[:self._test_splits[j]]
            temp_dates = dates[self._test_splits[j]+(n+1):].copy()
            np.random.shuffle(temp_dates)
            validation_dates = temp_dates[:20]
            train_set = sample[sample['date'].isin(train_dates)]  
            train_x = train_set[factor_list]
            train_y = train_set[self._label_name]
            validation_set = sample[sample['date'].isin(validation_dates)] 
            validation_x = validation_set[factor_list]
            validation_y = validation_set[self._label_name ]
            train_dmatrix = xgb.DMatrix(train_x, train_y)
            valid_dmatrix = xgb.DMatrix(validation_x, validation_y)
            params = {'seed':1993,'eta': 0.1,
           'gamma': 1.0,'nthread': 100,
              'subsample':0.8,'colsample_bytree':0.8,'reg_alpha':100,
               'min_child_weight': 0.1, 'max_depth': 8,'tree_method':'gpu_hist'}
            maximize = False
            this_params = {}
            # if model_type == 'rank':
                # this_params = {'objective': 'rank:pairwise','eval_metric':'ndcg@200-'}
                # maximize = True
            # elif model_type =='reg':
                # this_params = {'objective':'reg:linear','eval_metric':'mae'}
            this_params = {'objective':'reg:linear','eval_metric':'mae'}
            params.update(this_params)
            xgb_model = xgb.train(params, train_dmatrix, num_boost_round=1000,maximize=maximize,early_stopping_rounds=100,
                                  evals=[(valid_dmatrix, 'validation')])
   
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'wb') as f:
                pickle.dump(obj =xgb_model,file= f)
            print('scores:', xgb_model.best_score, xgb_model.best_iteration)
        return
        

    def label_predict(self, sample_daily, factor_list):

        res = []            
        for j in range(len(self._test_splits)):
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'rb') as f:
                model = pickle.load(file=f)
            test_x = sample_daily[factor_list]
            test_dmatrix = xgb.DMatrix(test_x)
            y_pred = model.predict(test_dmatrix)
            label_pred = pd.Series(data=y_pred,index=sample_daily['stock'].values)
            res.append(label_pred)
        res = pd.concat(res, axis=1)
        prediction = res.mean(axis =1)                    
        return prediction
def update_model_predict(root_path='',path_sample=[],factor_list=[],
            today_date = '20200407',retrain_flag = True,lookback_period_max = 300,
            model_config_list = [
                    ('XgboostReg_Model','vwap','vwap_re_1d',1,240),
                    ('DeepFM_Model','vwap','vwap_re_1d',1,240),
                    ('Lr_Model','vwap','vwap_re_5d',5,240)
                        ],suffix=None):
    t = time.time()
    
    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir(path_sample)])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period_max-20 : ]
        sample_list = []
        for day in sample_required_dates:
            df = pd.read_pickle(path_sample+ day + '.pkl')
            sample_list.append(df)
        training_sample = pd.concat(sample_list)
        label = pd.read_pickle('/data/user/013546/rubbish/log_return_roll5.pkl')[['date','stock','ret_0930_1129']]
        training_sample = training_sample.merge(label,on=['date','stock'],how='left')
        print('......................')   
    sample_daily = pd.read_pickle(path_sample+today_date+'.pkl')
    for config in model_config_list:
        print(config)
        excess = config[1]
        root_model_path = root_path+'Models/'+excess+'/'
        root_predict_path = root_path+'/DailyPrediction/'+excess+'/'
        if not suffix is None:
            root_model_path += suffix
            root_predict_path += suffix
        params={}
        params['label_name'] = config[2]
        params['weight'] = [-6,-2,0,0,0,10]
        params['time'] = excess
        params['modelname'] = config[0]+'_'+params['label_name']
        params['model_path'] = root_model_path + params['modelname']+'/'
        params['prediction_path'] = root_predict_path + params['modelname']+'/'
        params['sample_path'] = path_sample
        execstr = config[0]+'(params)'
        model = eval(execstr)
        if retrain_flag == True:
            gap_period = config[3]
            model_retrain_date = all_trading_days[-config[4]- gap_period-1 :-gap_period-1]
            retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]
            t = time.time()
            if not os.path.exists(model._model_path):
                os.makedirs(model._model_path)
            model.get_model(retrain_samples.copy(), factor_list)
            print(model._modelname +' re-train finished' , time.time() - t)
        
        pred = model.label_predict(sample_daily, factor_list)
        if not os.path.exists(model._prediction_path):
            os.makedirs(model._prediction_path)
        pred.to_csv(model._prediction_path + today_date +'.csv')
        print(model._modelname +'   predict finished' , today_date, time.time() - t)
        
close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
dates = list(close.index)
dates = [str(i.year)+str(i.month).zfill(2)+str(i.day).zfill(2) for i in dates]
train_start = '20180101'
year = str(2019)
date_start = year+'0101'
year = str(2020)
date_end = year+'1231'
step = 20
count = 0
lookback_period_max = 240
retrain_flag = True  
root_path = '/data/user/013546/AlphaDataCenter/'
suffix = 'test_xgb_ts_select_factor/'+date_start+'_'+date_end
model_config_list= [
            ('XgbV1','vwap','vwap_re_5d',5,240)
             ]
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
factor_list = ['AbsRet2Deal', 'AccountPayableTurn_ttm_qoq', 'AccountPayableTurn_ttm_std_1y', 'AccountPayableTurn_ttm_tsrank12', 
              'AccountPayableTurn_ttm_tsrank4', 'AccountPayableTurn_ttm_tsrank8', 'AccountPayableTurn_ttm_yoy', 'AgainstBeta', 'AmtEhdReverse', 'AmtStdBias', 'AmtVolStdRankMean5d', 'AssetTurn_ttm_qoq', 'AssetTurn_ttm_tsrank12', 'AssetTurn_ttm_tsrank4', 'AssetTurn_ttm_tsrank8', 'AssetTurn_ttm_yoy', 'AtrRetCorr', 'BR20d', 'BollingerDown20d', 'BotTopCumSwingStdRatio', 'CCAREnhancedPVCorr', 'CCAREnhancedPVCorrMean20d', 'CEMVsharpe', 'CEMVstd', 'CSTurnpureCorrRet', 'CSTurnpureCorrRetSharp', 'CdABReversion', 'CdASReversion', 'CloseCorrTurnR2', 'ClosePercentDeal5d_up', 'ClosePercentRank10d_up', 'ClosePercentRank5d', 'ClosePercentSharpe5d', 'CloseVolatility', 'CloseVolatility5d', 'CloseVwapRetKurt', 'CorrCloseTurn10d_max', 'CorrCloseTurn20d_max', 'CorrCloseTurn5d_max', 'CorrCloseVolumeSharpe', 'CorrDownVolumeSharpe', 'CorrVolReturn5d', 'CurDebtToDebt_std_1y', 'CybzCorrClose', 'DealnumSharpe', 'DebtToAsset_qoq', 'DebtToAsset_yoy', 'DedNetProfit_surprise', 'DedProfitToNP_qfa_surprise', 'DedProfitToNP_qfa_tsrank4', 'DedProfitToNP_ttm_qoq', 'DedProfitToNP_ttm_tsrank12', 'DedProfitToNP_ttm_tsrank4', 'DedProfitToNP_ttm_tsrank8', 'DeltaTurnSkew', 'DownUpMeanRatio5d', 'DownUpSumRatio5d', 'DownVolRatioDiff30', 'DuoKongMix', 'DuoKongPV', 'EBITDev', 'EP_Hist2_120D', 'EP_tsrank12', 'EP_tsrank4', 'EP_tsrank8', 'ExcessRetVolatility', 'FCFFP_tsrank12', 'FCFFP_tsrank4', 'FCFFP_tsrank8', 'FCFF_surprise', 'FR10d_1001', 'FR10d_1130', 'FR20d_1001', 'FR20d_1130', 'FR40d', 'FR40d_1001', 'FR40d_1130', 'FallTurnover', 'GTJA_005', 'GTJA_007', 'GTJA_016', 'GTJA_026', 'GTJA_032', 'GTJA_035', 'GTJA_042', 'GTJA_061', 'GTJA_064', 'GTJA_073', 'GTJA_087', 'GTJA_090', 'GTJA_099', 'GTJA_105', 'GTJA_121', 'GrahamGrowth', 'GrahamValue', 'GrossProfitMargin_qfa_surprise', 'GrossProfitMargin_qfa_tsrank12', 'GrossProfitMargin_qfa_tsrank4', 'GrossProfitMargin_qfa_tsrank8', 'GrossProfitMargin_ttm_qoq', 'GrossProfitMargin_ttm_tsrank12', 'GrossProfitMargin_ttm_tsrank4', 'GrossProfitMargin_ttm_tsrank8', 'GrossProfitMargin_ttm_yoy', 'GrowthRefined', 'HS300CorrClose', 'HighLowStdRatio5d', 'HighLowStdRatio_mean20d', 'HighLowSwingRatio', 'HighTurnCorr', 'HighVolCorrStd', 'HighVolumeCorr10d', 'IdeaReverser5d', 'IlliqMean2TurnoverStd', 'IlliqNeg20d', 'IlliqNeg60d', 'IlliqSwing', 'IndustryNeutralizedTurnoverStd', 'InventoryTurn_ttm_qoq', 'InventoryTurn_ttm_tsrank12', 'InventoryTurn_ttm_tsrank4', 'InventoryTurn_ttm_tsrank8', 'LargeSmallVolumeVWAPRatio', 'Last30MinRetDownVol5d', 'Last30MinUpDownMoneyRatio5d', 'Last30MinsVwapCloseRatio5d', 'Last30MinutesLongShortRatio1d', 'LiqCorr', 'LiqRatioAS', 'LowCandleBottom', 'LowSharpeAmountStdRatio', 'MPV_EWMA', 'MPV_EWMAHHI', 'MPV_EWMASTD', 'MeanTurn2RetDown5d', 'MidPVolCorr20', 'Min10VolBurst5Wegihted5d', 'Min10mRetUpVar', 'Min15DPVcorr', 'Min15mPriceMax', 'Min15mPricePath', 'Min30CEMVbias', 'Min30CEMVsharpe', 'Min30RSRS', 'Min30WeightVolAmpCloseRatio', 'Min5LastHalfHourRVI', 'Min5LastHalfHourVR', 'Min5LastHalfHourVR5dCut', 'Min5LastHalfHourVRSI10d', 'Min5LastHourElder20d', 'Min5LastHourVwapCorrVolume10dSharp', 'Min5LongShortRatioCut5d', 'Min5VwapToClose20d', 'Min5mAmtRatio', 'Min5mTopVolRet', 'Min60UpDownRatio', 'Min60_RVstd', 'MinAbnCorr', 'MinAmtMidChg', 'MinAmtMidSkew', 'MinAmtMidStd', 'MinCEMVskew', 'MinCloseCallAmt30maCorr', 'MinCloseCallAmtBias5d', 'MinCloseCallAmtHHI5d', 'MinCloseCallAmtRatio', 'MinCloseVolume', 'MinCloseVolumeRank', 'MinCorHighVolumeMax10d', 'MinCorrRank', 'MinCorrRankMean', 'MinCorrVolumePrice10d', 'MinCorrVolumePrice20d', 'MinCorrVolumeRetUp10d', 'MinCorrVolumeRetUp5d', 'MinDirectedVol', 'MinEMVA', 'MinEMVAsharpe', 'MinEMVAstd', 'MinExcessSharpe', 'MinExcessSharpe5d', 'MinHighVolSwing', 'MinHighVolumeRankCorr20d', 'MinIdx500Corr', 'MinIndexCorr', 'MinMaxDrawDownUp', 'MinNoiseReverse', 'MinPMAmpVolume5d', 'MinPMSignAmplitude5d', 'MinPmRSRS5d', 'MinRRC', 'MinRST', 'MinRSTstd', 'MinRetRange', 'MinReturnVolUp2Down5d', 'MinSignedAmtMaxDrawdown', 'MinSignedAmtPriceDelayDeltaCorr', 'MinSkew20d', 'MinSkewSharpe10d', 'MinSkewStd20d', 'MinSmartFoolRatio', 'MinSmartFoolRatioMean', 'MinTMcorr', 'MinTVolStd', 'MinTWAPExcessSharpe10d', 'MinTWAPReSharpe5d', 'MinTopRetUpVar', 'MinTopVolCorr5D', 'MinTopVolRate', 'MinUpBackSharpe', 'MinUpBackStd', 'MinUpDownMean2Vol5d', 'MinUpDownRatio', 'MinUpVoteRatio', 'MinVRCExcess5d', 'MinVVCorrRank', 'MinVVCorrRankStd', 'MinVVRankCorrStd', 'MinVVRtoCorrRank', 'MinVVRtoCorrRankMean', 'MinVolWeightedRet5d', 'MinVolumeVolUp2Down5d', 'MinVwapRV', 'MinVwapRV5', 'MinVwapRV5skew', 'MinVwapRVskew', 'MinWeightVolReRatio', 'MinWeightVolReSkew', 'MinWeightVolReSwing', 'Min_ACD', 'Min_ACDSharp', 'Min_ACDZScore', 'Min_AR', 'Min_CloseBuySellStrength', 'Min_DownReturn', 'Min_IlliqCloseReturn', 'Min_IlliqShortcut', 'Min_OverBuy', 'Min_OverBuyVol', 'Min_PredictReturn2Volume', 'Min_PredictReturnMean', 'Min_PredictReturnSharp', 'Min_PredictReturnZScore', 'Min_RSRS', 'Min_RelativeDownReturn', 'Min_TurnoverSharp', 'Min_TurnoverStd', 'Min_UpRange', 'Minute30m5dTurnStd', 'Minute30m5dVolumeHHI', 'Minute5dAmtSimilarityRet', 'Minute60minBias5d', 'MinuteALTKurt', 'MinuteAbnormalRe5d', 'MinuteAbnormalRe5m', 'MinuteAfterRAVwapReturn5d', 'MinuteAmtAutocorr5d', 'MinuteAmtCV3d', 'MinuteAmtCV5d', 'MinuteAmtRetCor5d', 'MinuteAmtStdSwing', 'MinuteCloseAmtReMean', 'MinuteCloseAmtReVote', 'MinuteCloseCallAuctionTurnover', 'MinuteCloseMMT', 'MinuteCloseMomentumBias', 'MinuteCloseMomentumSharpe', 'MinuteCloseResist', 'MinuteCloseSmartGame', 'MinuteCloseTurn', 'MinuteCloseTurnCorr', 'MinuteCloseTurnPlus', 'MinuteCloseTurnRank', 'MinuteCloseTurnRev', 'MinuteCloseTurnSharp', 'MinuteCloseTurnoverStd', 'MinuteCloseUpVar', 'MinuteClosingSessionVolumePercent', 'MinuteCorrPriceNotional', 'MinuteCorrPriceNotionalSharpe', 'MinuteCorrPriceVolumeSharpe', 'MinuteCorrRank', 'MinuteCorrVWAPVolume', 'MinuteCorrVolVwap', 'MinuteDCDTA', 'MinuteDCDTA5d', 'MinuteDownVolatilityRatio20d', 'MinuteEODRetDrawdownRatioSharpe', 'MinuteEODSkewness120Min', 'MinuteEODSortinoRatioSharpe', 'MinuteEODVolWeightedLongShortPower', 'MinuteEODVolWeightedLongShortPowerSharpe', 'MinuteEODVolumeRatio', 'MinuteEODVolumeWeightedReturn', 'MinuteEODVolumeWeightedReturnEWM', 'MinuteEODVolumeWeightedReturnSharpe', 'MinuteGroupReBias5d', 'MinuteHTRtnRvs', 'MinuteIdioKurt5d', 'MinuteIdioSkew5d', 'MinuteIlliqLast30m5D', 'MinuteIlliqVwapClose5d', 'MinuteLHourSkew', 'MinuteLast1hrSkewSharpe', 'MinuteLast1hrSkewSharpeBias', 'MinuteLast30mPriceVolRefine', 'MinuteLast30mPriceVolRefineMean', 'MinuteLast3hrsSkewSharpe', 'MinuteLast60mLongVolRatio', 'MinuteLastHourMDDMCLIMB20d', 'MinuteLastHourMDDMCLIMBstd20d', 'MinuteLastHourMaxClimb20dSR', 'MinuteLastHourPVCorr', 'MinuteLastHourSkewness5d', 'MinuteLastHrCorrPriceNotional', 'MinuteLastMtmRankVote5d', 'MinuteLastPSY', 'MinuteLastReStd1D', 'MinuteLastTurn20std', 'MinuteLastVolumeRank5std', 'MinuteMADistanceMA', 'MinuteMPVCorrRank', 'MinuteMacdEma10d', 'MinuteMaxTenMinReturn', 'MinuteMaxTenMinReturnSharpe', 'MinuteMovingAverageDiffMax', 'MinuteMovingAverageDiffMaxEWM', 'MinutePVCorr', 'MinutePVCorrMean', 'MinutePVCorrMin', 'MinutePVCorrMinAdj', 'MinutePVCorrStdAdj', 'MinutePmSkew', 'MinutePmSkewEma10d', 'MinutePmSkewSharpe', 'MinutePosNegVolumeRatio', 'MinutePriceStd10d', 'MinuteRAVolumeRatio5d', 'MinuteRSRSResidVolatilityZscore5d', 'MinuteRSRSstd5d', 'MinuteRTC', 'MinuteRePerDeal5d', 'MinuteRelativeUpVar', 'MinuteRetLastHrSkew', 'MinuteRetSkewnessSharpe', 'MinuteRetTurnRho', 'MinuteRetVolMultSharpe', 'MinuteRetVolMultSkew', 'MinuteRetVolMultSkewSharpe', 'MinuteRetVolProdSkew', 'MinuteRetVolProdSkewSharpe', 'MinuteReturnAutocorr5d', 'MinuteReturnDiffStdSharpe', 'MinuteReturnSkew', 'MinuteReturnSkewSharpe', 'MinuteReturnSkewnessSharpe', 'MinuteReturnStdSharpe', 'MinuteReturnVolSharpe', 'MinuteReturnVolumeMultipleSharpe', 'MinuteSignedAvgDistanceDiff', 'MinuteSignedAvgDistanceDiffMean', 'MinuteSortinoSharpe', 'MinuteTAVwapReturn5d', 'MinuteTERtnVRatio', 'MinuteTHLCorrRank', 'MinuteTLSTRvs', 'MinuteTLSVRatio', 'MinuteTLTurn', 'MinuteTPVDeltaCorr', 'MinuteTRC', 'MinuteTRtnVGRank', 'MinuteTRtnVGStdRank', 'MinuteTRtnVRatioRank', 'MinuteTSD', 'MinuteTTLSStdRank', 'MinuteTTPVCorr', 'MinuteTVRtnRank', 'MinuteTWR', 'MinuteTrendStr', 'MinuteTrendStrSharp', 'MinuteTurnoverStdSharpe', 'MinuteTurnoverVolSharpe', 'MinuteUpVar', 'MinuteVARe5d', 'MinuteVAVwapReturnSR5d', 'MinuteVMASkew', 'MinuteVVCorrHalfRatio', 'MinuteValidRet', 'MinuteVarianceRatio', 'MinuteVirtualHighLowPathSR5d', 'MinuteVirtualHighLowStdDif5d', 'MinuteVirtualHighLowStdSR5d', 'MinuteVirtualLineUpdownAmt5d', 'MinuteVol', 'MinuteVolCV60m5D', 'MinuteVolCVSharpe10d', 'MinuteVolCVSkew10d', 'MinuteVolVwapCorrCloseChg', 'MinuteVolWeightedPowerEWM', 'MinuteVolofVolumeHHI', 'MinuteVolumeHHI', 'MinuteVolumeHHISharpe', 'MinuteVolumeKurt', 'MinuteVolumeMACD', 'MinuteVolumeRatioBias', 'MinuteVolumeSkew', 'MinuteVolumeStabilitySharpe', 'MinuteVolumeStd20dCV', 'MinuteVolumeStdSharpe', 'MinuteWRMean', 'MinuteWRVolume', 'MinuteliqAmtRatioSharpe20d', 'MinuteliqSwingSharpe5d', 'MinuteliqSwingStd5', 'MomHigh2Low10d', 'MomHigh2Low20d', 'MomHighExclMorn20d', 'MomHighPm5d', 'NCFP_tsrank12', 'NCFP_tsrank8', 'NIGrowthZscore1y', 'NI_SQ_IndustryRank', 'NegativeIlliquidity', 'NetCash_surprise', 'NetProfitMargin_qfa_surprise', 'NetProfitMargin_qfa_tsrank12', 'NetProfitMargin_qfa_tsrank4', 'NetProfitMargin_qfa_tsrank8', 'NetProfitMargin_ttm_qoq', 'NetProfitMargin_ttm_tsrank12', 'NetProfitMargin_ttm_tsrank4', 'NetProfitMargin_ttm_tsrank8', 'NetProfitMargin_ttm_yoy', 'NetProfitSurprise', 'NetProfit_surprise', 'NonstationaryPV', 'NonstationaryPVSharp', 'OCFP_tsrank12', 'OCFP_tsrank4', 'OCFP_tsrank8', 'OCFToSales_ttm_tsrank12', 'OCFToSales_ttm_tsrank4', 'OCFToSales_ttm_tsrank8', 'OpenGapVolSharp10d', 'OprCost_surprise', 'OprProfitToNP_qfa_surprise', 'OprProfitToNP_qfa_tsrank12', 'OprProfitToNP_ttm_qoq', 'OprProfitToNP_ttm_tsrank12', 'OprProfitToNP_ttm_tsrank4', 'OprProfitToNP_ttm_tsrank8', 'OprProfitToNP_ttm_yoy', 'OprProfit_surprise', 'PEAdj', 'PVTTurn20d', 'PVTTurn5d', 'PePercent240d', 'PmVolumeRatio', 'PriceDiff', 'ROA_qfa_surprise', 'ROA_qfa_tsrank12', 'ROA_qfa_tsrank4', 'ROA_qfa_tsrank8', 'ROA_ttm_qoq', 'ROA_ttm_tsrank12', 'ROA_ttm_tsrank4', 'ROA_ttm_tsrank8', 'ROA_ttm_yoy', 'ROE_SQ', 'ROE_qfa_surprise', 'ROE_qfa_tsrank12', 'ROE_qfa_tsrank4', 'ROE_qfa_tsrank8', 'ROE_ttm_qoq', 'ROE_ttm_tsrank12', 'ROE_ttm_tsrank4', 'ROE_ttm_tsrank8', 'ROE_ttm_yoy', 'RSI', 'RangeRetCorr20', 'RankNetProfitDps', 'RankPBDev', 'RankPBRel', 'RankPEChange', 'RankPEDev', 'RankPERel', 'ReCorr20', 'RelativeIndPE40d', 'RelativeIndPEAS', 'RelativeIndPEGAvg', 'RetCorrTurnDelay', 'RetCorrTurnDelayPure', 'RetCutCorrTurnDelay', 'RetVolumeRetMultSharpe', 'ReturnSkewEMA20d', 'ReverseMomentum', 'ReverseMomentumDouble', 'ReverseMomentumTriple', 'SPPI', 'SP_tsrank4', 'SP_tsrank8', 'Sales_surprise', 'SectorIlliquidity', 'SectorNotionalSharpe', 'SectorOverperformanceVol', 'SectorPESharpe', 'SectorSize', 'SectorSkewness', 'ShortBear', 'SimpleVolume', 'StdMaxAmountRatio', 'SwingHighLowPriceCorr', 'SwingToTurn', 'TopAmountRatioVolumeDiffSharpe', 'TurnAmtCorr20d', 'TurnCorrSharp', 'TurnMidCorr', 'TurnNeuIndusRank', 'TurnNeuRetCorrSharp', 'TurnPE', 'TurnPEAS', 'TurnPEAvg', 'TurnPEStd', 'TurnPercent_1d_240d', 'TurnRankPercent_1d_240d', 'TurnoverMean2Std', 'TurnoverSharpe', 'TurnoverSharpe100d', 'TurnoverStdRatio', 'Twap2Vwap', 'UpVolRatioDiff30', 'ValueDelay', 'ValueGrowth', 'ValueRefined', 'VolPriceCorr', 'VolPriceFlyer', 'VolPriceFlyerPlus', 'VolPriceRunner', 'VolitilityMax', 'VolitilityRelative', 'VolumeRatioDown20d', 'VolumeShortLongStdRatio', 'VolumeStdBias', 'VoteDiff30', 'VwapCloseAdj20d', 'VwapTurnStdRatio', 'Vwap_Close_Range_Diff', 'WAPResistBackRatio', 'WAPResistBackStd', 'WAPResistBackTop', 'WQ_026', 'WQ_042', 'WeightedDownUpSumRatio5d', 'ZZ500CorrClose', 'ZaoYinTrader']
print('factor list num:',len(factor_list))
path_sample = '/data/group/800020/AlphaDataCenter/Sample/NormSample/'#
dates = [i for i in dates if i>=date_start and i<=date_end]
for today_date in dates:
    if count % step == 0:
        retrain_flag = True
    else: 
        retrain_flag = False          
    print('###########%s %s############' % (today_date,str(retrain_flag)))
    count+=1                            
    update_model_predict(root_path=root_path,path_sample=path_sample,factor_list=factor_list,
                today_date = today_date,retrain_flag = retrain_flag,
                lookback_period_max = lookback_period_max,
                model_config_list = model_config_list,suffix=suffix)
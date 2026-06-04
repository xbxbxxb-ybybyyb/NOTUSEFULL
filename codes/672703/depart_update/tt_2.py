import numpy as np
import xgboost as xgb
import pickle
import pandas as pd
import xgboost as xgb
from lightgbm import LGBMRegressor ,LGBMRanker   
import lightgbm as lgb
from sklearn.model_selection import train_test_split
class LgbReg():
    
    def __init__(self,params):

        self._label_name = params['label_name']
        self._random_seed = 1990
        self._modelname =  params['modelname']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']

    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed
    def learning_rate(self,n):
        if n > 6000:
            return 0.01 * np.exp(-(n-6000)/600) + 0.001
        elif n > 4000:
            return 0.02 * np.exp(-(n-4000)/600) + 0.001
        elif n > 2000:
            return 0.05 * np.exp(-(n-2000)/600) + 0.001
        else:
            return 0.1 * np.exp(-n/600) + 0.001
    def get_model(self, sample, factor_list):
        # sample['rank'] = sample.groupby(by='date')[self._label_name].rank(pct=True)
        # sample = sample[(sample['rank']-0.5).abs()>0.2]
        # sample = sample[sample[self._label_name]!=0]
        # df = sample[self._label_name].rank(pct=True)
        # df[df==1] = 1 -1/3676
        # df[df==0] = 1/3676
        # sample[self._label_name] = norm.ppf(df.values)
        dates = sample['date'].unique().tolist()
        import numpy as np
        np.random.seed(self._random_seed)
        np.random.shuffle(dates)
        for j in range(3):
            this_sample = sample[sample['date'].isin(dates[j*80:(j+1)*80])]
            train_x, validation_x, train_y, validation_y = train_test_split(this_sample[factor_list], this_sample[self._label_name], 
                test_size = 0.1, random_state = self._random_seed)
            model = LGBMRegressor(n_jobs=24, num_leaves=64, max_depth=6, learning_rate=0.1, 
                 n_estimators=2000, silent=False,
                 reg_lambda=1000,random_state=1605, first_metric_only=True,
                 feature_fraction=0.8, feature_fraction_seed=1504, bagging_fraction=0.8, bagging_fraction_seed=1504)
            model.fit(train_x, train_y, callbacks=[lgb.reset_parameter(learning_rate=lambda n: 0.1 * np.exp(-n/600) + 0.001)],    
                      eval_set=[(validation_x, validation_y)],early_stopping_rounds=40)
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'wb') as f:
                pickle.dump(obj = model,file= f)
            print('scores:', model.best_score_, model.best_iteration_)
        return
        

    def label_predict(self, sample_daily, factor_list):
        res = []            
        for j in range(3):
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'rb') as f:
                model = pickle.load(file=f)
            test_x = sample_daily[factor_list]
            y_pred = model.predict(test_x,num_iteration=model.best_iteration_)
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
    path_feature = path_sample
    label = pd.read_pickle('/data/user/013546/rubbish/map_act_label.pkl')
    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir(path_feature)])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period_max-20 : ]
        sample_feature = []
        sample_label = []
        for day in sample_required_dates:
            df = pd.read_pickle(path_feature+ day + '.pkl')
            sample_feature.append(df)
         
        training_sample = pd.concat(sample_feature)
        training_sample = training_sample[['date','stock']+factor_list].merge(label,on=['date','stock'],how='left')
        print('......................')   
    sample_daily = pd.read_pickle(path_feature+today_date+'.pkl')
  
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

import time
import os
close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
dates = list(close.index)
dates = [str(i.year)+str(i.month).zfill(2)+str(i.day).zfill(2) for i in dates]
train_start = '20180101'
date_start = '20200220'
date_end = '20200331'
step = 20
count = 0
lookback_period_max = 240
retrain_flag = True  
root_path = '/data/user/013546/AlphaDataCenter/'
suffix = 'norm0_'+date_start+'_'+date_end+'/'
model_config_list= [
            ('LgbReg','am','0930_1129_re_5d',5,240)
             ]
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
# factor_list = ['AbsRet2Deal', 'AccountPayableTurn_ttm_std_1y', 'AccountPayableTurn_ttm_tsrank12', 'AccountPayableTurn_ttm_tsrank4', 'AccountPayableTurn_ttm_tsrank8', 'AgainstBeta', 'AmtEhdReverse', 'AmtStdBias', 'AmtVolStdRankMean5d', 'Argmin5d', 'AroonDown5d', 'AssetTurn_ttm_qoq', 'AssetTurn_ttm_tsrank12', 'AssetTurn_ttm_tsrank4', 'AssetTurn_ttm_tsrank8', 'AtrRetCorr', 'BP_tsrank12', 'BP_tsrank4', 'BR20d', 'BollingerDown20d', 'BotTopCumSwingStdRatio', 'CCAREnhancedPVCorr', 'CCAREnhancedPVCorrMean20d', 'CEMVsharpe', 'CEMVstd', 'CSTurnpureCorrRet', 'CSTurnpureCorrRetSharp', 'CdABReversion', 'CdASReversion', 'CloseCorrTurnR2', 'ClosePercent2Journey', 'ClosePercentDeal5d_up', 'ClosePercentHighLow', 'ClosePercentIndus', 'ClosePercentLast60', 'ClosePercentRank10d_up', 'ClosePercentRank5d', 'ClosePercentUp5d', 'CloseVolatility', 'CloseVolatility5d', 'CloseVwapRetKurt', 'CloseVwapRetSkew', 'CorrCloseTurn10d_max', 'CorrCloseTurn20d_max', 'CorrCloseTurn5d_max', 'CorrCloseVolumeSharpe', 'CorrDownVolumeSharpe', 'CorrVolReturn5d', 'CurDebtToDebt_tsrank12', 'CurDebtToDebt_tsrank8', 'CybzCorrClose', 'DealnumSharpe', 'DebtToAsset_tsrank12', 'DedNetProfit_surprise', 'DedProfitToNP_qfa_surprise', 'DedProfitToNP_qfa_tsrank12', 'DedProfitToNP_qfa_tsrank4', 'DedProfitToNP_qfa_tsrank8', 'DedProfitToNP_ttm_qoq', 'DedProfitToNP_ttm_tsrank12', 'DedProfitToNP_ttm_tsrank4', 'DedProfitToNP_ttm_tsrank8', 'DedProfitToNP_ttm_yoy', 'DeltaTo5DMin', 'DeltaTurnSkew', 'DownSpace', 'DownUpMeanRatio5d', 'DownUpSumRatio5d', 'DownVolRatioDiff30', 'DuoKongMix', 'DuoKongPV', 'DuoKongVar', 'DuoKongVolumeVar', 'EBITDev', 'EP_Hist1_5D', 'EP_Hist2_120D', 'EP_tsrank12', 'EP_tsrank4', 'EP_tsrank8', 'EbitTTM', 'EbitdaTTM', 'ExcessRetVolatility', 'FCFFP_tsrank12', 'FCFFP_tsrank4', 'FCFFP_tsrank8', 'FCFF_surprise', 'FR10d_1001', 'FR10d_1130', 'FR20d_1001', 'FR20d_1130', 'FR40d', 'FR40d_1001', 'FR40d_1130', 'FallTurnover', 'GTJA_004', 'GTJA_005', 'GTJA_006', 'GTJA_007', 'GTJA_016', 'GTJA_017', 'GTJA_026', 'GTJA_032', 'GTJA_034', 'GTJA_035', 'GTJA_039', 'GTJA_042', 'GTJA_048', 'GTJA_061', 'GTJA_064', 'GTJA_065', 'GTJA_073', 'GTJA_090', 'GTJA_098', 'GTJA_099', 'GTJA_105', 'GTJA_121', 'GrahamGrowth', 'GrahamValue', 'GrossProfitMargin_qfa_surprise', 'GrossProfitMargin_qfa_tsrank12', 'GrossProfitMargin_qfa_tsrank4', 'GrossProfitMargin_qfa_tsrank8', 'GrossProfitMargin_ttm_qoq', 'GrossProfitMargin_ttm_tsrank12', 'GrossProfitMargin_ttm_tsrank4', 'GrossProfitMargin_ttm_tsrank8', 'GrowthRefined', 'HS300CorrClose', 'HighLowStdRatio5d', 'HighLowStdRatio_mean20d', 'HighLowSwingRatio', 'HighLowVwapRatio5d', 'HighTurnCorr', 'HighVolCorrStd', 'HighVolumeCorr10d', 'IdeaReverser5d', 'IlliqMean2TurnoverStd', 'IlliqNeg20d', 'IlliqNeg60d', 'IlliqSwing', 'IndustryNeutralizedTurnoverStd', 'InventoryTurn_ttm_qoq', 'InventoryTurn_ttm_tsrank12', 'InventoryTurn_ttm_tsrank4', 'InventoryTurn_ttm_tsrank8', 'LargeSmallVolumeVWAPRatio', 'Last15MinTrendStrength5d', 'Last30MinRetDownVol5d', 'Last30MinUpDownMoneyRatio5d', 'Last30MinsVwapCloseRatio5d', 'Last30MinutesLongShortRatio1d', 'LiqCorr', 'LiqRatioAS', 'LongShortPower', 'LowCandleBottom', 'LowSharpeAmountStdRatio', 'LowWire', 'MPV_EWMA', 'MPV_EWMAHHI', 'MPV_EWMASTD', 'Max2Min5d', 'MeanTurn2RetDown5d', 'MidPVolCorr20', 'Min10VolBurst5Wegihted5d', 'Min10mRetUpVar', 'Min15DPVbias', 'Min15DPVcorr', 'Min15mPriceMax', 'Min15mPricePath', 'Min30CEMVbias', 'Min30CEMVsharpe', 'Min30RSRS', 'Min30WeightVolAmpCloseRatio', 'Min30_PRchange_5d', 'Min5LastHalfHourRVI', 'Min5LastHalfHourVR', 'Min5LastHalfHourVR5dCut', 'Min5LastHalfHourVRSI10d', 'Min5LastHalfHourVolStd5d', 'Min5LastHourElder20d', 'Min5LastHourElder5dSharp', 'Min5LastHourMFI5d', 'Min5LastHourVwapCorrVolume10dSharp', 'Min5LongShortRatioCut5d', 'Min5VwapToClose20d', 'Min5mAmtRatio', 'Min5mTopVolRet', 'Min60RSRS', 'Min60UpDownRatio', 'Min60_RVstd', 'MinAbnCorr', 'MinAmtMidChg', 'MinAmtMidSkew', 'MinAmtMidStd', 'MinCEMVskew', 'MinCloseCallAmt30maCorr', 'MinCloseCallAmt5maCorrSharpe', 'MinCloseCallAmtBias5d', 'MinCloseCallAmtHHI5d', 'MinCloseCallAmtRatio', 'MinCloseVolume', 'MinCloseVolumeRank', 'MinCorHighVolumeMax10d', 'MinCorrRank', 'MinCorrRankMean', 'MinCorrVolumePrice', 'MinCorrVolumePrice10d', 'MinCorrVolumePrice20d', 'MinCorrVolumeRetUp10d', 'MinCorrVolumeRetUp5d', 'MinDirectedVol', 'MinDownPVCorr', 'MinEMVA', 'MinEMVAsharpe', 'MinEMVAstd', 'MinExcessIndusPercent', 'MinExcessSharpe', 'MinExcessSharpe5d', 'MinHighCorrVolume3d', 'MinHighVolSwing', 'MinHighVolumeRankCorr20d', 'MinIdx300Corr', 'MinIdx500Corr', 'MinIndexCorr', 'MinLowToHighUpPower', 'MinMaxDrawDownUp', 'MinNoiseReverse', 'MinPMAmpVolume5d', 'MinPMSignAmplitude5d', 'MinPmRSRS', 'MinPmRSRS5d', 'MinRRC', 'MinRST', 'MinRSTstd', 'MinReboundRate5d', 'MinRetRange', 'MinReturnVolUp2Down5d', 'MinSignedAmtMaxDrawdown', 'MinSignedAmtPriceDelayDeltaCorr', 'MinSignedAmtPriceDelayDeltaCorrMean', 'MinSkew20d', 'MinSkewSharpe10d', 'MinSkewStd20d', 'MinSkipCorrRatio', 'MinSmartFoolRatio', 'MinSmartFoolRatioMean', 'MinTMcorr', 'MinTVolStd', 'MinTWAPExcessSharpe10d', 'MinTopRetUpVar', 'MinTopVolCorr5D', 'MinTopVolRate', 'MinUpBackSharpe', 'MinUpBackStd', 'MinUpDownMean2Vol5d', 'MinUpDownRatio', 'MinUpVoteRatio', 'MinVRCExcess5d', 'MinVVCorrRank', 'MinVVCorrRankStd', 'MinVVRankCorrStd', 'MinVVRtoCorrRank', 'MinVVRtoCorrRankMean', 'MinVolAmpCorrRatio', 'MinVolWeightedRet5d', 'MinVolumeVolUp2Down5d', 'MinVwapRV', 'MinVwapRV5', 'MinVwapRV5skew', 'MinVwapRVskew', 'MinWeightVolReRatio', 'MinWeightVolReSkew', 'MinWeightVolReSwing', 'Min_ACD', 'Min_ACDBias', 'Min_ACDSharp', 'Min_ACDZScore', 'Min_AR', 'Min_CloseAutoCorrZScore', 'Min_CloseBias', 'Min_CloseBuySellStrength', 'Min_CloseBuySellStrengthZScore', 'Min_CorrReturnVolume', 'Min_DownReturn', 'Min_IlliqCloseReturn', 'Min_IlliqShortcut', 'Min_OverBuy', 'Min_OverBuyVol', 'Min_PredictReturn2Volume', 'Min_PredictReturnMean', 'Min_PredictReturnSharp', 'Min_PredictReturnZScore', 'Min_RSRS', 'Min_RelativeDownReturn', 'Min_TurnoverSharp', 'Min_TurnoverStd', 'Min_UpRange', 'Minute30m5dTurnStd', 'Minute30m5dVolumeHHI', 'Minute5dAmtSimilarityRet', 'Minute60minBias5d', 'MinuteALTKurt', 'MinuteAbnormalRe5d', 'MinuteAbnormalRe5m', 'MinuteAfterRAVwapReturn5d', 'MinuteAmtAutocorr5d', 'MinuteAmtCV3d', 'MinuteAmtCV5d', 'MinuteAmtRetCor1d', 'MinuteAmtRetCor5d', 'MinuteAmtStdSwing', 'MinuteAroon', 'MinuteBias30m5D', 'MinuteCloseAmtReHHI', 'MinuteCloseAmtReMean', 'MinuteCloseAmtReVote', 'MinuteCloseCallAuctionTurnover', 'MinuteCloseDiff', 'MinuteCloseMMT', 'MinuteCloseMomentumBias', 'MinuteCloseMomentumSharpe', 'MinuteCloseOpenEWMA', 'MinuteClosePriceXCorr', 'MinuteCloseResist', 'MinuteCloseSmartGame', 'MinuteCloseTurn', 'MinuteCloseTurnCorr', 'MinuteCloseTurnPlus', 'MinuteCloseTurnRank', 'MinuteCloseTurnRev', 'MinuteCloseTurnSharp', 'MinuteCloseTurnoverStd', 'MinuteCloseUpVar', 'MinuteCloseVol30mChg', 'MinuteCloseWR', 'MinuteCloseWREWMA', 'MinuteCloseWRVolume', 'MinuteClosingSREWM', 'MinuteClosingSessionVolumePercent', 'MinuteCorrCloseVolume', 'MinuteCorrPriceNotional', 'MinuteCorrPriceNotionalSharpe', 'MinuteCorrPriceVolumeSharpe', 'MinuteCorrRank', 'MinuteCorrVWAPVolume', 'MinuteCorrVolVwap', 'MinuteDCDTA', 'MinuteDCDTA5d', 'MinuteDownVolatilityRatio20d', 'MinuteEODRetDrawdownRatio', 'MinuteEODRetDrawdownRatioSharpe', 'MinuteEODRetVolMultiple', 'MinuteEODReturn', 'MinuteEODSharpe', 'MinuteEODSkewness120Min', 'MinuteEODSortinoRatio', 'MinuteEODSortinoRatioSharpe', 'MinuteEODVolWeightedLongShortPower', 'MinuteEODVolWeightedLongShortPowerSharpe', 'MinuteEODVolumeRatio', 'MinuteEODVolumeWeightedReturn', 'MinuteEODVolumeWeightedReturnEWM', 'MinuteEODVolumeWeightedReturnSharpe', 'MinuteGroupReBias5d', 'MinuteHTRtnRvs', 'MinuteIdioKurt5d', 'MinuteIdioSkew5d', 'MinuteIlliqLast30m5D', 'MinuteIlliqVwapClose5d', 'MinuteLHourSkew', 'MinuteLTSkew', 'MinuteLast1hrSkewSharpe', 'MinuteLast1hrSkewSharpeBias', 'MinuteLast30mPriceVolRefine', 'MinuteLast30mPriceVolRefineHHI', 'MinuteLast30mPriceVolRefineMean', 'MinuteLast3hrsSkewSharpe', 'MinuteLast60mLongVolRatio', 'MinuteLastHourMDDMCLIMB20d', 'MinuteLastHourMDDMCLIMBstd20d', 'MinuteLastHourMaxClimb20dSR', 'MinuteLastHourPVCorr', 'MinuteLastHourSkewness5d', 'MinuteLastHrCorrPriceNotional', 'MinuteLastMtmRank5d', 'MinuteLastMtmRankVote5d', 'MinuteLastPSY', 'MinuteLastReStd1D', 'MinuteLastSR5HHI', 'MinuteLastSR5d', 'MinuteLastTurn20std', 'MinuteLastVolumeRank5std', 'MinuteMADistance', 'MinuteMADistanceMA', 'MinuteMADistanceSP', 'MinuteMPVCorrRank', 'MinuteMacdEma10d', 'MinuteMaxDistanceRetMA', 'MinuteMaxTenMinReturn', 'MinuteMaxTenMinReturnSharpe', 'MinuteMovingAverageDiffMax', 'MinuteMovingAverageDiffMaxEWM', 'MinutePMRtnZscore10d', 'MinutePVCorr', 'MinutePVCorrMean', 'MinutePVCorrMin', 'MinutePVCorrMinAdj', 'MinutePVCorrStdAdj', 'MinutePmSkew', 'MinutePmSkewEma10d', 'MinutePmSkewSharpe', 'MinutePmTrendStr', 'MinutePosNegVolumeRatio', 'MinutePriceMACD', 'MinutePriceStd10d', 'MinuteRAVolumeRatio5d', 'MinuteRSIVolume', 'MinuteRSRSResidVolatilityZscore5d', 'MinuteRSRSstd5d', 'MinuteRTC', 'MinuteRePerDeal5d', 'MinuteRelativeUpVar', 'MinuteRetLastHrSkew', 'MinuteRetSkewnessSharpe', 'MinuteRetTurnCorr', 'MinuteRetTurnRho', 'MinuteRetVolMultMean', 'MinuteRetVolMultSharpe', 'MinuteRetVolMultSkew', 'MinuteRetVolMultSkewSharpe', 'MinuteRetVolProdSkew', 'MinuteRetVolProdSkewSharpe', 'MinuteReturnAutocorr5d', 'MinuteReturnDiffStdSharpe', 'MinuteReturnSkew', 'MinuteReturnSkewSharpe', 'MinuteReturnSkewnessSharpe', 'MinuteReturnStdSharpe', 'MinuteReturnVolSharpe', 'MinuteReturnVolumeMultiple', 'MinuteReturnVolumeMultipleSharpe', 'MinuteSignedAbnormalSmartHHI', 'MinuteSignedAbnormalSmartMean', 'MinuteSignedAvgDistanceDiff', 'MinuteSignedAvgDistanceDiffMean', 'MinuteSortinoSharpe', 'MinuteTAVwapReturn5d', 'MinuteTERtnVRatio', 'MinuteTHLCorrRank', 'MinuteTLSTDiffRatio', 'MinuteTLSTRvs', 'MinuteTLSVRatio', 'MinuteTLTurn', 'MinuteTPVDeltaCorr', 'MinuteTRC', 'MinuteTRtnVGRank', 'MinuteTRtnVGStdRank', 'MinuteTRtnVRatioRank', 'MinuteTRtnZscore', 'MinuteTSD', 'MinuteTTLSStdRank', 'MinuteTTPVCorr', 'MinuteTVRtnRank', 'MinuteTWR', 'MinuteTrendStr', 'MinuteTrendStrSharp', 'MinuteTurnoverStdSharpe', 'MinuteTurnoverVolSharpe', 'MinuteUpVar', 'MinuteVARe5d', 'MinuteVAVwapReturnSR5d', 'MinuteVMASkew', 'MinuteVVCorrHalfRatio', 'MinuteVWAPSharpe', 'MinuteVWAPSortinoSharpe', 'MinuteValidRet', 'MinuteVarianceRatio', 'MinuteVirtualHighLowPathSR5d', 'MinuteVirtualHighLowStdDif5d', 'MinuteVirtualHighLowStdSR5d', 'MinuteVirtualLineUpdownAmt5d', 'MinuteVol', 'MinuteVolCV60m5D', 'MinuteVolCVSharpe10d', 'MinuteVolCVSkew10d', 'MinuteVolVwapCorrCloseChg', 'MinuteVolWeightedPowerEWM', 'MinuteVolofVolumeHHI', 'MinuteVolumeHHI', 'MinuteVolumeHHISharpe', 'MinuteVolumeKurt', 'MinuteVolumeMACD', 'MinuteVolumeRatioBias', 'MinuteVolumeSkew', 'MinuteVolumeStabilitySharpe', 'MinuteVolumeStd20dCV', 'MinuteVolumeStdSharpe', 'MinuteVolumeWeightedReturnSharpe', 'MinuteWRMean', 'MinuteWRVolume', 'MinuteliqAmtRatioSharpe20d', 'MinuteliqSwingSharpe5d', 'MinuteliqSwingStd5', 'MomHigh2Low10d', 'MomHigh2Low20d', 'MomHighExclMorn20d', 'MomHighPm5d', 'NCFP_tsrank12', 'NCFP_tsrank4', 'NCFP_tsrank8', 'NIGrowthZscore1y', 'NI_SQ_IndustryRank', 'NegativeIlliquidity', 'NetCash_surprise', 'NetProfitMargin_qfa_surprise', 'NetProfitMargin_qfa_tsrank12', 'NetProfitMargin_qfa_tsrank4', 'NetProfitMargin_qfa_tsrank8', 'NetProfitMargin_ttm_qoq', 'NetProfitMargin_ttm_tsrank12', 'NetProfitMargin_ttm_tsrank4', 'NetProfitMargin_ttm_tsrank8', 'NetProfitSurprise', 'NetProfit_surprise', 'NonstationaryPV', 'NonstationaryPVSharp', 'OCFP_tsrank12', 'OCFP_tsrank4', 'OCFP_tsrank8', 'OCFToSales_qfa_tsrank12', 'OCFToSales_ttm_tsrank12', 'OCFToSales_ttm_tsrank8', 'OCFToSales_ttm_yoy', 'OpenGapVolSharp10d', 'OprCost_surprise', 'OprProfitToNP_qfa_surprise', 'OprProfitToNP_ttm_qoq', 'OprProfitToNP_ttm_tsrank12', 'OprProfitToNP_ttm_tsrank8', 'OprProfitToNP_ttm_yoy', 'OprProfit_surprise', 'OvernightDaytimeMomentum', 'PEAdj', 'PVTTurn20d', 'PVTTurn5d', 'PVcorrMom', 'PePercent240d', 'PmVolumeRatio', 'PredictReturn2Volume', 'PriceChangePmToAm', 'PriceDiff', 'ROA_qfa_surprise', 'ROA_qfa_tsrank12', 'ROA_qfa_tsrank4', 'ROA_qfa_tsrank8', 'ROA_ttm_qoq', 'ROA_ttm_tsrank12', 'ROA_ttm_tsrank4', 'ROA_ttm_tsrank8', 'ROA_ttm_yoy', 'ROE_SQ', 'ROE_qfa_surprise', 'ROE_qfa_tsrank12', 'ROE_qfa_tsrank4', 'ROE_qfa_tsrank8', 'ROE_ttm_qoq', 'ROE_ttm_tsrank12', 'ROE_ttm_tsrank4', 'ROE_ttm_tsrank8', 'ROE_ttm_yoy', 'RSI', 'RangeRetCorr20', 'RankNetProfitDps', 'RankPBDev', 'RankPBRel', 'RankPEChange', 'RankPEDev', 'RankPERel', 'RankedReversion', 'ReCorr20', 'RelativeIndPE40d', 'RelativeIndPE5d', 'RelativeIndPEAS', 'RelativeIndPEGAvg', 'RetCorrTurnDelay', 'RetCorrTurnDelayPure', 'RetCutCorrTurnDelay', 'RetVolumeRetMultSharpe', 'ReturnSkewEMA20d', 'ReverseMomentum', 'ReverseMomentumDouble', 'ReverseMomentumTriple', 'SPPI', 'SP_tsrank12', 'SP_tsrank4', 'SP_tsrank8', 'Sales_surprise', 'SectorIlliquidity', 'SectorNotionalSharpe', 'SectorOverperformanceVol', 'SectorPESharpe', 'SectorSize', 'SectorSkewness', 'SimpleVolume', 'StdMaxAmountRatio', 'SwingHighLowPriceCorr', 'SwingToTurn', 'TopAmountRatioVolumeDiffSharpe', 'TurnAmtCorr20d', 'TurnCorrSharp', 'TurnMidCorr', 'TurnNeuIndusRank', 'TurnNeuRetCorrSharp', 'TurnPE', 'TurnPEAS', 'TurnPEAvg', 'TurnPEStd', 'TurnPercent_1d_240d', 'TurnRankPercent_1d_240d', 'TurnoverMean2Std', 'TurnoverSharpe', 'TurnoverSharpe100d', 'TurnoverStdRatio', 'Twap2Vwap', 'UpVolRatioDiff30', 'ValueDelay', 'ValueGrowth', 'ValueRefined', 'VolPriceCorr', 'VolPriceFlyer', 'VolPriceFlyerPlus', 'VolPriceRunner', 'VolitilityMax', 'VolitilityRelative', 'VolumePriceKurt240d', 'VolumeRatioDown20d', 'VolumeShortLongStdRatio', 'VolumeStdBias', 'VoteDiff30', 'VwapCloseAdj20d', 'VwapTurnStdRatio', 'Vwap_Close_Range_Diff', 'WAPResistBackRatio', 'WAPResistBackStd', 'WAPResistBackTop', 'WQ_011', 'WQ_026', 'WQ_042', 'WeightedDownUpSumRatio5d', 'ZZ500CorrClose', 'ZaoYinTrader', 'netprofit_std']
# factor_list = ['ACD6d', 'ACDIndicator', 'AbsRet2Deal', 'AgainstBeta', 'AmPmDiff', 'AmtEhdReverse', 'AmtRet1d', 'AmtRet20d', 'AmtRet5d', 'AmtRet60d', 'AmtStd20d', 'AmtStd60d', 'AmtStdBias', 'AmtStdMean20d', 'AmtStdMean60d', 'AmtVolStdRankMean5d', 'Amt_MidP_Diff', 'Argmin5d', 'AroonDown5d', 'Atr10d', 'Atr5d', 'AtrDelta10d20d', 'AtrDelta10d50d', 'AtrDelta20d50d', 'AtrDelta20d60d', 'AtrDelta5d10d', 'AtrRetCorr', 'AvgTurn20d', 'AvgTurn60d', 'BR20d', 'Bias120d', 'Bias30d', 'BollingerDown20d', 'BotTopCumSwingStdRatio', 'CCAREnhancedPVCorr', 'CCAREnhancedPVCorrMean20d', 'CCI10d', 'CCI60d', 'CEMVsharpe', 'CEMVstd', 'CSTurnpureCorrRet', 'CSTurnpureCorrRetSharp', 'CdABReversion', 'CdASReversion', 'CloseCorrTurnR2', 'CloseDistance2Journey', 'ClosePercentDeal5d_up', 'ClosePercentRank10d_up', 'CloseTurnCorr', 'CloseVolatility', 'CloseVolatility5d', 'CloseVwapRetKurt', 'CloseVwapRetSkew', 'CorrCloseTurn10d', 'CorrCloseTurn10d_max', 'CorrCloseTurn20d_max', 'CorrCloseTurn5d', 'CorrCloseTurn5d_max', 'CorrCloseVolumeSharpe', 'CorrDownVolumeSharpe', 'CorrVolReturn5d', 'CybzCorrClose', 'DavisWin', 'DealnumSharpe', 'DedProfitToNP_ttm_std_1y', 'DeltaCloseAdj10d', 'DeltaCloseAdj1d', 'DeltaCloseAdj20d', 'DeltaCloseAdj60d', 'DeltaTo5DMin', 'DeltaTurn', 'DeltaTurnSkew', 'DeltaVolume', 'DeltaVwapAdjValid', 'DownUpMeanRatio5d', 'DownUpSumRatio5d', 'DownVolatility120d', 'DownVolatility20d', 'DownVolatility5d', 'DownVolatility60d', 'DuoKongMix', 'DuoKongPV', 'EBITDev', 'EMVA', 'EP_Hist1_5D', 'EP_Hist2_120D', 'EP_tsrank8', 'EbitTTM', 'EbitdaTTM', 'EodMove', 'ExcessRetVolatility', 'FR10d_1001', 'FR10d_1130', 'FR20d_1001', 'FR20d_1130', 'FR40d', 'FR40d_1001', 'FallTurnover', 'GTJA_001', 'GTJA_003', 'GTJA_008', 'GTJA_009', 'GTJA_011', 'GTJA_012', 'GTJA_016', 'GTJA_019', 'GTJA_020', 'GTJA_022', 'GTJA_025', 'GTJA_026', 'GTJA_027', 'GTJA_028', 'GTJA_029', 'GTJA_031', 'GTJA_032', 'GTJA_034', 'GTJA_035', 'GTJA_036', 'GTJA_040', 'GTJA_041', 'GTJA_042', 'GTJA_045', 'GTJA_048', 'GTJA_052', 'GTJA_053', 'GTJA_054', 'GTJA_056', 'GTJA_057', 'GTJA_058', 'GTJA_059', 'GTJA_060', 'GTJA_061', 'GTJA_062', 'GTJA_063', 'GTJA_064', 'GTJA_065', 'GTJA_066', 'GTJA_067', 'GTJA_068', 'GTJA_069', 'GTJA_070', 'GTJA_071', 'GTJA_073', 'GTJA_074', 'GTJA_078', 'GTJA_079', 'GTJA_080', 'GTJA_081', 'GTJA_082', 'GTJA_083', 'GTJA_084', 'GTJA_087', 'GTJA_090', 'GTJA_092', 'GTJA_094', 'GTJA_096', 'GTJA_097', 'GTJA_098', 'GTJA_099', 'GTJA_105', 'GTJA_115', 'GTJA_118', 'GTJA_121', 'GTJA_124', 'GTJA_176', 'GTJA_179', 'GTJA_224', 'GrahamGrowth', 'GrahamValue', 'GrossProfitMargin_ttm_std_1y', 'GrowthRefined', 'HS300CorrClose', 'HighLowStdRatio_mean20d', 'HighLowSwingRatio', 'HighTurnCorr', 'HighVolCorrStd', 'HighVolumeCorr10d', 'IdeaReverser5d', 'IlliqCv60d', 'IlliqMean2TurnoverStd', 'IlliqNeg20d', 'IlliqNeg60d', 'IlliqSwing', 'IndustryNeutralizedTurnoverStd', 'LargeSmallVolumeVWAPRatio', 'LiqCorr', 'LiqRatio', 'LiqRatio5d', 'LiqRatioAS', 'LiqRatioSA', 'LiqRatioStd', 'LongShortPower', 'LowCandleBottom', 'LowSharpeAmountStdRatio', 'LowWire', 'MDI', 'MPV_EWMA', 'MPV_EWMASTD', 'MTM20d', 'MTM5d', 'Max2Min5d', 'MeanTurn2RetDown5d', 'MidPVolCorr20', 'Min10VolBurst5Wegihted5d', 'Min10mRetUpVar', 'Min15mPriceMax', 'Min30CEMVsharpe', 'Min5LastHalfHourVRSI10d', 'Min5LastHalfHourVolStd5d', 'Min5VwapToClose20d', 'Min5mAmtRatio', 'Min5mTopVolRet', 'Min60_RVstd', 'MinAbnCorr', 'MinAmtMidChg', 'MinAmtMidSkew', 'MinAmtMidStd', 'MinCEMVskew', 'MinCloseCallAmt5maCorrSharpe', 'MinCloseCallAmtBias5d', 'MinCloseCallAmtRatio', 'MinCloseVolume', 'MinCloseVolumeRank', 'MinCorHighVolumeMax10d', 'MinCorrRank', 'MinCorrRankMean', 'MinCorrVolumePrice', 'MinCorrVolumePrice10d', 'MinCorrVolumePrice20d', 'MinCorrVolumeRetUp10d', 'MinCorrVolumeRetUp5d', 'MinDirectedVol', 'MinEMVA', 'MinEMVAsharpe', 'MinEMVAstd', 'MinExcessSharpe5d', 'MinHighCorrVolume3d', 'MinHighVolSwing', 'MinHighVolumeRankCorr20d', 'MinIdx300Corr', 'MinIdx500Corr', 'MinIndexCorr', 'MinMaxDrawDownUp', 'MinNoiseReverse', 'MinRRC', 'MinRST', 'MinRSTstd', 'MinRetRange', 'MinReturnVolUp2Down5d', 'MinSkew20d', 'MinSkewSharpe10d', 'MinSkewStd20d', 'MinTMcorr', 'MinTWAPExcessSharpe10d', 'MinTopRetUpVar', 'MinTopVolCorr5D', 'MinUpBackSharpe', 'MinUpBackStd', 'MinVRCExcess5d', 'MinVVCorrRank', 'MinVVCorrRankStd', 'MinVVRankCorrStd', 'MinVVRtoCorrRank', 'MinVVRtoCorrRankMean', 'MinVolAmpCorrRatio', 'MinVolWeightedRet5d', 'MinVolumeVolUp2Down5d', 'MinVwapRV', 'MinVwapRV5', 'MinVwapRVskew', 'MinWeightVolReRatio', 'MinWeightVolReSkew', 'MinWeightVolReSwing', 'Min_IlliqCloseReturn', 'Min_IlliqShortcut', 'Min_OCVR20d', 'Min_OverBuy', 'Min_OverBuyVol', 'Min_RSRS', 'Min_Range_Ratio_1d', 'Min_Range_Ratio_20d', 'Min_Range_Ratio_5d', 'Min_RelativeDownReturn', 'Min_TurnoverSharp', 'Min_TurnoverStd', 'Min_UpRange', 'Minute30m5dTurnStd', 'Minute30m5dVolumeHHI', 'Minute5dAmtSimilarityRet', 'MinuteALTKurt', 'MinuteAbnormalRe5d', 'MinuteAbnormalRe5m', 'MinuteAfterRAVwapReturn5d', 'MinuteAmtAutocorr5d', 'MinuteAmtCV3d', 'MinuteAmtCV5d', 'MinuteAmtRetCor1d', 'MinuteAmtRetCor5d', 'MinuteAmtStdSwing', 'MinuteCloseCallAuctionTurnover', 'MinuteCloseConsistency', 'MinuteCloseMMT', 'MinuteCloseRDailyR', 'MinuteCloseResist', 'MinuteCloseTurn', 'MinuteCloseTurnCorr', 'MinuteCloseTurnPlus', 'MinuteCloseTurnRank', 'MinuteCloseTurnRev', 'MinuteCloseTurnSharp', 'MinuteCloseTurnoverStd', 'MinuteCloseUpVar', 'MinuteClosingSessionVolumePercent', 'MinuteCorrPriceNotionalSharpe', 'MinuteCorrPriceVolumeSharpe', 'MinuteCorrRank', 'MinuteCorrVolVwap', 'MinuteDailyMtm', 'MinuteDownVolatilityRatio20d', 'MinuteDuoKong0', 'MinuteEODSkewness120Min', 'MinuteEODVolWeightedLongShortPowerSharpe', 'MinuteEODVolumeRatio', 'MinuteGroupReBias5d', 'MinuteIdioKurt5d', 'MinuteIdioSkew5d', 'MinuteIlliqLast30m5D', 'MinuteIlliqVwapClose5d', 'MinuteLHourSkew', 'MinuteLTSkew', 'MinuteLast15Volume', 'MinuteLast1hrSkewSharpe', 'MinuteLast30mPriceVolRefine', 'MinuteLast30mPriceVolRefineMean', 'MinuteLast3hrsSkewSharpe', 'MinuteLast60mLongVolRatio', 'MinuteLastHourMDDMCLIMBstd20d', 'MinuteLastHourMaxClimb20dSR', 'MinuteLastHourMtm', 'MinuteLastHourSkewness5d', 'MinuteLastReStd1D', 'MinuteLastTurn20std', 'MinuteLastVolumeRank5std', 'MinuteLastVwapVolumeCorr', 'MinuteMPVCorrRank', 'MinuteMaxDistanceRetMA', 'MinuteMaxTenMinReturn', 'MinuteMaxTenMinReturnSharpe', 'MinuteMovingAverageDiffMax', 'MinuteMovingAverageDiffMaxEWM', 'MinutePCorr', 'MinutePVCorr', 'MinutePVCorrMean', 'MinutePVCorrMin', 'MinutePVCorrMinAdj', 'MinutePVCorrStdAdj', 'MinutePmSkew', 'MinutePmSkewEma10d', 'MinutePmSkewSharpe', 'MinutePriceStd10d', 'MinuteRAVolumeRatio5d', 'MinuteRSRSResidVolatilityZscore5d', 'MinuteRSRSstd5d', 'MinuteRePerDeal5d', 'MinuteRelativeUpVar', 'MinuteRetSkewnessSharpe', 'MinuteRetTurnCorr', 'MinuteRetTurnRho', 'MinuteRetVolMultSharpe', 'MinuteRetVolMultSkew', 'MinuteRetVolMultSkewSharpe', 'MinuteRetVolProdSkew', 'MinuteRetVolProdSkewSharpe', 'MinuteReturnAutocorr5d', 'MinuteReturnDiffStdSharpe', 'MinuteReturnSkew', 'MinuteReturnSkewSharpe', 'MinuteReturnSkewnessSharpe', 'MinuteReturnStdSharpe', 'MinuteReturnVolSharpe', 'MinuteSignedAbnormalSmartHHI', 'MinuteSignedAbnormalSmartMean', 'MinuteTAVwapReturn5d', 'MinuteTHLCorrRank', 'MinuteTLTurn', 'MinuteTrendStrength10d', 'MinuteTrendStrength20d', 'MinuteTrendStrength5d', 'MinuteTurnWeightedHLongRe', 'MinuteTurnWeightedHLongReMean', 'MinuteTurnoverStdSharpe', 'MinuteTurnoverVolSharpe', 'MinuteUpVar', 'MinuteVARe5d', 'MinuteVAVwapReturnSR5d', 'MinuteVMASkew', 'MinuteVVCorrHalfRatio', 'MinuteVarianceRatio', 'MinuteVirtualHighLowStdDif5d', 'MinuteVirtualHighLowStdSR5d', 'MinuteVol', 'MinuteVolCVSkew10d', 'MinuteVolVwapCorrCloseChg', 'MinuteVolWeightedPowerEWM', 'MinuteVolofVolumeHHI', 'MinuteVolume30minHHISharpe', 'MinuteVolumeHHI', 'MinuteVolumeHHISharpe', 'MinuteVolumeMACD', 'MinuteVolumeRate', 'MinuteVolumeRatioBias', 'MinuteVolumeSkew', 'MinuteVolumeStabilitySharpe', 'MinuteVolumeStd20dCV', 'MinuteVolumeStdSharpe', 'MinuteVwapDiff', 'MinuteliqAmtRatioSharpe20d', 'MinuteliqSwingSharpe5d', 'MinuteliqSwingStd5', 'MomHigh2Low10d', 'MomHigh2Low20d', 'MomHighExclMorn20d', 'NI_SQ_IndustryRank', 'NetProfitMargin_ttm_std_1y', 'NetProfitMargin_ttm_yoy', 'NonstationaryPV', 'NonstationaryPVSharp', 'OpenGapVolSharp10d', 'OpenHighMoveHigher', 'OvernightDaytimeMomentum', 'P2GWin', 'PB_Hist1_250D', 'PB_Hist2_5D', 'PCFWin', 'PDPS_Hist1_120D', 'PDPS_Hist2_120D', 'PEAdj', 'PEWin', 'PSWin', 'PS_Hist1_20D', 'PS_Hist2_250D', 'PVStdCap', 'PVTTurn20d', 'PVTTurn5d', 'PctChangeMax20d', 'PctChangeMax5d', 'PctChangeMax60d', 'PePercent240d', 'PeRoe', 'PeakDistancePV', 'PriceBiasDividStd60', 'PriceBiasZscore60', 'PriceChangePmToAm', 'PriceDelay', 'PriceDiff', 'ROEWin', 'ROE_SQ', 'ROE_ttm_std_1y', 'RSI', 'RangeRetCorr20', 'RankPBDev', 'RankPBRel', 'RankPEChange', 'RankPEDev', 'RankPERel', 'Re300ReturnScore5D', 'ReCorr20', 'Relative300Return5D', 'Relative500ReturnEMA10D', 'Relative500ReturnEMA120D', 'Relative500ReturnEMA20D', 'Relative500ReturnEMA60D', 'RelativeIndPE40d', 'RelativeIndPE5d', 'RelativeIndPEAS', 'RelativeIndPEGAvg', 'RelativePB', 'RelativePE', 'RelativePS', 'RetCorrCloseRank', 'RetCorrTurnDelay', 'RetCorrTurnDelayPure', 'RetCutCorrTurnDelay', 'RetVolumeRetMultSharpe', 'ReturnSkewEMA20d', 'ReverseDistance', 'ReverseMomentum', 'ReverseMomentumDouble', 'ReverseMomentumTriple', 'ReversePV40d', 'RhoCloseAmtMa20d', 'RhoCloseAmtMa60d', 'RhoSwingAmt20d', 'RhoSwingAmt60d', 'SPPI', 'SectorIlliquidity', 'SectorNotionalSharpe', 'SectorOverperformanceVol', 'SectorPESharpe', 'SectorSize', 'SectorSkewness', 'ShortBull', 'SimpleVolume', 'SizeNeuTurn5d', 'StdMaxAmountRatio', 'SwingDays10d', 'SwingDays20d', 'SwingDays5d', 'SwingHighLowPriceCorr', 'SwingToTurn', 'SwingTurn', 'TopAmountRatioVolumeDiffSharpe', 'TurnCV20', 'TurnDays10d', 'TurnDays20d', 'TurnDays5d', 'TurnDays60d', 'TurnMidCorr', 'TurnNeuIndusRank', 'TurnNeuRetCorrSharp', 'TurnPE', 'TurnPEAS', 'TurnPEAvg', 'TurnPEStd', 'TurnPercent_1d_240d', 'TurnPriceRatio10d', 'TurnPriceRatio20d', 'TurnRankPercent_1d_240d', 'TurnoverMean2Std', 'TurnoverSharpe', 'TurnoverSharpe100d', 'TurnoverStdRatio', 'Twap2Vwap', 'TyDegree', 'TyVolatility', 'UpDownVolatility', 'UpVolatility120d', 'UpVolatility20d', 'UpVolatility5d', 'UpVolatility60d', 'ValueDelay', 'ValueRefined', 'VolCV_60D', 'VolPriceCorr', 'VolPriceFlyer', 'VolPriceFlyerPlus', 'VolPriceRunner', 'VolitilityMax', 'VolitilityRelative', 'VolumeRatio20d', 'VolumeRatio5d', 'VolumeRatio60d', 'VolumeRatioDown20d', 'VolumeShortLongStdRatio', 'VolumeStdBias', 'VwapCloseAdj20d', 'VwapTurnStdRatio', 'WAPResistBackRatio', 'WAPResistBackStd', 'WAPResistBackTop', 'WQ_004', 'WQ_015', 'WQ_026', 'WQ_027', 'WQ_035', 'WQ_042', 'WQ_044', 'ZZ500CorrClose', 'ZaoYinTrader', 'alpha12']
rubbish = ['Vwap_Close_Range_Diff', 'LongBear', 'LongBull', 
'BollingerDown20d', 'ShortBear', 'BollingerUp20d', 
 'ShortBull', 'RankNetProfitDps']
factor_list = sorted(list(set(factor_list)-set(rubbish)))
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
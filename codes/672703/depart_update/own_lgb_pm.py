import numpy as np
import xgboost as xgb
import pickle
import pandas as pd
import xgboost as xgb
from lightgbm import LGBMRegressor ,LGBMRanker   
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from scipy.stats import norm
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
        dates = sample['date'].unique().tolist()
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
        prediction = res 
#        prediction = res.mean(axis =1)                    
        return prediction
def update_model_predict(root_path='',path_sample=[],factor_list=[],
            today_date = '20200407',retrain_flag = True,lookback_period_max = 300,
            model_config_list = [
                    ('XgboostReg_Model','vwap','vwap_re_1d',1,240),
                    ('DeepFM_Model','vwap','vwap_re_1d',1,240),
                    ('Lr_Model','vwap','vwap_re_5d',5,240)
                        ],suffix=None):
    t = time.time()
    path_feature = '/data/group/800020/AlphaDataCenter/Department/DepartSample/Sample/feature/'
    path_label = '/data/group/800020/AlphaDataCenter/Department/DepartSample/Sample/label/'
    path_feature = path_sample
    label = pd.read_pickle('/data/group/800020/AlphaExperiment/Test/label_1300_1459_keepna.pkl')
    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir(path_feature)])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period_max-20 : ]
        sample_feature = []
        sample_label = []
        for day in sample_required_dates:
            df = pd.read_pickle(path_feature+ day + '.pkl')
            sample_feature.append(df)
#            df = pd.read_pickle(path_label+ day + '.pkl')
#            sample_label.append(df)
        training_sample = pd.concat(sample_feature)
        # training_sample = training_sample.merge(pd.concat(sample_label),on=['date','stock'],how='left')
      
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
#            cond = (~np.isnan(retrain_samples[params['label_name']]))&(retrain_samples[params['label_name']].abs<=3)
            cond = (~np.isnan(retrain_samples[params['label_name']]))
            retrain_samples = retrain_samples[cond]
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
date_start = '20190101'
date_end = '20200706'
step = 20
count = 0
lookback_period_max = 240
retrain_flag = True  
root_path = '/data/user/013546/AlphaDataCenter/'
suffix = 'own_drop300_'+date_start+'_'+date_end+'/'
model_config_list= [
            ('LgbReg','pm','1300_1459_re_5d',5,240)
             ]
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/HFSample/hfactor_list.pkl')
print('old:',len(factor_list))
rubbish = ['Vwap_Close_Range_Diff', 'LongBear', 'LongBull', 
'BollingerDown20d', 'ShortBear', 'BollingerUp20d', 
 'ShortBull', 'RankNetProfitDps']+['GTJA_017', 'BP_tsrank4', 'ClosePercentHighLow', 'netprofit_std', 'GTJA_096', 'InventoryTurn_ttm_yoy', 'OprProfitToNP_qfa_tsrank8', 'GTJA_009', 'GTJA_008', 'ClosePercentIndus', 'VolumePriceKurt60d', 'SignedPriceRatio', 'BP_tsrank12', 'Min30_PRchange_5d', 'MinuteCorrReturnVolumeResampled', 'Min_Range_Ratio_1d', 'MinTWAPReSharpe5d', 'MinuteHighPricePos5d', 'CCI10d', 'GTJA_028', 'GTJA_078', 'MinExcessIndusPercent', 'GTJA_076', 'Min_CorrCloseVolume', 'CurDebtToDebt_tsrank8', 'GTJA_003', 'DeltaVwapAdjValid', 'WQ_054', 'DownDayReturn', 'IlliqCv20d', 'CloseDistance2Journey', 'MinUpDownRetAcc', 'GTJA_038', 'GTJA_080', 'GTJA_011', 'AtrDelta5d10d', 'VolumeReversionMultiple', 'GTJA_022', 'MinWR_20_80', 'MinuteCloseNetural', 'GTJA_013', 'LongBear', 'DeltaCloseAdj1d', 'GTJA_085', 'DeltaTurn', 'DeltaVolume', 'GTJA_021', 'MinuteEODRetVolMultipleBias', 'VolumeRatio5d', 'GTJA_002']
rubbish+=['MinuteLastHourMtm', 'VolMeanSharpeUp_13h', 'EodMove', 'VolumeRatio60d', 'VolumeRatio20d', 'AmtRet1d', 'GTJA_070', 'MinuteLast15Volume', 'Min_Range_Ratio_20d', 'MinuteTrendStrength20d', 'WQ_027', 'CorrCloseTurn10d', 'GTJA_080', 'MinuteTurnWeightedHLongRe', 'Min_Range_Ratio_5d', 'Min_Range_Ratio_1d', 'MinuteTurnWeightedHLongReMean', 'AtrDelta10d20d', 'MinuteDailyMtm', 'MinuteVolume30minHHISharpe', 'VolumeRatio5d', 'AtrDelta5d10d', 'WQ_044', 'GTJA_124', 'LiqRatioStd', 'AtrDelta10d50d', 'GTJA_179', 'TurnCV20', 'GTJA_118', 'WQ_035', 'GTJA_062', 'AmtStdMean20d', 'alpha12', 'LiqRatioSA', 'Amt_MidP_Diff', 'CorrCloseTurn5d', 'GTJA_078', 'LiqRatio', 'CCI10d', 'DeltaVwapAdjValid', 'EMVA', 'PriceBiasZscore60', 'PriceDelay', 'GTJA_066', 'GTJA_083', 'GTJA_029', 'PeakDistancePV', 'Relative500ReturnEMA10D', 'DeltaCloseAdj1d', 'GTJA_009', 'MinuteTrendStrength10d', 'GTJA_069', 'Bias30d', 'RhoCloseAmtMa20d', 'AmtRet5d', 'GTJA_031', 'PctChangeMax5d', 'AtrDelta20d50d', 'GTJA_084', 'VolCV_60D', 'PB_Hist2_5D', 'DeltaCloseAdj20d', 'ReverseDistance', 'GTJA_071', 'Relative500ReturnEMA20D', 'GTJA_036', 'LiqRatio5d', 'GTJA_115', 'RelativePS', 'GTJA_081', 'GTJA_074', 'AtrDelta20d60d', 'AmtRet20d', 'DeltaCloseAdj10d', 'MinuteVolumeRate', 'SwingDays5d', 'GTJA_224', 'Relative300Return5D', 'GTJA_020', 'MinuteTrendStrength5d', 'GTJA_019', 'TurnDays5d', 'DeltaTurn', 'GTJA_063', 'DeltaVolume', 'GTJA_027', 'GTJA_176', 'GTJA_011', 'WQ_015', 'Min_OCVR20d', 'CloseTurnCorr', 'PEWin', 'GTJA_079', 'GTJA_060', 'UpDownVolatility', 'SwingDays10d', 'AmtStdMean60d', 'MDI', 'RelativePB', 'CCI60d', 'UpVolatility20d', 'PS_Hist1_20D', 'PctChangeMax20d', 'GTJA_097', 'PS_Hist2_250D', 'MinuteCloseRDailyR', 'UpVolatility5d', 'SizeNeuTurn5d', 'TurnDays10d', 'AmPmDiff', 'GTJA_067', 'AmtStd20d', 'GTJA_022', 'MinuteVwapDiff', 'PCFWin', 'GTJA_003', 'PDPS_Hist2_120D', 'GTJA_057', 'MinutePCorr', 'GTJA_045', 'RhoCloseAmtMa60d', 'RelativePE', 'SwingTurn', 'ReversePV40d', 'MTM5d', 'Min_CloseAutoCorrZScore', 'TyDegree', 'GTJA_094', 'GTJA_096', 'OpenHighMoveHigher', 'GTJA_040', 'TurnDays20d', 'PriceBiasDividStd60', 'MinuteEODRetVolMultipleBias', 'Relative500ReturnEMA60D', 'AvgTurn20d', 'ACD6d', 'MinWR_20_80', 'WQ_054', 'GTJA_056', 'P2GWin', 'GTJA_058', 'PSWin', 'SwingDays20d', 'MinuteCorrReturnVolumeResampled', 'ShortBull', 'GTJA_053', 'GTJA_001', 'MinSignedAmtPriceDelayDeltaCorr', 'MinutePMRtnZscore10d', 'ROEWin', 'MinuteReturnVolumeMultiple', 'CloseDistance2Journey', 'Bias120d', 'MinPmRSRS', 'HF_Last30minUpVolumeRetZscore_13h', 'RhoSwingAmt60d', 'ACDIndicator', 'Min30_PRchange_1d', 'GTJA_028', 'DownSpace', 'MinUpDownRetAcc', 'VolumePriceKurt60d', 'MinuteLastVwapVolumeCorr', 'DeltaCloseAdj60d', 'MTM20d', 'Relative500ReturnEMA120D', 'Atr5d', 'MinuteRetVolMultMean', 'MinuteCloseNetural', 'MinuteEODSortinoRatio', 'AmtRet60d', 'GTJA_013', 'MaxDrawDown_13h', 'PctChangeMax60d', 'UpVolatility60d', 'MinuteCloseConsistency', 'Re300ReturnScore5D', 'VolumePriceKurt120d', 'Min_ACDSharp', 'TyVolatility', 'AmtStd60d', 'HighFreqSwingStdCmp_13h', 'MinuteEODSharpe', 'WR2d_13h', 'Min_CorrCloseVolume', 'TurnDays60d', 'PDPS_Hist1_120D', 'GTJA_002', 'MinuteAmPmReturnDiff', 'AvgTurn60d', 'OCFToSales_ttm_std_3y', 'MinuteCloseDuoKong', 'PVStdCap', 'UpVolatility120d', 'Min_CloseBias', 'GTJA_052', 'MinuteEODVolWeightedLongShortPower', 'RhoSwingAmt20d', 'GTJA_085']
rubbish+=['MinuteLastHourMtm', 'VolMeanSharpeUp_13h', 'EodMove', 'VolumeRatio60d', 'VolumeRatio20d', 'AmtRet1d', 'GTJA_070', 'MinuteLast15Volume', 'Min_Range_Ratio_20d', 'MinuteTrendStrength20d', 'WQ_027', 'CorrCloseTurn10d', 'GTJA_080', 'MinuteTurnWeightedHLongRe', 'Min_Range_Ratio_5d', 'Min_Range_Ratio_1d', 'MinuteTurnWeightedHLongReMean', 'AtrDelta10d20d', 'MinuteDailyMtm', 'MinuteVolume30minHHISharpe', 'VolumeRatio5d', 'AtrDelta5d10d', 'WQ_044', 'GTJA_124', 'LiqRatioStd', 'AtrDelta10d50d', 'GTJA_179', 'TurnCV20', 'GTJA_118', 'WQ_035', 'GTJA_062', 'AmtStdMean20d', 'alpha12', 'LiqRatioSA', 'Amt_MidP_Diff', 'CorrCloseTurn5d', 'GTJA_078', 'LiqRatio', 'CCI10d', 'DeltaVwapAdjValid', 'EMVA', 'PriceBiasZscore60', 'PriceDelay', 'GTJA_066', 'GTJA_083', 'GTJA_029', 'PeakDistancePV', 'Relative500ReturnEMA10D', 'DeltaCloseAdj1d', 'GTJA_009', 'MinuteTrendStrength10d', 'GTJA_069', 'Bias30d', 'RhoCloseAmtMa20d', 'AmtRet5d', 'GTJA_031', 'PctChangeMax5d', 'AtrDelta20d50d', 'GTJA_084', 'VolCV_60D', 'PB_Hist2_5D', 'DeltaCloseAdj20d', 'ReverseDistance', 'GTJA_071', 'Relative500ReturnEMA20D', 'GTJA_036', 'LiqRatio5d', 'GTJA_115', 'RelativePS', 'GTJA_081', 'GTJA_074', 'AtrDelta20d60d', 'AmtRet20d', 'DeltaCloseAdj10d', 'MinuteVolumeRate', 'SwingDays5d', 'GTJA_224', 'Relative300Return5D', 'GTJA_020', 'MinuteTrendStrength5d', 'GTJA_019', 'TurnDays5d', 'DeltaTurn', 'GTJA_063', 'DeltaVolume', 'GTJA_027', 'GTJA_176', 'GTJA_011', 'WQ_015', 'Min_OCVR20d', 'CloseTurnCorr', 'PEWin', 'GTJA_079', 'GTJA_060', 'UpDownVolatility', 'SwingDays10d', 'AmtStdMean60d', 'MDI', 'RelativePB', 'CCI60d', 'UpVolatility20d', 'PS_Hist1_20D', 'PctChangeMax20d', 'GTJA_097', 'PS_Hist2_250D', 'MinuteCloseRDailyR', 'UpVolatility5d', 'SizeNeuTurn5d', 'TurnDays10d', 'AmPmDiff', 'GTJA_067', 'AmtStd20d', 'GTJA_022', 'MinuteVwapDiff', 'PCFWin', 'GTJA_003', 'PDPS_Hist2_120D', 'GTJA_057', 'MinutePCorr', 'GTJA_045', 'RhoCloseAmtMa60d', 'RelativePE', 'SwingTurn', 'ReversePV40d', 'MTM5d', 'Min_CloseAutoCorrZScore', 'TyDegree', 'GTJA_094', 'GTJA_096', 'OpenHighMoveHigher', 'GTJA_040', 'TurnDays20d', 'PriceBiasDividStd60', 'MinuteEODRetVolMultipleBias', 'Relative500ReturnEMA60D', 'AvgTurn20d', 'ACD6d', 'MinWR_20_80', 'WQ_054', 'GTJA_056', 'P2GWin', 'GTJA_058', 'PSWin', 'SwingDays20d', 'MinuteCorrReturnVolumeResampled', 'ShortBull', 'GTJA_053', 'GTJA_001', 'MinSignedAmtPriceDelayDeltaCorr', 'MinutePMRtnZscore10d', 'ROEWin', 'MinuteReturnVolumeMultiple', 'CloseDistance2Journey', 'Bias120d', 'MinPmRSRS', 'HF_Last30minUpVolumeRetZscore_13h', 'RhoSwingAmt60d', 'ACDIndicator', 'Min30_PRchange_1d', 'GTJA_028', 'DownSpace', 'MinUpDownRetAcc', 'VolumePriceKurt60d', 'MinuteLastVwapVolumeCorr', 'DeltaCloseAdj60d', 'MTM20d', 'Relative500ReturnEMA120D', 'Atr5d', 'MinuteRetVolMultMean', 'MinuteCloseNetural', 'MinuteEODSortinoRatio', 'AmtRet60d', 'GTJA_013', 'MaxDrawDown_13h', 'PctChangeMax60d', 'UpVolatility60d', 'MinuteCloseConsistency', 'Re300ReturnScore5D', 'VolumePriceKurt120d', 'Min_ACDSharp', 'TyVolatility', 'AmtStd60d', 'HighFreqSwingStdCmp_13h', 'MinuteEODSharpe', 'WR2d_13h', 'Min_CorrCloseVolume', 'TurnDays60d', 'PDPS_Hist1_120D', 'GTJA_002', 'MinuteAmPmReturnDiff', 'AvgTurn60d', 'OCFToSales_ttm_std_3y', 'MinuteCloseDuoKong', 'PVStdCap', 'UpVolatility120d', 'Min_CloseBias', 'GTJA_052', 'MinuteEODVolWeightedLongShortPower', 'RhoSwingAmt20d', 'GTJA_085', 'VolumeReversionMultiple', 'GTJA_092', 'MinuteEODReturn', 'GTJA_223', 'MinTWAPReSharpe5d', 'MinutePriceMACD', 'WR_13h', 'HfHalfDayCloseRtnCountDiffBias_13h', 'MinuteEODRetVolMultiple', 'Min_ACDBias', 'MinuteEODVolumeWeightedReturn', 'MinuteVolCV60m5D', 'Atr10d', 'DavisWin', 'PB_Hist1_250D', 'Min30_PRchange_5d', 'MinuteVolumeWeightedReturnSharpe', 'DownVolatility5d', 'VolumePriceKurt240d', 'Min_DownReturn', 'HfLast120RangeMeanRatio_13h', 'GTJA_076', 'MinuteTRtnZscore', 'VolSharpeUp_13h', 'DownVolatility120d', 'MinuteSkew5d', 'RankedReversion', 'TurnPriceRatio10d', 'IlliqCv20d', 'DownVolatility60d', 'IlliqCv60d', 'MinSkipCorrRatio', 'HighFreqWaveRetStd_13h', 'MomHighPm5d', 'HfLast120RangeMeanRatioBias_13h', 'Min_CloseSignAutoCorrZScore', 'HighFreqDrawBackStdBias_13h', 'CorrVWAPTrendHigh_13h', 'Min5LastHourElder5dSharp', 'MinuteHTRtnRvs', 'GTJA_059', 'HighLowVwapRatio5d', 'MinuteVWAPSharpe', 'MinuteEODVolumeWeightedReturnEWM', 'MinuteVWAPSortino', 'WQ_011', 'MinExcessIndusPercent', 'ClosePercentHighLow', 'MinuteTWR', 'BollingerUp20d', 'MinuteSkew10d', 'GTJA_068', 'GTJA_038', 'MinuteLastSR5d', 'DownVolatility20d', 'WilliamsIndicator_13h', 'GTJA_004', 'ReLow_13h', 'Min30WeightVolAmpCloseRatio', 'Min60RSRS', 'MinuteCloseVolumeXCorr', 'MinPMSignAmplitude5d', 'HfLongVwapSwingCorrBias_13h', 'GTJA_021', 'DedProfitToNP_ttm_std_1y', 'MinuteCloseVol30mChg', 'MinuteClosingSREWM', 'UpDownVol5d', 'PredictReturn2Volume', 'ReVolumeCorr_13h', 'netprofit_std', 'Atr20d', 'MinuteLastSR5HHI', 'GrossProfitMargin_ttm_std_3y', 'GTJA_065', 'OCFToSales_ttm_std_1y', 'Min_ACDZScore', 'MinPmRSRS5d', 'ClosePercentIndus', 'MinuteLongBear', 'RelativeDy', 'VolumeDownChange_13h', 'NetProfitMargin_ttm_std_3y', 'alpha53', 'MinuteVolWeightedPowerEWM', 'CloseLoc', 'InventoryTurn_ttm_std_1y', 'AssetTurn_ttm_std_3y', 'PeRoe', 'Min5LastHourElder20d', 'Minute60minBias5d', 'CurDebtToDebt_tsrank4', 'Min5LastHourVwapCorrVolume5d', 'SwingPriceLongCorr_13h', 'MinuteMADistanceSP', 'GTJA_007', 'MinuteVirtualHighLowPathSR5d', 'ROE_ttm_std_1y', 'MinuteEODWinRate', 'MinuteCloseOpenEWMA', 'WQ_038', 'Max2Min5d', 'BP_tsrank12', 'UpVolDiff30', 'MinuteCloseMomentumBias', 'LongBull', 'hfCPVCorrHDbias_13h', 'MinDownPVCorr', 'DebtToAsset_std_3y', 'GTJA_077', 'GTJA_017', 'Twap2Vwap', 'HighLowStdRatio5d', 'ROE_ttm_std_3y', 'OprProfitToNP_ttm_std_3y', 'MinuteSwingRatio_13h', 'MinExcessSharpe', 'GTJA_015', 'Min_CloseSignAutoCorr', 'DownDayReturn', 'HighLowVwapRatio_13', 'GrossProfitMargin_ttm_std_1y', 'NetProfitMargin_ttm_std_1y', 'Minute15mReTo5D', 'Min60UpDownRatio', 'OprProfitToNP_ttm_std_1y', 'MinCorrRto5m5dAdj', 'MinuteCloseWR', 'OprProfitToNP_ttm_yoy', 'OprProfitToNP_qfa_tsrank4', 'Atr50d', 'GTJA_091', 'MinVolAmpCorrRatio', 'OprProfitToNP_ttm_qoq', 'MinHighVolRet', 'MinuteBias30m5D', 'MinuteSortinoSharpe', 'MinuteSkew20d', 'MinuteAroon', 'Atr60d', 'MinuteVirtualHighLowStdDif5d', 'GTJA_006', 'DebtToAsset_std_1y', 'PmVolumeRatio', 'GTJA_008', 'BP_tsrank8', 'BP_tsrank4', 'OprProfitToNP_ttm_tsrank4', 'TurnPriceRatio20d', 'CurDebtToDebt_std_3y', 'MinuteSwing', 'MinuteLastRetCMO', 'ClosePercentLast60', 'Last30MinUpDownMoneyRatio5d', 'FCFFP_tsrank12', 'Coskew60d', 'MinHighCorrVolume3d']
factor_list = sorted(list(set(factor_list)-set(rubbish)))
print('factor list num:',len(factor_list))
path_sample = '/data/group/800020/AlphaDataCenter/HFSample/NormSample/'#
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
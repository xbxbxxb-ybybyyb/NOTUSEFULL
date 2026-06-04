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
    depart_factor_list = ['ForecastPERoll', 'C9_DIFF60', 'profitchg_alpuniv', 'roe_basic_alpunivchg', 'ODPB_DIFF120', 'qfa_yoysales_alpunivchg', 'yoynetprofit_alpunivchg', 'CumretClseSlope_60', 'PVTTurn180d', 'RetVolMultSharp_30', 'UpVolatilityRatio_20', 'alphas_dongj_pct_chg_swing_combine', 'ForecastEPPercent120d', 'RevSplit', 'ForecastPEGRollChange40d', 'ForecastPEGDelta20d', 'PsPercent240d', 'ForecastPEGRoll', 'MinCM', 'VolSurgeSharpe', 'PVTTurn60d', 'RankinglistEffect', 'ODPB_DIFF20', 'ForecastEPChange60d', 'ForecastEPDelta20d', 'RetMktDevCorr', 'ForecastBPPercent120d', 'ForecastPE', 'DivMulStaVol', 'LowRtnVolGrowthSharpe60d', 'ValueGrowthChange60d', 'HighCapVolumeRR', 'MinRVM', 'ForecastPEGDelta5d', 'TurnGain', 'CorrCloseRankTurn20d', 'MinRRCs', 'GTJA36', 'GTJA2TransRolling20', 'SmallPlayersVwap', 'ODPEG_DIFF20', 'InvSta', 'ForecastPEGPercent120d', 'MarketHolder', 'TwapVwapRet', 'ExtremeTurnStd', 'CloseCapVolumeRRSharp', 'PcfPercent240d', 'OpenCapVolumeRR', 'AmtDealReDiff5d', 'ODPEG_DIFF120', 'alp10_alpuniv', 'BeforehandRetCut30', 'AbnAmtRet', 'WinnerList_225', 'BoolDW', 'MomW', 'RTurnGainStd', 'BigPlayersVwap', 'BeforehandRetCut20', 'TurnCV_10', 'RTurnGainMin', 'TickFactor_PassBuyOrderStdRatio', 'GTJA2TransRolling5', 'AmtPerDealRetCorr', 'Tick_bsdiff_hl_top_active_ordervol_cov3_daily', 'MinVwapARC2VRCExcessSharpe20d', 'LoserList_200', 'CEMV_CS30_Skew40', 'alp22_alpuniv', 'TickFactor_MaxActBuyOrderStdRatio', 'csad_ftest', 'MinPVCS', 'pechgnew_alpuniv', 'ForecastEPGChange60d', 'uretvvolnew_stdskew_60_10_daily', 'TickFactor_MaxBuyOrderStdRatio', 'dretvvolnew_scmmean_20_10_daily', 'CapVolumeRR', 'MinTTM', 'MinUBS', 'MinWAC', 'LiquidityPure20Part2', 'BeforehandRetResidual30', 'TurnHighCloseSigma', 'IVR_000300_20', 'MinSkew40d', 'TickFactor_RegBuyOrderStdRatio', 'Tick_bsdiff_illq_tail_passive_orderamt_corr3_daily', 'RetSkewSharp', 'alp29_alpuniv', 'OperRevTTMStandardGrowth', 'AmtPerTradeWeightedReturn', 'MinuteTWRSharpe20', 'MinUBK', 'BigOrderReturn20d', 'CorrRetAmtPct_CS15', 'dwf_alpuniv', 'TickFactor_ActBuyOrderStdRatio', 'HighCloseTurnSharpe']
    own_factor_list = sorted(list(set(factor_list)-set(depart_factor_list)))
    label = pd.read_pickle('/data/user/013546/rubbish/label_keepna.pkl')
    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir(path_feature)])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period_max-20 : ]
        sample_depart_feature = []
        sample_own_feature = []
        sample_label = []
        for day in sample_required_dates:
            df = pd.read_pickle(path_feature+ day + '.pkl')
            sample_depart_feature.append(df)
            df = pd.read_pickle(path_sample+ day + '.pkl')
            sample_own_feature.append(df)
#            df = pd.read_pickle(path_label+ day + '.pkl')
#            sample_label.append(df)
        depart_sample = pd.concat(sample_depart_feature)
        own_sample = pd.concat(sample_own_feature)
     
        # training_sample = training_sample.merge(pd.concat(sample_label),on=['date','stock'],how='left')
        training_sample = depart_sample[['date','stock']+depart_factor_list].merge(own_sample[['date','stock']+own_factor_list],on=['date','stock'],how='left')
        training_sample = training_sample[['date','stock']+factor_list].merge(label,on=['date','stock'],how='left')
        print('......................')   
    sample_daily0 = pd.read_pickle(path_feature+today_date+'.pkl')
    sample_daily1 = pd.read_pickle(path_sample+today_date+'.pkl')
    sample_daily = sample_daily0[['date','stock']+depart_factor_list].merge(sample_daily1[['date','stock']+own_factor_list],on=['date','stock'],how='left')
    print(len(sample_daily.columns))
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
date_end = '20191231'
step = 20
count = 0
lookback_period_max = 240
retrain_flag = True  
root_path = '/data/user/013546/AlphaDataCenter/'
suffix = 'own_depart_'+date_start+'_'+date_end+'/'
model_config_list= [
            ('LgbReg','vwap','vwap_re_5d',5,240)
             ]
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
print('old:',len(factor_list))
rubbish = ['Vwap_Close_Range_Diff', 'LongBear', 'LongBull', 
'BollingerDown20d', 'ShortBear', 'BollingerUp20d', 
 'ShortBull', 'RankNetProfitDps']+['GTJA_017', 'BP_tsrank4', 'ClosePercentHighLow', 'netprofit_std', 'GTJA_096', 'InventoryTurn_ttm_yoy', 'OprProfitToNP_qfa_tsrank8', 'GTJA_009', 'GTJA_008', 'ClosePercentIndus', 'VolumePriceKurt60d', 'SignedPriceRatio', 'BP_tsrank12', 'Min30_PRchange_5d', 'MinuteCorrReturnVolumeResampled', 'Min_Range_Ratio_1d', 'MinTWAPReSharpe5d', 'MinuteHighPricePos5d', 'CCI10d', 'GTJA_028', 'GTJA_078', 'MinExcessIndusPercent', 'GTJA_076', 'Min_CorrCloseVolume', 'CurDebtToDebt_tsrank8', 'GTJA_003', 'DeltaVwapAdjValid', 'WQ_054', 'DownDayReturn', 'IlliqCv20d', 'CloseDistance2Journey', 'MinUpDownRetAcc', 'GTJA_038', 'GTJA_080', 'GTJA_011', 'AtrDelta5d10d', 'VolumeReversionMultiple', 'GTJA_022', 'MinWR_20_80', 'MinuteCloseNetural', 'GTJA_013', 'LongBear', 'DeltaCloseAdj1d', 'GTJA_085', 'DeltaTurn', 'DeltaVolume', 'GTJA_021', 'MinuteEODRetVolMultipleBias', 'VolumeRatio5d', 'GTJA_002']
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
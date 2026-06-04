import numpy as np 
import pandas as pd 
from config_path import *
import sys
sys.path.insert(0,'am_update_pf/model/')
from DeepFM import *
from XgboostRegression import *
from LinearRegression import *
from XgboostReg_Model_V1 import *
from LgbReg import *
from xquant.xqutils.helper import link
lm = link.LinkMessage()

def get_trade_date(start_date, window):
    is_valid = pd.read_pickle(basic_daily_path + 'is_valid.pkl')
    if type(window) == type(start_date):
        return is_valid.loc[start_date:window].index
    elif window > 0:
        return is_valid.loc[start_date:].iloc[:window].index
    else:
        return is_valid.loc[:start_date].iloc[window:].index
def update_model_fix_predict(root_path='',
            today_date = '20200407',retrain_flag = True,lookback_period_max = 300,
            model_config_list = [
                    ('XgboostReg_Model','vwap','vwap_re_1d',1,240)
                        ],suffix=None,act_check=False,pred_label=True):
    t = time.time()
    factor_info = pd.read_pickle(factor_info_path)
    own_factors = sorted(list(set(factor_info['own_day_factors']+factor_info['own_fix_factors'])))
    depart_day_factors = factor_info['depart_day_factors']
    factor_list = sorted(list(set(own_factors+depart_day_factors)))
    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir(day_depart_feature_path)])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period_max-20 : ]
        sample_feature = []
        sample_label = []
        for day in sample_required_dates:
            pre_day = get_trade_date(day,-2)[-2].strftime('%Y%m%d')
            df0 = pd.read_pickle(day_depart_feature_path+ pre_day + '.pkl')[['stock']+depart_day_factors]
            df1 = pd.read_pickle(hsample_norm_path+ day + '.pkl')[['date','stock']+own_factors]
            df = df1.merge(df0,on=['stock'],how='left')
            sample_feature.append(df)
            df = pd.read_pickle(fix_depart_label_path+day+'.pkl')
            sample_label.append(df)
        training_sample = pd.concat(sample_feature)
        training_sample = training_sample[['date','stock']+factor_list].merge(pd.concat(sample_label),on=['date','stock'],how='left')
        print('......................')   
    pre_day = get_trade_date(today_date,-2)[-2].strftime('%Y%m%d')
    df0 = pd.read_pickle(day_depart_feature_path+ pre_day + '.pkl')[['stock']+depart_day_factors]
    df1 = pd.read_pickle(hsample_norm_path+ today_date + '.pkl')[['date','stock']+own_factors]
    sample_daily = df1.merge(df0,on=['stock'],how='left')
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
        if not os.path.exists(params['model_path']):
            os.makedirs(params['model_path'])
        if not os.path.exists(params['prediction_path']):
            os.makedirs(params['prediction_path'])
        execstr = config[0]+'(params)'
        model = eval(execstr)
        if retrain_flag == True:
            gap_period = config[3]
            model_retrain_date = all_trading_days[-config[4]- gap_period-1 :-gap_period-1]
            retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]
            retrain_samples = retrain_samples[~np.isnan(retrain_samples[params['label_name']])]
       
            t = time.time()
            if not os.path.exists(model._model_path):
                os.makedirs(model._model_path)
            model.get_model(retrain_samples.copy(), factor_list)
            print(model._modelname +' re-train finished' , time.time() - t)
        
        pred = model.label_predict(sample_daily, factor_list)
        if not os.path.exists(model._prediction_path):
            os.makedirs(model._prediction_path)
        if pred_label:
            pred.to_csv(model._prediction_path + today_date +'.csv')
        if act_check:
            act_stat = pred.describe()
            act_stat = round(act_stat,2)
            act_stat = act_stat.astype('str')
            act_stat_ = act_stat.to_dict()

            act_dict_str = ''
            for key, value in act_stat_.items():
                act_dict_str=act_dict_str+key+':'+value+', '        
            lm.sendMessage("Train :%s,  %s, %s" % (params['modelname'],act_dict_str,today_date))            
        print(model._modelname +'   predict finished' , today_date, time.time() - t)

def update_model_day_predict(root_path='',today_date = '20200407',retrain_flag = True,lookback_period_max = 300,
            model_config_list = [
                    ('XgboostReg_Model','vwap','vwap_re_1d',1,240)
                        ],suffix=None,act_check=False,pred_label=True):
    t = time.time()
    factor_info = pd.read_pickle(factor_info_path)
    factor_list = sorted(list(set(factor_info['depart_day_factors']+factor_info['own_day_factors'])))
    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir(day_depart_feature_path)])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period_max-20 : ]
        sample_feature = []
        sample_label = []
        sample_own_feature = []
        for day in sample_required_dates:
            df = pd.read_pickle(day_depart_feature_path+ day + '.pkl')[['date','stock']+factor_info['depart_day_factors']]
            sample_feature.append(df)
            df = pd.read_pickle(sample_norm_path+ day + '.pkl')[['date','stock']+factor_info['own_day_factors']]
            sample_own_feature.append(df)
            df = pd.read_pickle(day_depart_label_path+ day + '.pkl')
            sample_label.append(df)
        training_sample = pd.concat(sample_feature)
        training_sample = training_sample.merge(pd.concat(sample_own_feature),on=['date','stock'],how='left')
        training_sample = training_sample.merge(pd.concat(sample_label),on=['date','stock'],how='left')

        print('......................')   
    sample_daily = pd.read_pickle(day_depart_feature_path+today_date+'.pkl')[['date','stock']+factor_info['depart_day_factors']]
    sample_daily_own = pd.read_pickle(sample_norm_path+ today_date + '.pkl')[['date','stock']+factor_info['own_day_factors']]
    sample_daily = sample_daily.merge(sample_daily_own,on=['date','stock'],how='left')
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
        print(params['model_path'],params['prediction_path'])
        execstr = config[0]+'(params)'
        model = eval(execstr)
        if retrain_flag == True:
            gap_period = config[3]
            model_retrain_date = all_trading_days[-config[4]- gap_period-1 :-gap_period-1]
            retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]
            retrain_samples = retrain_samples[~np.isnan(retrain_samples[params['label_name']])]
            t = time.time()
            if not os.path.exists(model._model_path):
                os.makedirs(model._model_path)
            print(model._modelname +' re-train begin' , time.time() - t)
            model.get_model(retrain_samples.copy(), factor_list)
            print(model._modelname +' re-train finished' , time.time() - t)
        
        pred = model.label_predict(sample_daily, factor_list)
        if not os.path.exists(model._prediction_path):
            os.makedirs(model._prediction_path)
        if pred_label:
            pred.to_csv(model._prediction_path + today_date +'.csv')

        if act_check:
            act_stat = pred.describe()
            act_stat = round(act_stat,2)
            act_stat = act_stat.astype('str')
            act_stat_ = act_stat.to_dict()

            act_dict_str = ''
            for key, value in act_stat_.items():
                act_dict_str=act_dict_str+key+':'+value+', '        
            lm.sendMessage("Train :%s,  %s, %s" % (params['modelname'],act_dict_str,today_date))    
        
        print(model._modelname +'   predict finished' , today_date, time.time() - t)
        
def update_model_predict(today_date,retrain_flag=False,model_type='am',act_check=False,pred_label=True):
    if model_type=='pm':
        update_model_fix_predict(root_path=model_root_path,
            today_date = today_date,retrain_flag = retrain_flag,lookback_period_max = 240,
            model_config_list = model_config_dict[model_type],act_check=act_check,pred_label=pred_label)
    else:
        update_model_day_predict(root_path=model_root_path,
            today_date = today_date,retrain_flag = retrain_flag,lookback_period_max = 240,
            model_config_list = model_config_dict[model_type],act_check=act_check,pred_label=pred_label)


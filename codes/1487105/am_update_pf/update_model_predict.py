import numpy as np 
import pandas as pd 
from config_path import *
import sys
sys.path.insert(0,'am_update_pf/model/')
from DeepFM import *
from DeepFM_300 import *
from DeepFM_500 import *
from KerasDeepFM import *
from DeepFM import *
from XgboostRegression import *
from LinearRegression import *
from XgboostReg_Model_V1 import *
from XgbRegTSFourModel import *
from LgbReg import *
from XgbSP import *
from KerasDeepFMMulti import *
import update_sample
from xquant.xqutils.helper import link
lm = link.LinkMessage()

def update_single_model(root_path,modelname,strategy_type,label_name,gap,train_window=240,sample_flag=True,factor_list=[],
                    today_date='',suffix='',train_flag=True,act_check=True,custom_params={}):
    factor_own = [i[:-11] for i in factor_list if 'TeamSample' in i.split('_')]
    factor_dep = [i for i in factor_list if 'TeamSample' not in i.split('_')]
    factor_list_real = sorted(list(set(factor_own+factor_dep)))
    t = time.time()
    root_model_path = root_path+'Models/'+strategy_type+'/'
    root_predict_path = root_path+'/DailyPrediction/'+strategy_type+'/'
    print('factor list',len(factor_list))
    if not suffix=='':
        root_model_path += suffix
        root_predict_path += suffix
    params={}
    params['label_name'] = label_name
    params['modelname'] = modelname+'_'+label_name
    params['model_path'] = root_model_path + params['modelname']+'/'
    params['prediction_path'] = root_predict_path + params['modelname']+'/'
    params['strategy_type'] = strategy_type
    params.update(custom_params)
    print(params)
    execstr = modelname+'(params)'
    model = eval(execstr)
    if train_flag:
        train_date = today_date
        all_trading_days = sorted([e[:-4] for e in os.listdir(day_depart_feature_path)])
        all_trading_days = [e for e in all_trading_days if e <= train_date]
        model_retrain_date = all_trading_days[-train_window- gap-1 :-gap-1]
        t = time.time()
        if not os.path.exists(model._model_path):
            os.makedirs(model._model_path)
        print(model._modelname +' re-train begin' , time.time() - t)
        
        if not sample_flag:
            model.get_model(model_retrain_date, factor_list)
        else:
            sample = update_sample.load_sample(factor_list,model_retrain_date,strategy_type,label_name,train_flag)
            sample = sample[~np.isnan(sample[label_name])]
            model.get_model(sample,factor_list_real)
        print(model._modelname +' re-train finished' , time.time() - t)
    if not os.path.exists(model._prediction_path):
        os.makedirs(model._prediction_path)
    today_sample = update_sample.load_sample(factor_list,[today_date],strategy_type,label_name,False)
    pred = model.label_predict(today_sample, factor_list_real)
    pred.to_csv(model._prediction_path + today_date +'.csv') 
    print(model._modelname +'   predict finished' , time.time() - t) 
  
def update_model_predict(today_date,retrain_flag=False,model_type='am',act_check=False,pred_label=True):
    factor_custom_info = pd.read_pickle(factor_custom_path)
    for model_config in model_config_dict[model_type]:
        if (model_type in model_custom_params):
            if (model_config[0] in model_custom_params[model_type]):
                custom_params = model_custom_params[model_type][model_config[0]]
            else:
                custom_params = {}
        else:
            custom_params = {}
        print(model_config[0],custom_params)   
        update_single_model(root_path=model_root_path,modelname=model_config[0],strategy_type=model_type,label_name=model_config[2],
                    gap=model_config[3],train_window=model_config[4],sample_flag=model_config[5],factor_list=factor_custom_info[model_type][model_config[0]],
                    today_date=today_date,train_flag=retrain_flag,act_check=True,custom_params=custom_params)
import numpy as np
import xgboost as xgb
import pickle
import pandas as pd
import xgboost as xgb
from lightgbm import LGBMRegressor ,LGBMRanker   
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from scipy.stats import norm
import sys
sys.path.insert(0,'depart_update/model')
import pandas as pd
from sklearn import linear_model
import pickle
import numpy as np
from scipy import stats
def boxcox(y):
    y_pos=y-y.min()+1
    y2,lambda_=stats.boxcox(y_pos)
    y_bp=pd.Series(index=y.index,data=y2)
    return y_bp
def quantile(y):
    y_b3=y[y<y.mean()-4*y.std()].values
    sort_b3=np.sort(y_b3)
    rank_b3_dict={sort_b3[x]:x for x in range(len(y_b3))}

    y_o3=y[y>y.mean()+4*y.std()].values
    sort_o3=np.sort(-y_o3)
    rank_o3_dict={-sort_o3[x]:len(y)-1-x for x in range(len(y_o3))}

    rank_dict=rank_b3_dict
    rank_dict.update(rank_o3_dict)
    def transform(x,y):
        ppf=norm.ppf((rank_dict[x]+0.5)/len(y))
        return y.std()*ppf+y.mean()
    y_ppf=y.apply(lambda x:transform(x,y) if x in rank_dict else x)
    return y_ppf
def normalize(y):
    y_norm=(y-y.mean())/y.std()
    return y_norm
def map_act(y):
    y_bp=boxcox(y)
    y_ppf=quantile(y_bp)
    y_norm=normalize(y_ppf)
    return y_norm

class Lr_Model_IC():
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
        
    def get_model(self, sample, factor_list):
        # df = sample[self._label_name].rank(pct=True)
        # df[df==1] = 1 -1/3676
        # df[df==0] = 1/3676
        # sample[self._label_name] = norm.ppf(df.values)
        datelist = np.sort(np.unique(sample['date'].values))
        sample[self._label_name] = map_act(sample[self._label_name])
        sample = sample[~np.isnan(sample[self._label_name])]
        
        # mu = sample[self._label_name].mean()
        # std = sample[self._label_name].std()
        # up = mu+3*std
        # down = mu-3*std
        # sample.loc[sample[self._label_name]>=up,self._label_name] = up 
        # sample.loc[sample[self._label_name]<=down,self._label_name] = down
        sample_valid = sample[sample['date']<datelist[-4]]
        
        X_train = sample_valid[factor_list]
        y_train = sample_valid[self._label_name]
        model = linear_model.LinearRegression(fit_intercept=True,n_jobs=15)
        # model.fit(X_train,y_train)
        
        IC = sample.groupby('date').apply(lambda x:x[factor_list].corrwith(x['vwap_re_1d'],method='pearson'))
        sign = np.sign(IC.mean())
        IC = IC*sign
        # print(IC.shape)
        ic_std_change = IC.iloc[-20:].std()/IC.iloc[-240:].std()
        ic_down = np.where(IC.values<0,IC.values,np.nan)
        ic_down = pd.DataFrame(ic_down,index=IC.index,columns=IC.columns)
        ic_down_std_change = ic_down.iloc[-20:].std()/ic_down.iloc[-240:].std()
        ind = np.where(~((ic_std_change>=1.2)&(ic_down_std_change>=1.2)))[0]
        print(len(ind))
        model.fit(X_train.iloc[:,ind],y_train)
        coef = model.coef_
        model.coef_ = np.zeros(len(factor_list))
        model.coef_[ind] = coef
        
        filename = self._model_path + 'model.pkl'
        with open(filename, 'wb') as f:
            pickle.dump(obj =model,file= f)

        return 


    def label_predict(self, sample_daily, factor_list):
            
        filename = self._model_path  +'model.pkl'
        with open(filename, 'rb') as f:
            model = pickle.load(file=f)
        # model.coef_[model.coef_>0.02] = 0.02
        # model.coef_[model.coef_<-0.02] = -0.02
        X_test = sample_daily[factor_list]
        y_pred = model.predict(X_test)
        label_pred = pd.Series(data=y_pred,index=sample_daily['stock'].values)
        return label_pred
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
    label = pd.read_pickle('/data/user/013546/rubbish/label_group.pkl').fillna(0)
    if retrain_flag == True:
        all_trading_days = sorted([e[:-4] for e in os.listdir(path_feature)])
        all_trading_days = [e for e in all_trading_days if e <= today_date]
        sample_required_dates = all_trading_days[-lookback_period_max-20 : ]
        sample_feature = []
        sample_label = []
        for day in sample_required_dates:
            df = pd.read_pickle(path_feature+ day + '.pkl')
            sample_feature.append(df)
            df = pd.read_pickle(path_label+ day + '.pkl')
            sample_label.append(df)
        training_sample = pd.concat(sample_feature)
        training_sample = training_sample.merge(pd.concat(sample_label),on=['date','stock'],how='left')
      
        # training_sample = training_sample[['date','stock','vwap_re_1d']+factor_list].merge(label,on=['date','stock'],how='left')
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
date_start = '20190701'
date_end = '20191231'
step = 20
count = 0
lookback_period_max = 240
retrain_flag = True  
root_path = '/data/user/013546/AlphaDataCenter/'
suffix = 'depart_sequence_norm_'+date_start+'_'+date_end+'/'
model_config_list= [
            ('Lr_Model_IC','am','0930_1129_re_5d',1,240)
             ]
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Department/DepartSample/factor_info_new.pkl')['day_factors']
rubbish = ['Vwap_Close_Range_Diff', 'LongBear', 'LongBull', 
'BollingerDown20d', 'ShortBear', 'BollingerUp20d', 
 'ShortBull', 'RankNetProfitDps']
factor_list = sorted(list(set(factor_list)-set(rubbish)))
print('factor list num:',len(factor_list))
path_sample = '/data/group/800020/AlphaDataCenter/Department/DepartSample/Sample/feature/'#
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
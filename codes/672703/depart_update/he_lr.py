import pandas as pd
from sklearn import linear_model
import pickle
import numpy as np
from sklearn.linear_model import LogisticRegression

class LRMulti_Model():
    
    def __init__(self,params):
        self._label_name = params['label_name']
        self._random_seed = 1990
        self._modelname =  params['modelname']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']
        self._new_label_name = 'label_new'
        self.label_range = {'1': [0, 0.1], '2': [0.1, 0.2],  ## short 收益
          '3': [0.8, 0.9], '4': [0.9, 1]}  ## long 收益
        self.class_type = [int(i) for i in self.label_range.keys()]


    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed

    def factor_melt(self,factor, factor_name):
        factor['date'] = factor.index
        factor_m = factor.melt(id_vars='date', var_name='stock', value_name=factor_name)
        factor_m.columns = ['date', 'stock', factor_name]
        return factor_m

    def init_model(self):
        C = 1
        n_jobs = 10
        penalty='l2'
        solver = 'lbfgs'
        random_state = 1
        multi_class = 'multinomial'
        # {'C': 1, 'n_jobs': 4, 'penalty': 'l2', 'solver': 'lbfgs',
        #  'random_state': 1, 'multi_class': 'multinomial'}
        model = LogisticRegression(C=C, solver=solver, n_jobs=n_jobs,penalty=penalty, multi_class=multi_class,random_state=random_state)
        return model

    def get_train_samples(self,all_data, factor_name_list,get_valid_sample=True):
        ## 直接dropna会将有些缺失较为严重的特征对应样本全部剔除，训练问题不大，但预测时该特征会没有值
        train_data = all_data.dropna(axis=0)
        X = train_data[factor_name_list].values.astype(np.float64)
        Y_np = train_data[self._new_label_name].values.astype(np.float64)
        assert np.isnan(X).flatten().sum() == 0, 'X has NaN values'
        assert np.isnan(Y_np).sum() == 0, 'Y_np has NaN values'
        mu = np.nanmean(X, axis=0)
        sigma = np.nanstd(X, axis=0, ddof=1)
        X[:, sigma == 0] = np.subtract(X[:, sigma == 0], mu[sigma == 0])
        X[:, sigma != 0] = np.divide(np.subtract(X[:, sigma != 0], mu[sigma != 0]), sigma[sigma != 0])
        if get_valid_sample:
            train_length = int(len(Y_np)*0.9)
            X_train = X[:train_length,:]
            X_valid = X[train_length:,:]
            Y_np_train = Y_np[:train_length]
            Y_np_valid = Y_np[train_length:]
            return X_train,Y_np_train,X_valid,Y_np_valid
        else:
            return X,Y_np

    def generate_classfier_label(self,ret, label_range):
        ret_rank = ret.rank(pct=True, method='average', ascending=True, axis=1)
        label = pd.DataFrame(np.nan, index=ret_rank.index, columns=ret_rank.columns)
        for k in label_range.keys():
            rank_range = label_range[k]
            assert rank_range[1] > rank_range[0], "please check the 'label_range'"
            label[(ret_rank > rank_range[0]) & (ret_rank <= rank_range[1])] = int(k)
        return label

    def get_model(self, sample, factor_list):
        ret = sample[[self._label_name, 'stock', 'date']]
        ret = ret.pivot(values=self._label_name, columns='stock', index='date')
        label = self.generate_classfier_label(ret=ret, label_range=self.label_range)
        label = self.factor_melt(factor=label, factor_name=self._new_label_name)
        sample = pd.merge(left=sample, right=label, on=['date', 'stock'], how='inner')

        X_train,y_train = self.get_train_samples(sample,factor_list,get_valid_sample=False)
        model = self.init_model()
        model.fit(X_train,y_train)
        
        filename = self._model_path + 'model.pkl'
        with open(filename, 'wb') as f:
            pickle.dump(obj =model,file= f)
        return 


    def label_predict(self, sample_daily, factor_list):
            
        filename = self._model_path  +'model.pkl'
        with open(filename, 'rb') as f:
            model = pickle.load(file=f)

        X = sample_daily[factor_list].values.astype(np.float64)
        mu=np.nanmean(X,axis=0)
        sigma=np.nanstd(X,axis=0)
        X[:,sigma==0]=np.subtract(X[:,sigma==0],mu[sigma==0])
        X[:,sigma!=0]=np.divide(np.subtract(X[:,sigma!=0],mu[sigma!=0]),sigma[sigma!=0])
        X[np.isnan(X)] = 0

        y_pred = model.predict_proba(X)
        predict_result = {}
        for j in self.class_type:
            predict_result[j] = pd.Series(y_pred[:,np.where(model.classes_==j)[0][0]],index=sample_daily['stock'].values)
            assert predict_result[j].isnull().sum()==0,'存在valid stock未给预测值'

        # label_pred = predict_result[4]-predict_result[1]
        label_pred = predict_result
        return label_pred
def update_model_predict(root_path='',path_sample=[],factor_list=[],
            today_date = '20200407',retrain_flag = True,lookback_period_max = 300,
            model_config_list = [
                    ('XgboostReg_Model','vwap','vwap_re_1d',1,240),
                    ('DeepFM_Model','vwap','vwap_re_1d',1,240),
                    ('Lr_Model','vwap','vwap_re_5d',5,240)
                        ],suffix=None):
    t = time.time()
    path_feature = path_sample
    label = pd.read_pickle('/data/user/013546/rubbish/map_act_label.pkl').fillna(0)
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
        # training_sample = training_sample[['date','stock']+factor_list].merge(label,on=['date','stock'],how='left')
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
train_start = '20170101'
date_start = '20180101'
date_end = '20200624'
step = 20
count = 0
lookback_period_max = 240
retrain_flag = True  
root_path = '/data/user/013546/AlphaDataCenter/'
suffix = 'hezq1_'+date_start+'_'+date_end+'/'
model_config_list= [
            ('LRMulti_Model','vwap','vwap_re_1d',1,240)
             ]
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
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
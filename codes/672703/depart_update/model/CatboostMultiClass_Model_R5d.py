import numpy as np
import pickle
import pandas as pd
import copy
import os
import time
from sklearn.model_selection import train_test_split
import sys
import catboost
import multiprocessing as mp


class CatboostMultiClass_Model_R5d():
    
    def __init__(self,params):
        self._label_name = params['label_name']
        self._random_seed = 1990
        self._modelname =  params['modelname']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']
        self._sample_path = params['sample_path']
        self._check_dates = params['check_dates']
        self._weight = params['weight']
        self._time = params['time']
        self.tool_path = '/data/user/013546/AlphaDataCenter/catboost_tool/'



    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed


    def cal_ret(self, weight, model, test_days, factor_list, ret):
        r = []
        for days in test_days:
            
            temp = pd.read_pickle(self._sample_path+ days +'.pkl')
            temp[days] = (np.array(weight)*model.predict_proba(temp[factor_list])).sum(axis=1)                
            temp.index = temp['stock'].values
            temp['return'] = ret.loc[days]
            temp1 = temp.sort_values(by=days,ascending=False).iloc[:int(0.2*temp.shape[0]),:]
            # nums  = int(temp1['return'].size/4.)
            # w = np.array(nums*[0.5]+nums*[0.25]+nums*[0.15]+(temp1['return'].size-3*nums)*[0.1])
            # r.append((temp1['return']*w).sum()/w.sum() - temp['return'].mean())
            r.append(temp1['return'].mean() - temp['return'].mean())
        rr=pd.Series(r,index = test_days)
        sharpe = rr.mean()/rr.std()
        return sharpe, weight


    def get_best_weight(self, weight_list, model, test_days, factor_list,):
        
        base_data_path =  '/data/group/800020/AlphaDataCenter/Basic/'
        if self._time == 'vwap':
            vwap = pd.read_pickle(base_data_path+'/daily/vwap_adj.pkl')
            ret = vwap/vwap.shift(1) - 1
            ret = ret.shift(-4)
        elif self._time == 'am':
            vwap = pd.read_pickle(base_data_path+'/daily/vwap_am_adj_cz.pkl')
            ret = vwap/vwap.shift(1) - 1
            ret = ret.shift(-4)           
        elif self._time == 'pm':
            vwap = pd.read_pickle(base_data_path+'/daily/vwap_pm_adj_cz.pkl')
            ret = vwap/vwap.shift(1) - 1
            ret = ret.shift(-1)            
                        
        sr = []
        w_list = []

        pools = mp.Pool(processes=24)
        tasks = []
        for w in weight_list:
            tasks.append(pools.apply_async(self.cal_ret, (w, model, test_days, factor_list, ret)))
        pools.close()
        pools.join()
        
        error = []
        for t in tasks:
            try:
                cc = t.get()
                sr.append(cc[0])
                w_list.append(cc[1])
            except:
                error.append(0)
                pass
        print('Weight Error: ',len(error))
        best_w = w_list[sr.index(max(sr))]
        return best_w



    def get_model(self, sample, factor_list):

        dates = sorted([str(i.year) + str(i.month).zfill(2) + str(i.day).zfill(2) for i in list(set(sample['date']))])

        try:
            old_weight = np.load(self.tool_path+self._time+'_weight.npy')
            last_date = np.load(self.tool_path+self._time+'_last_date.npy').tolist()[0]
            if last_date <= dates[-1]:
                test_date = self._check_dates
                filename = self._model_path +'model.pkl'
                with open(filename, 'rb') as f:
                    last_model = pickle.load(file=f)
                all_weight = np.load(self.tool_path + '/weights/trial_weights.npy').tolist()
                new_weight = self.get_best_weight(all_weight, last_model, test_date, factor_list)
                np.save(self.tool_path+self._time+'_weight.npy', new_weight)
                print('Weights Renewed.')
            else:
                np.save(self.tool_path+self._time+'_weight.npy', self._weight)
                print('Initialize Weights Again.')
        except FileNotFoundError:
            np.save(self.tool_path+self._time+'_weight.npy', self._weight)
            print('Initialize Weights.')

        np.save(self.tool_path+self._time+'_last_date.npy',[dates[-1]])

        sample = sample[sample[self._label_name].values!=0]

        X_in_sample = sample.loc[:,factor_list]
        y_in_sample = sample.loc[:,self._label_name]
        X_train, X_cv, y_train, y_cv = train_test_split(X_in_sample, y_in_sample, 
            test_size = 0.1, random_state = self._random_seed, stratify = y_in_sample)
        
        print('Train Start.')
        model = catboost.CatBoostClassifier(iterations=3000,thread_count=-1,depth=6,
                                        eval_metric='MultiClassOneVsAll',
                                        random_seed = self._random_seed,
                                        learning_rate = 0.015,
                                        logging_level='Verbose', nan_mode='Forbidden',
                                        loss_function = 'MultiClassOneVsAll',
                                        early_stopping_rounds=10,
                                        l2_leaf_reg = 10,
                                       )
        model.fit(X_train,y_train,eval_set=(X_cv, y_cv),plot=False,verbose=False)
        
        filename = self._model_path +'model.pkl'
        with open(filename, 'wb') as f:
            pickle.dump(obj =model,file= f)

        return

        

    def label_predict(self, sample_daily, factor_list):

        filename = self._model_path +'model.pkl'
        with open(filename, 'rb') as f:
            model = pickle.load(file=f)

        X = sample_daily[factor_list]
        new_weight = np.load(self.tool_path+self._time+'_weight.npy').tolist()
        y_pred = (np.array(new_weight)*model.predict_proba(X)).sum(axis=1)
        prediction = pd.Series(data=y_pred,index=sample_daily['stock'].values)
        return prediction

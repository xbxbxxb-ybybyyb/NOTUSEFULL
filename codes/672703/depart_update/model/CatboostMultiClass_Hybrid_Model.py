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
sys.path.insert(0,'/data/user/013546/AlphaDataCenter/catboost_tool/')
import check_prediction_new as cp



class CatboostMultiClass_Hybrid_Model():
    
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
        self._today = params['today']
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
            nums  = int(temp1['return'].size/4.)
            w = np.array(nums*[0.5]+nums*[0.25]+nums*[0.15]+(temp1['return'].size-3*nums)*[0.1])
            r.append((temp1['return']*w).sum()/w.sum() - temp['return'].mean())
            # r.append(temp1['return'].mean() - temp['return'].mean())
        rr=pd.Series(r,index = test_days)
        sharpe = rr.mean()/rr.std()
        vol = -1.* rr.std()
        negsum = -1.* (rr[rr<0].sum())
        return sharpe, vol, negsum, weight

    def save_data(self,df_update,path):
        if os.path.exists(path):
            store_data = pd.read_pickle(path)
        else:
            store_data = df_update
        if isinstance(df_update,dict):
            for k,v in store_data.items():
                v=v.append(df_update[k])
                v = v.loc[~v.index.duplicated(keep='last')].sort_index()
                store_data[k] = v.astype(np.float64)
        else:
            store_data = store_data.append(df_update).astype(np.float64)
            store_data = store_data.loc[~store_data.index.duplicated(keep='last')].sort_index()
        pd.to_pickle(store_data,path)
        return store_data
    def get_best_weight(self, weight_list, model, test_days_r1, test_days_r3, factor_list,):
        
        base_data_path =  '/data/group/800020/AlphaDataCenter/Basic/'
        if self._time == 'vwap':
            vwap = pd.read_pickle(base_data_path+'/daily/vwap_adj.pkl')
            ret = vwap/vwap.shift(1) - 1
            ret1 = ret.shift(-2)
            ret3 = ret.shift(-4)
        elif self._time == 'am':
            vwap = pd.read_pickle(base_data_path+'/daily/vwap_am_adj_cz.pkl')
            ret = vwap/vwap.shift(1) - 1
            ret1 = ret.shift(-2)
            ret3 = ret.shift(-4)          
        elif self._time == 'pm':
            vwap = pd.read_pickle(base_data_path+'/daily/vwap_pm_adj_cz.pkl')
            ret = vwap/vwap.shift(1) - 1
            ret1 = ret.shift(-1)
            ret3 = ret.shift(-3)            
                        
        sr = []
        vol = []
        w_list = []

        pools = mp.Pool(processes=24)
        tasks = []
        for w in weight_list:
            tasks.append(pools.apply_async(self.cal_ret, (w, model, test_days_r3, factor_list, ret3)))
        pools.close()
        pools.join()
        
        error = []
        for t in tasks:
            try:
                cc = t.get()
                sr.append(cc[0])
                vol.append(cc[1])
                w_list.append(cc[3])
            except:
                error.append(0)
                pass
        print('Weight Error: ',len(error))
        best_sharpe = w_list[sr.index(max(sr))]
        best_vol = w_list[vol.index(max(vol))]

        negsum = []
        w_list1 = []
        pools = mp.Pool(processes=24)
        tasks = []
        for w in weight_list:
            tasks.append(pools.apply_async(self.cal_ret, (w, model, test_days_r1, factor_list, ret1)))
        pools.close()
        pools.join()
        
        error = []
        for t in tasks:
            try:
                cc = t.get()
                negsum.append(cc[2])
                w_list1.append(cc[3])
            except:
                error.append(0)
                pass
        print('Weight Error: ',len(error))
        best_negsum = w_list[negsum.index(max(negsum))]       
        return best_sharpe, best_vol, best_negsum



    def get_model(self, sample, factor_list):

        dates = sorted([str(i.year) + str(i.month).zfill(2) + str(i.day).zfill(2) for i in list(set(sample['date']))])

        try:
            last_date = np.load(self.tool_path+self._time+'_last_date.npy').tolist()[0]
            if last_date <= dates[-1]:
                test_date = self._check_dates
                filename = self._model_path +'model.pkl'
                with open(filename, 'rb') as f:
                    last_model = pickle.load(file=f)
                all_weight = np.load(self.tool_path + '/all_weights.npy').tolist()
                sr, vol, negsum = self.get_best_weight(all_weight, last_model, test_date['r1d'], test_date['r3d'], factor_list)
                np.save(self.tool_path+self._time+'_sharpe_weight.npy', sr)
                np.save(self.tool_path+self._time+'_vol_weight.npy', vol)
                np.save(self.tool_path+self._time+'_negsum_weight.npy', negsum)
                print('Weights Renewed.')
                sr_pred = pd.read_pickle(self.tool_path+self._time+'_sharpe_pred.pkl')
                vol_pred = pd.read_pickle(self.tool_path+self._time+'_vol_pred.pkl')
                negsum_pred = pd.read_pickle(self.tool_path+self._time+'_negsum_pred.pkl')
                if self._time == 'vwap':
                    if sr_pred.shape[0] >= 10:
                        scores = cp.check_prediction_new(sr_pred+vol_pred,'vwap','0930',240,1,20,1,15)
                        last_week_ret = scores.mean(axis=1).iloc[-5:].mean()
                        if last_week_ret < -0.1:
                            np.save(self.tool_path+self._time+'_wflag.npy', [-1])
                        else:
                            np.save(self.tool_path+self._time+'_wflag.npy', [1])
                    else:
                        np.save(self.tool_path+self._time+'_wflag.npy', [1])
                elif self._time == 'am':
                    if sr_pred.shape[0] >= 7:
                        scores = cp.check_prediction_new(sr_pred+vol_pred,'vwap','0930',120,1,20,1,15)
                        last_week_ret = scores.mean(axis=1).iloc[-5:].mean()
                        if last_week_ret < -0.1:
                            np.save(self.tool_path+self._time+'_wflag.npy', [-1])
                        else:
                            np.save(self.tool_path+self._time+'_wflag.npy', [1])
                    else:
                        np.save(self.tool_path+self._time+'_wflag.npy', [1])                           
            else:
                np.save(self.tool_path+self._time+'_sharpe_weight.npy', self._weight)
                np.save(self.tool_path+self._time+'_vol_weight.npy', self._weight)
                np.save(self.tool_path+self._time+'_negsum_weight.npy', self._weight)
                np.save(self.tool_path+self._time+'_wflag.npy', [1])
                print('Initialize Weights Again.')
        except FileNotFoundError:
            np.save(self.tool_path+self._time+'_sharpe_weight.npy', self._weight)
            np.save(self.tool_path+self._time+'_vol_weight.npy', self._weight)
            np.save(self.tool_path+self._time+'_negsum_weight.npy', self._weight)
            np.save(self.tool_path+self._time+'_wflag.npy', [1])
            print('Initialize Weights.')

        np.save(self.tool_path+self._time+'_last_date.npy',[dates[-1]])

        sample = sample[sample[self._label_name].values!=0]

        X_in_sample = sample.loc[:,factor_list]
        y_in_sample = sample.loc[:,self._label_name]
        X_train, X_cv, y_train, y_cv = train_test_split(X_in_sample, y_in_sample, 
            test_size = 0.1, random_state = self._random_seed, stratify = y_in_sample)
        
        print('Train Start.')
        model = catboost.CatBoostClassifier(iterations=2000,thread_count=-1,depth=6,
                                        eval_metric='MultiClassOneVsAll',
                                        random_seed = self._random_seed,
                                        learning_rate = 0.025,
                                        logging_level='Verbose', nan_mode='Forbidden',
                                        loss_function = 'MultiClassOneVsAll',
                                        rsm = 0.66,
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
        # 首先生成各个目标对应的pred，格式标准化并且concat
        sr_weight = np.load(self.tool_path+self._time+'_sharpe_weight.npy').tolist()
        vol_weight = np.load(self.tool_path+self._time+'_vol_weight.npy').tolist()
        negsum_weight = np.load(self.tool_path+self._time+'_negsum_weight.npy').tolist()
        sr_pred = (np.array(sr_weight)*model.predict_proba(X)).sum(axis=1)
        sr_pred = (sr_pred-min(sr_weight)) / (max(sr_weight)-min(sr_weight))
        vol_pred = (np.array(vol_weight)*model.predict_proba(X)).sum(axis=1)
        vol_pred = (vol_pred-min(vol_weight)) / (max(vol_weight)-min(vol_weight))
        negsum_pred = (np.array(negsum_weight)*model.predict_proba(X)).sum(axis=1)
        negsum_pred = (negsum_pred-min(negsum_weight)) / (max(negsum_weight)-min(negsum_weight))
        sr_pred_raw = pd.Series(data=sr_pred, index=sample_daily['stock'].values)
        vol_pred_raw = pd.Series(data=vol_pred, index=sample_daily['stock'].values)
        negsum_pred_raw = pd.Series(data=negsum_pred, index=sample_daily['stock'].values)
 
        self.save_data(sr_pred_raw.to_frame(name = pd.to_datetime(self._today)).T,self.tool_path+self._time+'_sharpe_pred.pkl')
        self.save_data(vol_pred_raw.to_frame(name = pd.to_datetime(self._today)).T,self.tool_path+self._time+'_vol_pred.pkl')
        self.save_data(negsum_pred_raw.to_frame(name = pd.to_datetime(self._today)).T,self.tool_path+self._time+'_negsum_pred.pkl')
    
        # 依据vwap还是am分类
        # 依据wflag决定使用哪一套权重
        if os.path.exists(self.tool_path+self._time+'_wflag.npy'):
            wflag = np.load(self.tool_path+self._time+'_wflag.npy').tolist()[0]
        else:
            wflag = 1
        if self._time == 'vwap':
            y_pred = (sr_pred_raw + vol_pred_raw)/2.
        elif self._time == 'am':
            if wflag == 1:
                y_pred = (sr_pred_raw + vol_pred_raw)/2.
            else:
                y_pred = negsum_pred_raw

        prediction = y_pred
        return prediction

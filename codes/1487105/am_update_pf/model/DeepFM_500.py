import numpy as np
import pandas as pd
import tensorflow as tf
import copy
import random
import datetime as dt
import gc
from ModelDeepFM import *
from sklearn.model_selection import StratifiedKFold
import pickle
import time
import os
import multiprocessing as mlp

class DeepFM_500():

    def __init__(self,params):
        self._label_name = params['label_name']
        self._random_seed = 1990
        self._modelname =  params['modelname']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']
        self.NUM_SPLITS = 3
        try:
            os.makedirs(self._model_path)
        except:
            pass
        try:
            os.makedirs(self._prediction_path)
        except:
            pass          
    
    
    def revise_label(self, label):
        self._label_name = label


    def revise_random_seed(self, seed):
        self._random_seed = seed
        
    def get_model(self, sample, factor_list, dfm_params=None):

        layer_num = 80
        NUM_SPLITS = self.NUM_SPLITS
        norm_label = True
        dates = [str(i.year) + str(i.month).zfill(2) + str(i.day).zfill(2) for i in list(set(sample['date']))]
        dates.sort()

        boundaries = {}
        a = time.time()
        print('Generate boundary dict...')
        pool = mlp.Pool(processes=20)
        task = []
        for factor_name in factor_list:    
            task.append(pool.apply_async(self.Layer_equally_get,(sample[factor_name].copy(),factor_name,layer_num,)))
        pool.close()
        pool.join()
        for t in task:
            boundary,factor_name = t.get()
            boundaries[factor_name] = boundary

        # for factor_name in factor_list:    
        #     boundary = self.Layer_equally_get(sample,factor_name,layer_num)
        #     boundaries[factor_name] = boundary
        with open(self._model_path + 'boundary.pkl','wb') as f1:
            pickle.dump(boundaries,f1)

        factor_all_ = copy.deepcopy(factor_list)
        factor_all_orig = copy.deepcopy(factor_list)
        on_ = ['date','stock',self._label_name] 
        factor_all_.extend(on_)        
        train_date_start = dates[0]
        train_date_end = dates[-1]
        print('train_date_start %s' % train_date_start,'train_date_end %s' % train_date_end)

        data_train = sample[factor_all_]   
        sample_num = data_train.shape[0]
        embedding_size = 64
        nn_layer1_num = int(sample_num/len(factor_list)/embedding_size*0.8)
        if nn_layer1_num % 2 != 0:
            nn_layer1_num+=1
        nn_layer1_num = 6#max(nn_layer1_num,2)
        print('nn_layer1_num: ',nn_layer1_num)             

        data_recode_train_orig = data_train.copy()

        print('# 对 原始因子数据进行等频分组 start')
        t1 = dt.datetime.now()

        pool = mlp.Pool(processes=20)
        task = []
        for factor_name in factor_list:    
            boundary = boundaries[factor_name]
            task.append(pool.apply_async(self.Layer_equally_boundary,(data_train[factor_name].copy(),factor_name,layer_num,boundary,)))
        pool.close()
        pool.join()

        for t in task:
            data_recode_train,factor_name = t.get()
            data_recode_train_orig[factor_name] = data_recode_train
        b = time.time()
        print('###等频分组结束 : ',b-a)
        
        if norm_label:
            t1 = dt.datetime.now()
            print('###norming start###')
            other_info = data_recode_train_orig[['stock','date', self._label_name]]
            data_recode_train = data_recode_train_orig.groupby('date').transform(self.transform_norm)[factor_list]
            data_recode_train = pd.concat([data_recode_train, other_info], axis = 1)
            # data_train = Norm(data_train,date_train)
            t2 = dt.datetime.now()
            print('###norming end###:',t2-t1)
        else:
            data_recode_train = data_recode_train_orig

        # try:
        #     data_recode_train.drop('date',axis=1,inplace=True)
        #     data_train.drop('date',axis=1,inplace=True)
        # except KeyError:
        #     pass

        data_train = data_train.reindex(columns=sorted(data_train.columns))
        data_recode_train = data_recode_train.reindex(columns=sorted(data_train.columns))
        data_train_all = data_recode_train.append(data_train)
        data_train_all.fillna(0,inplace=True)

        del data_train
        # del X_train
        gc.collect()

        np.random.seed(self._random_seed)
        np.random.shuffle(factor_all_orig)

        dates = sample['date'].unique().tolist()
        dates = sorted(dates)
        for i in range(NUM_SPLITS):
            # 240
            if i == 0:
                factor_list_ = factor_all_orig[:int(len(factor_all_orig)/5*4)]
#                print(i,factor_list_[:5])

                train_dates = dates[:80]
                validation_dates = dates[85:]
            elif i == 1:
                factor_list_ = factor_all_orig[int(len(factor_all_orig)/10*1):int(len(factor_all_orig)/10*9)]
#                print(i,factor_list_[:5])
                train_dates = dates[80:160]
                validation_dates = dates[:75] + dates[165:]
            elif i == 2:
                factor_list_ = factor_all_orig[-int(len(factor_all_orig)/5*4):]
#                print(i,factor_list_[:5])
                train_dates = dates[-80:]
                validation_dates = dates[:-75]

            # if i == 0:
            #     train_dates = dates[:160]
            #     validation_dates = dates[180:]
            # elif i == 1:
            #     train_dates = dates[80:]
            #     validation_dates = dates[:60]# + dates[200:]


            # 360
            # if i == 0:
            #     train_dates = dates[:180]
            #     validation_dates = dates[200:]
            # elif i == 1:
            #     train_dates = dates[90:270]
            #     validation_dates = dates[:70] + dates[290:]
            # elif i == 2:
            #     train_dates = dates[-180:]
            #     validation_dates = dates[:-200]

            # 480
            # if i == 0:
            #     train_dates = dates[:240]
            #     validation_dates = dates[260:]
            # elif i == 1:
            #     train_dates = dates[120:360]
            #     validation_dates = dates[:100] + dates[380:]
            # elif i == 2:
            #     train_dates = dates[-240:]
            #     validation_dates = dates[:-260]                
            
            # train_dates = dates[i*80:(i+1)*80]
            # try:
            #     validation_dates =  dates[i+1*80:]#sorted(list(set(dates)-set(train_dates)))
            # except:
            #     print('last sub_model',i)    
            #     validation_dates =  sorted(list(set(dates)-set(train_dates)))
            #     validation_dates = validation_dates[:-20]

            train_ = data_train_all[data_train_all['date'].isin(train_dates)].copy()  
            Xv_train_all_ = train_[factor_list_].values.tolist()
            y_train_all_ = train_[self._label_name].values.tolist()

            valid_ = data_train_all[data_train_all['date'].isin(validation_dates)].copy()  
            Xv_valid_all_ = valid_[factor_list_].values.tolist()
            y_valid_all_ = valid_[self._label_name].values.tolist()
            print('train_:',train_.shape,'valid_',valid_.shape)

        
        # _get = lambda x, l: [x[i] for i in l]
        # for i, (train_idx, valid_idx) in enumerate(folds):
        #     Xv_train_all_, y_train_all_ = _get(Xv_train_all, train_idx), _get(y_train_all, train_idx)
        #     Xv_valid_all_, y_valid_all_ = _get(Xv_train_all, valid_idx), _get(y_train_all, valid_idx)
            
            t = time.time()
            # ------------------ DeepFM Model ------------------
            # params
            em_size=32
            dfm_params = {
                 "use_fm": True,
                 "use_deep": True,
                 "embedding_size": 16, #16 better
                 "dropout_fm": [0.5, 0.5], # [1,1]
                 "deep_layers": [int(em_size/2),em_size,em_size,int(em_size/2)],#[16, 32, 32, 16],#[em_size,em_size,em_size,16],#[16, 32, 32, 16], #[int(nn_layer1_num), 16, embedding_size]
                 "dropout_deep": [0.5, 0.5, 0.5, 0.5,0.5],#[0.5, 0.5, 0.5, 0.5],#[0.6, 0.6, 0.6, 0.6],
                 "deep_layers_activation": tf.nn.relu,
                 "epoch": 5, # 30
                 "batch_size": 2048,   #2048
                 "learning_rate": 0.0009,  # can use a bigger as lr0,then decay
                 "optimizer_type": "adam",
                 "batch_norm": 1,
                 "batch_norm_decay": 0.995,
                 "l2_reg": 0.99,#0.95 #0.9
                 "l1_reg": 0.4,#0.001 #0.0001 #0.000001
                 "verbose": True,
                 "loss_type":'mse',
                 "optimizer_type":"adam",
            }                  
  

            dfm_params["random_seed"] = self._random_seed
            dfm_params["label_do"] = self._label_name
            dfm_params["feature_size"] = len(factor_list_)#len(Xv_train_all[0])
            dfm_params["field_size"] = len(factor_list_)#data_train_all.shape[0]#len(Xv_train_all[0])

            if dfm_params["use_fm"] and dfm_params["use_deep"]:
                clf_str = "DeepFM"
            elif dfm_params["use_fm"]:
                clf_str = "FM"
            elif dfm_params["use_deep"]:
                clf_str = "DNN"  
            else:
                clf_str = "LR"

            print('feature_size %s, field_size %s' % (str(dfm_params["feature_size"]),str(dfm_params["field_size"])))

            dfm = ModelDeepFM(**dfm_params)
            # if i == NUM_SPLITS-1:
            #     refit_label = True
            # else:
            #     refit_label = False

            dfm.fit(Xv_train_all_, y_train_all_, Xv_valid_all_, y_valid_all_,i,clf_str, early_stopping=True, refit=False)
            # save model
            dfm.saver.save(dfm.sess,self._model_path,global_step=i)
            print('########################################### %s training use time: ' % str(i), time.time()-t )
        return

    def label_predict(self,sample_daily, factor_list):    
        print(self._model_path)
        vwap_boundary_dict = pd.read_pickle(self._model_path + 'boundary.pkl')
        data_recode_test_orig = copy.deepcopy(sample_daily)
        layer_num = 80
        for factor_name in factor_list:
        #     print(factor_name)
            boundary_ = vwap_boundary_dict[factor_name]
            boundary,data_recode_test1 = self.Layer_equally_daily_boundary(sample_daily,factor_name,layer_num,boundary_)  
            data_recode_test_orig[factor_name] = (data_recode_test1 - data_recode_test1.mean())/data_recode_test1.std()
        data_recode_test_orig.fillna(0,inplace=True)    
        data_recode_test_orig=data_recode_test_orig[factor_list]

        data_recode_test_orig.astype('float')
        data_recode_test_orig[np.isnan(data_recode_test_orig)] = 0
        factor_list_orig = copy.deepcopy(factor_list)
        np.random.seed(self._random_seed)
        np.random.shuffle(factor_list_orig)
        
        pred_label_ = pd.DataFrame(np.zeros(len(sample_daily)),index=sample_daily['stock'].values)[0]
        pred_label_list = []
        for i in range(self.NUM_SPLITS):
            if i == 0:
                factor_list_ = factor_list_orig[:int(len(factor_list_orig)/5*4)]
#                print(i,factor_list_[:5])
            elif i == 1:
                factor_list_ = factor_list_orig[int(len(factor_list_orig)/10*1):int(len(factor_list_orig)/10*9)]
#                print(i,factor_list_[:5])
            elif i == 2:
                factor_list_ = factor_list_orig[-int(len(factor_list_orig)/5*4):]
#                print(i,factor_list_[:5])

            X_test = data_recode_test_orig[factor_list_].values
            Xv_test_all = X_test.tolist()

            print('Num %s model' % str(i))
            tf.reset_default_graph()
            sess = tf.Session() 
            sess.run(tf.global_variables_initializer())
            graph = tf.get_default_graph()
            saver = tf.train.import_meta_graph(self._model_path + '-%s.meta' % i)
            saver.restore(sess,self._model_path + '-%s' % i) # 注意路径写法
            feat_value = graph.get_tensor_by_name("feat_value:0")
            label = graph.get_tensor_by_name("label:0")
            dropout_keep_fm = graph.get_tensor_by_name("dropout_keep_fm:0")
            dropout_keep_deep = graph.get_tensor_by_name("dropout_keep_deep:0")
            train_phase = graph.get_tensor_by_name("train_phase:0")
            predict = graph.get_tensor_by_name("predict:0")

            feed_dict={feat_value:Xv_test_all,label:np.zeros((len(Xv_test_all),1)),\
                       dropout_keep_fm:[1,1],dropout_keep_deep:[1,1,1,1,1],\
                      train_phase:False}

            y_pred_test = predict.eval(feed_dict=feed_dict,session=sess)
            pred_label = pd.DataFrame(y_pred_test,index=sample_daily['stock'].values)[0]
            pred_label_list.append(pred_label)
            pred_label_ += pred_label
            sess.close()

        pred_label_ = pred_label_/self.NUM_SPLITS
        return pred_label_

    def Layer_equally_daily_boundary(self, data_test,factor_name,layer_num,boundary):
        # 根据CDF等频率分组
        # 输出的分组序号保持和原始值一致单调性
        # 全局去极值    
        # 等频分组
        # 计算分组边界
        if len(boundary)!=layer_num-1: 
            print('Error! check frequency bounday!')

        data_arr = copy.deepcopy(data_test[factor_name].values)
        data_orig = copy.deepcopy(data_arr)
        data = copy.deepcopy(data_arr)
        for i in range(0,layer_num-1):
            if i == 0:
                boundary_lower = -np.inf
                boundary_upper = boundary[i]        
            else:
                boundary_lower = boundary[i-1]
                boundary_upper = boundary[i]    
            data[(data_orig>boundary_lower).T & (data_orig<=boundary_upper).T] = i    
    #         print(i,boundary_lower,boundary_upper)
        boundary_lower = boundary[i]
        boundary_upper = np.inf            
    #     print(boundary_lower,boundary_upper)
        data[(data_orig>boundary_lower).T & (data_orig<=boundary_upper).T] = i+1
        data_arr = copy.deepcopy(data)  
        # data_recode_train = data_arr[:train_len]
        data_recode_test = data_arr
        # data_filter_mad = copy.deepcopy(data_filter)
        return boundary,data_recode_test

    def transform_norm(self, data):
        data = data.subtract(data.mean()).divide(data.std())
        return data

    def Layer_equally_get(self, data_train,factor_name,layer_num):
        # 根据CDF等频率分组
        # 输出的分组序号保持和原始值一致单调性
        # 全局去极值    
        # 等频分组
        # 计算分组边界
        values = data_train.values
        values = values[~np.isnan(values)]
        values_pd = pd.DataFrame(values.T)
        boundary = values_pd.describe(percentiles=[i/layer_num for i in range(1,layer_num)])[4:-1][0].values
        boundary = list(boundary)
        return boundary,factor_name

    def Layer_equally_boundary(self, data_train_,factor_name,layer_num,boundary):

        if len(boundary)!=layer_num-1: 
            print('Error! check frequency bounday!')
        # 根据边界对数据重新编码

        data_orig = data_train_.values
        data = copy.deepcopy(data_orig)
        for i in range(0,layer_num-1):
            if i == 0:
                boundary_lower = -np.inf
                boundary_upper = boundary[i]        
            else:
                boundary_lower = boundary[i-1]
                boundary_upper = boundary[i]    
            data[(data_orig>boundary_lower).T & (data_orig<=boundary_upper).T] = i    
    #         print(i,boundary_lower,boundary_upper)
        boundary_lower = boundary[i]
        boundary_upper = np.inf            
    #     print(boundary_lower,boundary_upper)
        data[(data_orig>boundary_lower).T & (data_orig<=boundary_upper).T] = i+1

        return data,factor_name
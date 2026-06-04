import numpy as np
import pandas as pd
import tensorflow as tf
import copy
import random
import datetime as dt
import gc
import tensorflow as tf
from ModelDeepFM import DeepFM
from sklearn.model_selection import StratifiedKFold
import pickle
import time
import os

class DeepFM_Model():
    
    def __init__(self):
        self._label_name = '1300_1459_re_1d'
        self._random_seed = 1990
        self._modelname =  'DeepFM_'+ self._label_name
        self._model_path = '/data/group/800020/AlphaDataCenter/Models/'+self._modelname+'/'
        self._prediction_path = '/data/group/800020/AlphaDataCenter/DailyPrediction/pm/'+self._modelname+'/'
        self.NUM_SPLITS = 3
        try:
            os.makedirs(self._model_path)
        except:
            pass
        try:
            os.makedirs(self._prediction_path)
        except:
            pass
    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed
        
    def get_model(self, sample, factor_list):

        layer_num = 80
        NUM_SPLITS = self.NUM_SPLITS
        norm_label = True
        dates = [str(i.year) + str(i.month).zfill(2) + str(i.day).zfill(2) for i in list(set(sample['date']))]
        dates.sort()

        boundaries = {}
        print('Generate boundary dict...')
        for factor_name in factor_list:    
            boundary = self.Layer_equally_get(sample,factor_name,layer_num)
            boundaries[factor_name] = boundary
        with open(self._model_path + 'boundary.pkl','wb') as f1:
            pickle.dump(boundaries,f1)

        factor_all_ = copy.deepcopy(factor_list)
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

        for factor_name in factor_list:
            boundary = boundaries[factor_name]
            data_recode_train = self.Layer_equally_boundary(data_train,factor_name,layer_num,boundary)
            data_recode_train_orig[factor_name] = data_recode_train - int(layer_num/2)
        
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

        try:
            data_recode_train.drop('date',axis=1,inplace=True)
            data_train.drop('date',axis=1,inplace=True)
        except KeyError:
            pass

        data_train = data_train.reindex(columns=sorted(data_train.columns))
        data_recode_train = data_recode_train.reindex(columns=sorted(data_train.columns))
        data_train_all = data_recode_train.append(data_train)
        data_train_all.fillna(0,inplace=True)
        X_train = data_train_all[factor_list].values
        y_train = data_train_all[self._label_name].values
        folds = list(StratifiedKFold(n_splits= NUM_SPLITS, shuffle=True,random_state=self._random_seed).split(X_train, y_train.reshape(len(y_train),1).argmax(1)))    

        t1 = dt.datetime.now()
        Xv_train_all = X_train.tolist()
        y_train_all = y_train.tolist()
        t2 = dt.datetime.now()
        print('###to list done###:',t2-t1)

        del data_train_all
        del data_train
        del X_train
        gc.collect()
        
        _get = lambda x, l: [x[i] for i in l]
        for i, (train_idx, valid_idx) in enumerate(folds):
            Xv_train_all_, y_train_all_ = _get(Xv_train_all, train_idx), _get(y_train_all, train_idx)
            Xv_valid_all_, y_valid_all_ = _get(Xv_train_all, valid_idx), _get(y_train_all, valid_idx)
            
            t = time.time()
            # ------------------ DeepFM Model ------------------
            # params
            dfm_params = {
                "use_fm": True,
                "use_deep": True,
                "embedding_size": 16, #16 better
                "dropout_fm": [0.5, 0.6], # [1,1]
                "deep_layers": [int(nn_layer1_num), 32, embedding_size], #[16, 32, 64]
                "dropout_deep": [0.6, 0.6, 0.6, 0.6],
                "deep_layers_activation": tf.nn.relu,
                "epoch": 5, # 30
                "batch_size": 2048,   # 1024
                "learning_rate": 0.001,  # can use a bigger as lr0,then decay
                "optimizer_type": "adam",
                "batch_norm": 1,
                "batch_norm_decay": 0.995,
                "l2_reg": 0.9, #0.01
                "l1_reg": 0.000001, #0.01
                "verbose": True,
                "loss_type":'mse',
                "random_seed": self._random_seed,
                "optimizer_type":"adam",
                "label_do":self._label_name
            }

            dfm_params["feature_size"] = len(Xv_train_all[0])
            dfm_params["field_size"] = len(Xv_train_all[0])

            if dfm_params["use_fm"] and dfm_params["use_deep"]:
                clf_str = "DeepFM"
            elif dfm_params["use_fm"]:
                clf_str = "FM"
            elif dfm_params["use_deep"]:
                clf_str = "DNN"  
            else:
                clf_str = "LR"

            print('feature_size %s, field_size %s' % (str(dfm_params["feature_size"]),str(dfm_params["field_size"])))

            dfm = DeepFM(**dfm_params)
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

        X_test = data_recode_test_orig.values
        Xv_test_all = X_test.tolist()
        pred_label_ = pd.DataFrame(np.zeros(len(sample_daily)),index=sample_daily['stock'].values)[0]
        for i in range(self.NUM_SPLITS):
            print('Num %s model' % str(i))
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
                       dropout_keep_fm:[1,1],dropout_keep_deep:[1,1,1,1],\
                      train_phase:False}

            y_pred_test = predict.eval(feed_dict=feed_dict,session=sess)
            pred_label = pd.DataFrame(y_pred_test,index=sample_daily['stock'].values)[0]
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
        values = data_train[factor_name].values
        values = values[~np.isnan(values)]
        values_pd = pd.DataFrame(values.T)
        boundary = values_pd.describe(percentiles=[i/layer_num for i in range(1,layer_num)])[4:-1][0].values
        boundary = list(boundary)
        return boundary

    def Layer_equally_boundary(self, data_train,factor_name,layer_num,boundary):

        if len(boundary)!=layer_num-1: 
            print('Error! check frequency bounday!')
        # 根据边界对数据重新编码

        data_orig = data_train[factor_name].values
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

        return data
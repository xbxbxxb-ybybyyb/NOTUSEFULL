import sys
import copy
import os
from keras import models
from keras.callbacks import ModelCheckpoint,EarlyStopping
from sklearn.model_selection import StratifiedKFold
import numpy as np
from sklearn.model_selection import KFold,StratifiedKFold
import numpy as np
import random as rn
import tensorflow as tf
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

import keras
from keras.layers import Input, Embedding, Dense, Flatten
from keras.layers import Concatenate, dot, Activation, Reshape
from keras.layers import Dense, Activation, Flatten, Convolution1D, Dropout
from keras.layers import BatchNormalization, concatenate, Dropout, Add
from keras.layers import RepeatVector, merge, Subtract, Lambda, Multiply
from keras.models import Model
from keras.regularizers import l2 as l2_reg
from keras.regularizers import l1_l2 as l1_l2
#from keras import initializations
import itertools
from keras import backend  as K
from keras.engine.topology import Layer
from keras.metrics import categorical_accuracy
from keras.optimizers import Adam
from sklearn.metrics import mean_squared_error
import keras.backend.tensorflow_backend as KTF
from config_path import *
os.environ["CUDA_VISIBLE_DEVICES"] = "0"#,1,2,3,4
os.environ['TF_CPP_MIN_LOG_LEVEL']='1'
config = tf.ConfigProto()
config.gpu_options.allow_growth=True   #不全部占满显存, 按需分配
config.gpu_options.per_process_gpu_memory_fraction = 0.3
sess = tf.Session(config=config)
KTF.set_session(sess)
np.random.seed(42)
rn.seed(42)
tf.set_random_seed(42)


class MySumLayer(Layer):
    def __init__(self, axis, **kwargs):
        self.supports_masking = True
        self.axis = axis
        super(MySumLayer, self).__init__(**kwargs)

    def compute_mask(self, input, input_mask=None):
        # do not pass the mask to the next layers
        return None

    def call(self, x, mask=None):
        if mask is not None:
            # mask (batch, time)
            mask = K.cast(mask, K.floatx())
            if K.ndim(x)!=K.ndim(mask):
                mask = K.repeat(mask, x.shape[-1])
                mask = tf.transpose(mask, [0,2,1])
            x = x * mask
            if K.ndim(x)==2:
                x = K.expand_dims(x)
            return K.sum(x, axis=self.axis)
        else:
            if K.ndim(x)==2:
                x = K.expand_dims(x)
            return K.sum(x, axis=self.axis)

    def compute_output_shape(self, input_shape):
        output_shape = []
        for i in range(len(input_shape)):
            if i!=self.axis:
                output_shape.append(input_shape[i])
        if len(output_shape)==1:
            output_shape.append(1)
        return tuple(output_shape)
    def get_config(self):    
        config = {
            'axis': self.axis    
        }    
        base_config = super(MySumLayer, self).get_config()    
        return dict(list(base_config.items()) + list(config.items()))        


class ModelDeepFM(BaseEstimator, TransformerMixin):
    def __init__(self, feature_size, field_size, k=8, 
                dropout_keep_fm=[1.0, 1.0, 1.0],
                deep_layers=[32, 32, 1], 
                dropout_keep_deep=[0.5, 0.5, 0.5],
                epoch=10, batch_size=256,
                learning_rate=0.001, optimizer_type='adam',
                verbose=1, random_seed=2016,
                use_fm=True, use_deep=True,
                loss_type='logloss', eval_metric='auc',
                l2=0.0, l1=0,l2_fm=0.0, 
                log_dir = './output', bestModelPath = './output/keras.model',
                greater_is_better = True, decay=0,use_first=True,Train_label=True, cn_label=True, model_n=2,
                label_ts=False,activation_name='tanh',kernel_initializer_name='glorot_normal',factor_drop_ratio=0,
                em_initial_ones = False, use_fm_last = False
                ):
        # assert (use_fm or use_deep)
        assert loss_type in ['logloss', 'mse', 'mae','ranking_logloss','coef'], \
            'loss_type can be either "logloss" for classification task or "mse" for regression task or "ranking_logloss" for ranking task'

        self.feature_size = feature_size        # denote as M, size of the feature dictionary
        self.field_size = field_size            # denote as F, size of the feature fields
        self.k = k    # denote as K, size of the feature embedding

        self.dropout_keep_fm = dropout_keep_fm
        self.deep_layers = deep_layers
        self.dropout_keep_deep = dropout_keep_deep

        self.use_fm = use_fm
        self.use_deep = use_deep
        self.use_first = use_first

        self.verbose = verbose
        self.epoch = epoch
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.optimizer_type = optimizer_type

        self.seed = random_seed
        self.loss_type = loss_type
        self.eval_metric = eval_metric

        self.l2 = l2
        self.l1 = l1
        self.l2_fm = l2_fm
        
        self.model_n = model_n

        self.bestModelPath = bestModelPath
        self.log_dir = log_dir

        self.greater_is_better = greater_is_better
        self.decay = decay
        self.cn_label = cn_label
        self.activation = activation_name
        self.kernel_initializer_name = kernel_initializer_name
        self.factor_drop_ratio = factor_drop_ratio
        self.em_initial_ones  = em_initial_ones
        self.use_fm_last = use_fm_last

        self._init_graph()

    def correlation_coefficient_loss(self, y_true, y_pred):
        x = y_true
        y = y_pred
        mx = K.mean(x)
        my = K.mean(y)
        xm, ym = x-mx, y-my
        r_num = K.sum(tf.multiply(xm,ym))
        r_den = K.sqrt(tf.multiply(K.sum(K.square(xm)), K.sum(K.square(ym))))
        r = -r_num / r_den
        return r        

    def _init_graph(self):

        np.random.seed(self.seed)
        tf.set_random_seed(self.seed)
        glorot = 0.02
        if self.kernel_initializer_name == 'glorot_normal':
            kernel_initial = keras.initializers.TruncatedNormal(mean=0.0, stddev=glorot, seed=self.seed)

        self.feat_value_ = Input(shape=(self.field_size,))
        self.feat_value = Dropout(self.dropout_keep_fm[2], seed=self.seed, name='feat_value',input_shape=(self.field_size,))(self.feat_value_)
        feat_value = Reshape((self.field_size, 1))(self.feat_value) #None*F*1
        ###----first order------######
        self.y_first_order = self.feat_value    
    
        ##deep 
        if self.em_initial_ones:
            self.y_deep = Dropout(self.dropout_keep_deep[0], seed=self.seed)(self.y_first_order)# # None*(F*k)

        input_size = self.feature_size * self.k        
        self.y_deep_ = []
        for i in range(0, len(self.deep_layers)):    
            if self.deep_layers[i]>0:
                self.y_deep = Dense(self.deep_layers[i], activation=None,kernel_regularizer=keras.regularizers.l1_l2(l2=self.l2,l1=self.l1),\
                    kernel_initializer=kernel_initial)(self.y_deep)
                self.y_deep = BatchNormalization()(self.y_deep,training=False)
                self.y_deep = Activation(self.activation)(self.y_deep)#'relu','tanh'
                self.y_deep = Dropout(self.dropout_keep_deep[i+1], seed=self.seed)(self.y_deep) #None*32
                self.y_deep_.append(self.y_deep)
            
        self.y_first_order = Dropout(self.dropout_keep_fm[0], seed=self.seed,name='y_first_order')(self.y_first_order)
        #deepFM
        self.concat_y = Concatenate()([self.y_first_order] + self.y_deep_) 
        input_size = self.feature_size  + np.array(self.deep_layers).sum()
            # self.concat_y = self.y_first_order
            # input_size = self.feature_size
        print('Final Output shape:',input_size)
        glorot = np.sqrt(2.0 / (input_size + 1))
        self.y = Dense(1, name='main_output',kernel_regularizer=keras.regularizers.l1_l2(l2=self.l2,l1=self.l1),\
        kernel_initializer=keras.initializers.TruncatedNormal(mean=0.0, stddev=glorot, seed=self.seed))(self.concat_y) #None*1
        if self.dropout_keep_fm[2] == 0:
            self.model = Model(inputs=self.feat_value, outputs=self.y, name='model')
        else:
            self.model = Model(inputs=self.feat_value_, outputs=self.y, name='model')
        print('optimizer_type',self.optimizer_type)
        if self.optimizer_type == 'adam':
            self.optimizer = Adam(lr=self.learning_rate, decay=self.decay)#decay=0.0001
 
        if self.loss_type == 'coef':
            self.loss = self.correlation_coefficient_loss#'mean_squared_error'
            self.metrics = self.correlation_coefficient_loss
            greater_is_better=False
            print('use coef')    

        self.model.compile(optimizer=self.optimizer,
                loss=self.loss, metrics=[self.metrics])


import numpy as np
import random as rn
import tensorflow as tf
import pandas as pd
import datetime
import os
def get_trade_date(start_date, window):
    is_valid = pd.read_pickle(basic_daily_path + 'is_valid.pkl')
    if type(window) == type(start_date):
        return is_valid.loc[start_date:window].index
    elif window > 0:
        return is_valid.loc[start_date:].iloc[:window].index
    else:
        return is_valid.loc[:start_date].iloc[window:].index
class XModel(object):  
    def get_quct(self,sample,fs,n_bins=80):
        ranked = (sample[fs].fillna(0).rank(method='first'))
        qcuted = ranked.apply(pd.qcut,args=(n_bins,list(range(n_bins))))
        f=lambda x:(x-x.mean())/x.std()
        qcuted_norm = (qcuted.astype('float')).apply(f)
        qcuted_norm[['stock','date']]=sample[['stock','date']]
        return qcuted_norm    
    def get_sample(self,dates=None,label_name='',factor_info={},dfm_params=None,label_qcut=False):#@label_qcut=True
        if isinstance(dates,list):
            dates= [i for i in dates if i>='20160101']            
        factor_list = factor_info['factors']
        timepoint = factor_info['timepoint']
        # hf
        if timepoint in ['0930','1000','1030','1100','1300','1330','1400','1430']:
            timepoint_depart_sample_path = factor_info['fix_sample_path']
            print('timepoint_depart_sample_path',timepoint_depart_sample_path)            
            if dates==None:
                sample = None
            elif not isinstance(dates,list):
                today_date = dates
                pre_day = get_trade_date(today_date,-2)[-2].strftime('%Y%m%d')
                sample_daily_depart = pd.read_pickle(day_depart_feature_path+pre_day+'.pkl')[['stock']+factor_info['depart_day_factors']]
                sample_daily_own = pd.read_pickle(sample_norm_path+ pre_day + '.pkl')[['stock']+factor_info['own_day_factors']]
                if len(factor_info['extend_factors'])>0:
                    sample_daily_extend = pd.read_pickle(extend_sample_path+ pre_day + '.pkl')[['stock']+factor_info['extend_factors']]
                    sample_daily_depart = sample_daily_depart.merge(sample_daily_extend,on=['stock'],how='left')                  
                if timepoint!='0930':
                    sample_fix = pd.read_pickle(timepoint_depart_sample_path+'feature/'+today_date+'.pkl')[['date','stock']+factor_info['fix_factors']]
                    sample = sample_fix.merge(sample_daily_depart.merge(sample_daily_own,on=['stock'],how='left'),on=['stock'],how='left')
                else:
                    sample = sample_daily_depart.merge(sample_daily_own,on=['stock'],how='left')
                    sample['date'] = pd.to_datetime(today_date)
                if label_qcut is True:     
                    sample = self.get_quct(sample,factor_list)
            else:
                sample_feature = []
                sample_label = []
                for day in dates:
                    pre_day = get_trade_date(day,-2)[-2].strftime('%Y%m%d')
                    df0 = pd.read_pickle(day_depart_feature_path+ pre_day + '.pkl')[['stock']+factor_info['depart_day_factors']]
                    df1 = pd.read_pickle(sample_norm_path+ pre_day + '.pkl')[['stock']+factor_info['own_day_factors']]
                    if len(factor_info['extend_factors'])>0:
                        sample_daily_extend = pd.read_pickle(extend_sample_path+ pre_day + '.pkl')[['stock']+factor_info['extend_factors']]
                        df0 = df0.merge(sample_daily_extend,on=['stock'],how='left')                                    
                    if timepoint!='0930':
                        try:
                            df2 = pd.read_pickle(timepoint_depart_sample_path+'feature/'+day+'.pkl')[['date','stock']+factor_info['fix_factors']]
                        except:
                            continue
                        df = df0.merge(df1,on=['stock'],how='left').merge(df2,on=['stock'],how='left')
                        if label_qcut is True: 
                            df = self.get_quct(df,factor_list)
                        sample_feature.append(df)
                    else:
                        df = df0.merge(df1,on=['stock'],how='left')
                        df['date'] = pd.to_datetime(day)
                        if label_qcut is True: 
                            df = self.get_quct(df,factor_list)
                        sample_feature.append(df)
                    df3 = pd.read_pickle(timepoint_depart_sample_path+'label/'+ day + '.pkl')[['date','stock',label_name]]
                    # if dfm_params['loss_type'] == 'logloss':
                    #     df3 = df3[df3[label_name]!=0]
                    #     df3[label_name][df3[label_name].values>1]=1
                    #     df3[label_name][df3[label_name].values<1]=0                        
                    sample_label.append(df3)
                    
                sample = pd.concat(sample_feature)
                sample = sample.merge(pd.concat(sample_label),on=['date','stock'],how='left')
                print('......................')   
                sample = sample[~np.isnan(sample[label_name])]
        else:
            #vwap
            timepoint_depart_sample_path = depart_sample_path + '/Sample/'
            print('timepoint_depart_sample_path',timepoint_depart_sample_path)            
            if dates==None:
                sample = None
            elif not isinstance(dates,list):
                today_date = dates
                sample_daily_depart = pd.read_pickle(day_depart_feature_path+today_date+'.pkl')[['stock']+factor_info['depart_day_factors']]
                sample_daily_own = pd.read_pickle(sample_norm_path+ today_date + '.pkl')[['stock']+factor_info['own_day_factors']]
                sample = sample_daily_depart.merge(sample_daily_own,on=['stock'],how='left')
                if len(factor_info['extend_factors'])>0:
                    sample_daily_extend = pd.read_pickle(extend_sample_path+ today_date + '.pkl')[['stock']+factor_info['extend_factors']]
                    sample = sample.merge(sample_daily_extend,on=['stock'],how='left')                
                sample['date'] = pd.to_datetime(today_date)     
            else:
                sample_feature = []
                sample_label = []
                for day in dates:
                    df0 = pd.read_pickle(day_depart_feature_path+ day + '.pkl')[['stock']+factor_info['depart_day_factors']]
                    df1 = pd.read_pickle(sample_norm_path+ day + '.pkl')[['stock']+factor_info['own_day_factors']]
                    df = df0.merge(df1,on=['stock'],how='left')
                    if len(factor_info['extend_factors'])>0:
                        sample_daily_extend = pd.read_pickle(extend_sample_path+ day + '.pkl')[['stock']+factor_info['extend_factors']]
                        df = df.merge(sample_daily_extend,on=['stock'],how='left')                                    
                    df['date'] = pd.to_datetime(day)
                    sample_feature.append(df)
                    if label_name == 'vwap_re_3_5_10d':
                        df3 = pd.read_pickle(timepoint_depart_sample_path+'label/'+ day + '.pkl')[['date','stock','vwap_re_3d','vwap_re_5d','vwap_re_10d']]
                        df3[label_name]=df3[['vwap_re_3d','vwap_re_5d','vwap_re_10d']].mean(axis=1)
                        df3[label_name]=(df3[label_name]-df3[label_name].mean())/(df3[label_name].std())
                    elif label_name == 'vwap_re_5_10_20d':
                        df3 = pd.read_pickle(timepoint_depart_sample_path+'label/'+ day + '.pkl')[['date','stock','vwap_re_20d','vwap_re_5d','vwap_re_10d']]
                        df3[label_name]=df3[['vwap_re_20d','vwap_re_5d','vwap_re_10d']].mean(axis=1)
                        df3[label_name]=(df3[label_name]-df3[label_name].mean())/(df3[label_name].std()) 
                    elif label_name in ['vwap_neu_re_5d','vwap_neu2_re_5d']:
                        df3 = []
                    else:
                        df3 = pd.read_pickle(timepoint_depart_sample_path+'label/'+ day + '.pkl')[['date','stock',label_name]]                    
                    sample_label.append(df3)
                if label_name == 'vwap_neu_re_5d':
                    sample_label = pd.read_pickle('/data/user/012620/AlphaData/label_size_industry_beta500_momentum.pkl')                    
                    print('vwap_neu_re_5d')
                elif label_name == 'vwap_neu2_re_5d':
                    sample_label = pd.read_pickle('/data/user/012620/AlphaData/demean_standard_just_resid_indus_size.pkl')                    
                    print('vwap_neu2_re_5d')                    
                if isinstance(sample_label,list):
                    sample_label = pd.concat(sample_label)
                sample = pd.concat(sample_feature)
                sample = sample.merge(sample_label,on=['date','stock'],how='left')
                print('......................')   
                sample = sample[~np.isnan(sample[label_name])]            

        return sample,factor_list
    def get_model(self):
        raise NotImplementedError
    def lable_predict(self):
        raise NotImplementedError

class DeepFM_test_shN_qcut(XModel):
    
    def __init__(self,params):
        self._label_name = params['label_name']
        self._random_seed = 1989#params['random_seed']
        self._modelname =  params['modelname']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']
        self._factor_info = params['factor_info']
    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed


    def my_generator(self,dates,batch_size,factor_do=None):
        factor_info = (self._factor_info).copy()
        if factor_do is None:
            pass
        else:            
            factor_info['factors'] = factor_do
        sample,factor_list = self.get_sample(dates,self._label_name,factor_info)
        train_x = sample[factor_list].values
        train_y = sample[self._label_name].values
        total_size = len(train_x)
        
        while True:
            shuffle_index_list = np.random.permutation(len(train_x))
            train_x = train_x[shuffle_index_list]
            train_y = train_y[shuffle_index_list]
            for i in range(total_size//batch_size):
                yield train_x[i*batch_size:(i+1)*batch_size],train_y[i*batch_size:(i+1)*batch_size]
#DeepFM_keras3M_M1_lrV8_hf_base_NoShuffle0930_0.005_2048_0.2_0.7
    def get_model(self,dates,factor_list_,dfm_params=None):
        
        factor_list = copy.deepcopy(sorted(factor_list_))           
        nn = len(factor_list)
        drop=0.7
        learning_rate=0.005
        l2=0.2  
        if dfm_params is None:
            dfm_params = {
                'feature_size': nn,
                'field_size': nn,
                'k': 8,
                'use_fm': True,
                'use_deep': True,
                'dropout_keep_fm': [drop, drop, drop],#0.5, 0.6
                'deep_layers': [8, 32, 64],
                'dropout_keep_deep': [drop, drop, drop, drop],
                'epoch': 5,
                'batch_size': 1024*2,
                'learning_rate': learning_rate,#0.01,
                'optimizer_type': 'adam',
                'verbose': 1,
                'random_seed': 1989,
                'loss_type': 'mse',
                'eval_metric': 'auc',
                'l2': l2,#0.9,
                'greater_is_better': True,
                'Train_label':True,
                'model_n':1,
                'label_ts':False
            }  
        print('len factors',nn)            
        dfm_params['feature_size']=nn
        dfm_params['field_size']=nn
        factor_drop_ratio = dfm_params['factor_drop_ratio']
        np.random.seed(dfm_params['random_seed']) 
        if dfm_params['label_ts'] is False:
            np.random.shuffle(dates)

#        print(factor_list[410:420])      
        if factor_drop_ratio>0:
            pass
            # np.random.shuffle(factor_list)    
#            print(factor_drop_ratio,dfm_params['random_seed'], factor_list[410:420])    
        print('date',dates[0])

        batch_size = dfm_params['batch_size']
        epochs = dfm_params['epoch']
         
        try:
            os.makedirs(self._model_path)
        except:
            pass

        # from xquant.factordata import FactorData
        # s = FactorData()
        # sample_date = s.tradingday('20190701','20200701')
        # valid_dates = []
        # valid_dates.append(sample_date)  
        gap = int(self._label_name.split('_')[-1][:1])
        model_n = dfm_params['model_n']

        if model_n == 4:
            valid_dates = []
            valid_dates.append([dates[:int(len(dates)/4*3)],dates[:int(len(dates)/4*3)]]) #@         
            valid_dates.append([dates[:int(len(dates)/4)*2]+dates[int(len(dates)/4)*3:],dates[:int(len(dates)/4)*2]+dates[int(len(dates)/4)*3:]])
            valid_dates.append([dates[:int(len(dates)/4)*1]+dates[int(len(dates)/4)*2:],dates[:int(len(dates)/4)*1]+dates[int(len(dates)/4)*2:]])
            valid_dates.append([dates[int(len(dates)/4*1):],dates[int(len(dates)/4*1):]])

            train_dates = []
            train_dates.append(sorted(list(set(dates)-set(valid_dates[0][1])))) #@         
            train_dates.append(sorted(list(set(dates)-set(valid_dates[1][1]))))
            train_dates.append(sorted(list(set(dates)-set(valid_dates[2][1]))))
            train_dates.append(sorted(list(set(dates)-set(valid_dates[3][1]))))

        i_model=0
        for i_date in range(len(train_dates)):
            if factor_drop_ratio>0:
                factor_do = factor_list[min(int(factor_drop_ratio*i_date*len(factor_list)),len(factor_list)-100):int(factor_drop_ratio*(i_date+1)*len(factor_list))]
                factor_do = sorted(list(set(factor_list)-set(factor_do)))
                nn = len(factor_do)
                dfm_params['feature_size']=nn
                dfm_params['field_size']=nn                
            else:
                factor_do = factor_list.copy()
            if os.path.isfile(os.path.join(self._model_path, 'model%s' % str(i_model) +'_%s.h5' % str(epochs))) and dfm_params['Train_label'] is False:
                print('Warning Exist',os.path.join(self._model_path, 'model%s' % str(i_model) +'_%s.h5' % str(epochs)))
                i_model +=1
                continue
            else:
                patience = 300
                if patience>=epochs:
                    dates_val = valid_dates[i_date][0][:2]
                    save_best_only = False
                else:
                    dates_val = valid_dates[i_date][0]                
                    save_best_only = True                     
                checkpoint = ModelCheckpoint(os.path.join(self._model_path, 'model%s' % str(i_model) + '_{epoch:02d}' +'.h5'), monitor='val_loss', \
                    save_best_only=save_best_only,mode='auto',verbose=2,save_weights_only=True,period=5)                    
                earlystopping = EarlyStopping(monitor="val_loss", patience=patience,mode='min')#@
                callback_list = [checkpoint,earlystopping]                 
                dates_train = train_dates[i_date]

                np.random.shuffle(dates_train)
                np.random.shuffle(dates_val)
                # print(i_model,'dates_train',dates_train[0])
                print(i_model,'dates_train',dates_train[0],len(dates_train),len(dates_val),batch_size,len(dates_val)*3300//batch_size,len(factor_do),factor_do[0],\
                    min(int(factor_drop_ratio*i_date*len(factor_list)),len(factor_list)-100),int(factor_drop_ratio*(i_date+1)*len(factor_list)))
#                print(factor_do[400:410],factor_do[-10:])
                dfm = ModelDeepFM(**dfm_params)
                history=dfm.model.fit_generator(self.my_generator(dates_train,batch_size,factor_do),steps_per_epoch=len(dates_train)*3300//batch_size,
                                            validation_data = self.my_generator(dates_val,batch_size,factor_do),validation_steps=len(dates_val)*3300//batch_size,
                                            epochs=epochs, verbose=2,shuffle=True,callbacks=callback_list)
                i_model += 1
                pd.to_pickle(pd.DataFrame(history.history),os.path.join(self._model_path, 'model%s' % str(i_model) + '_history.pkl'))
                K.clear_session()
                tf.reset_default_graph()
    def label_predict(self, sample_daily, factor_list_,dfm_params,ep=''):
        res = []
        factor_list = copy.deepcopy(sorted(factor_list_))
        nn = len(factor_list)
        dfm_params['feature_size']=nn
        dfm_params['field_size']=nn
        model_n = dfm_params['model_n']
        factor_drop_ratio = dfm_params['factor_drop_ratio']
        np.random.seed(dfm_params['random_seed'])             
        if factor_drop_ratio>0:
            pass
        for j in range(model_n):
            if factor_drop_ratio>0:
                factor_do = factor_list[min(int(factor_drop_ratio*j*len(factor_list)),len(factor_list)-100):int(factor_drop_ratio*(j+1)*len(factor_list))]
                factor_do = sorted(list(set(factor_list)-set(factor_do)))
                nn = len(factor_do)
                dfm_params['feature_size']=nn
                dfm_params['field_size']=nn                
            else:
                factor_do = factor_list.copy()

            dfm = ModelDeepFM(**dfm_params)
            if ep is '':
                dfm.model.load_weights(os.path.join(self._model_path, 'model%s' % str(j) +'.h5'))            
            else:
                dfm.model.load_weights(os.path.join(self._model_path, 'model%s' % str(j) +'_%s.h5' % str(ep)))
            x_test = sample_daily[factor_do]#(( - x_stats['mu']) / x_stats['std']).values
            y_pred = dfm.model.predict(x_test)
            label_pred = pd.Series(index=sample_daily['stock'].values, data=y_pred.flatten())
            res.append(label_pred)
            K.clear_session()
            tf.reset_default_graph()
        res_ = pd.concat(res, axis=1)
        prediction = res_.mean(axis =1) 
        return prediction,res        
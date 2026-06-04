import os
os.environ['KERAS_BACKEND'] = 'tensorflow'
import numpy as np
import pandas as pd
from keras import models
from keras import layers
from keras import optimizers
from keras.callbacks import ModelCheckpoint, EarlyStopping
from keras import backend as K
from keras.utils.generic_utils import CustomObjectScope
import tensorflow as tf

import numpy as np
import time
import sys
import pickle as pkl
import datetime as dt
from sklearn.model_selection import TimeSeriesSplit
import random
import math
from tqdm import tqdm
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import classification_report

seed=1
random.seed(seed)
np.random.seed(seed)
tf.set_random_seed(seed)

def r_square(y_true, y_pred):
    SS_res =  K.sum(K.square( y_true-y_pred ),axis=0)
    SS_tot = K.sum(K.square( y_true - K.mean(y_true) ),axis=0 )
    return K.mean( 1 - SS_res/(SS_tot + K.epsilon()) )

def mae_np(y_true, y_pred):
    return np.mean(np.abs(y_pred - y_true))

def rsquare_np(y_true, y_pred):
    SS_res =  np.sum(np.square( y_true-y_pred ),axis=0)
    SS_tot = np.sum(np.square( y_true - np.mean(y_true) ),axis=0 )
    return 1 - SS_res/(SS_tot + 1e-6)
def group_return(act,pct,pct_mean=True,group_num=20):
    if pct_mean:
        pct = pct.sub(pct.mean(axis=1),axis=0) 
    act = act.rank(axis=1,pct=True,ascending=True,method='first')
#     print(act)
    g_return = {}
    pct_small = 1/group_num
    i = 0
    g_return[i]   = pct[(act>=pct_small*i)&(act<=pct_small*(i+1))].mean(axis=1)
    for i in range(1,group_num):
        g_return[i] = pct[(act>pct_small*i)&(act<=pct_small*(i+1))].mean(axis=1)
    g_return = pd.DataFrame(g_return)
#     print(g_return)
    return g_return
def cal_corr(pred_list, pct_list):
    for i, label_pred in enumerate(pred_list):
        for j, pct_daily in enumerate(pct_list):
            print('pred: '+str(i)+', real: '+str(j))
            pct_daily=pct_daily.reindex(columns=label_pred.columns)
            gr=group_return(label_pred,pct_daily)
            print(np.mean(np.array(gr),axis=0))
class CustomStopper(EarlyStopping):
    def __init__(self, monitor='val_loss',
             min_delta=0, patience=0, verbose=0, mode='auto', start_epoch = 0): # add argument for starting epoch
        super(CustomStopper, self).__init__(monitor=monitor,patience=patience,min_delta=min_delta,mode=mode)
        self.start_epoch = start_epoch

    def on_epoch_end(self, epoch, logs=None):
        if epoch > self.start_epoch:
            super().on_epoch_end(epoch, logs)
class LSTM_Model():
    def __init__(self, params):
        self._label_name = params['label_name']
        self._random_seed = 2333
        self._modelname = params['modelname']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']
        self._latent_dim = 256

    def revise_model_path(self, path):
        self._model_path = path

    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed

    def prev(self, train_sample, prev_idx):
        prev_sample = []
        zeros = np.zeros((train_sample.shape[1]), np.float)
        for idx, i in enumerate(prev_idx):
            if i >= 0 and i <= idx:
                prev_sample.append(train_sample[idx - i])
            else:
                prev_sample.append(train_sample[idx])
        return np.array(prev_sample)

    def define_model(self, factor_list):
        latent_dim = self._latent_dim
        encoder_inputs = layers.Input(shape=(5, len(factor_list)),
                                      name='encoder_inputs')
        encoder = layers.LSTM(latent_dim, name='encoder')
        encoder_outputs = encoder(encoder_inputs)
        decoder_dense = layers.Dense(3,
                                     name='decoder_dense',
                                     activation='softmax')
        decoder_outputs = decoder_dense(encoder_outputs)

        # Define and compile model as previously
        self.model = models.Model(encoder_inputs, decoder_outputs)

    def get_model(self, train_sample, factor_list):
        self.define_model(factor_list)

        y_train = train_sample[self._label_name].values
        idx_sample = np.nonzero(np.sum(y_train,axis=1))
        y_train_sample = y_train[idx_sample]
        
        x_train = train_sample[factor_list]

        mu = x_train.mean()  # according to factor
        std = x_train.std()
        std[std == 0] = 1.e-6
        pd.DataFrame(index=['mu', 'std'], data=[mu, std]).T.to_pickle(
            os.path.join(self._model_path, 'mlgb_x_stats.pkl'))

        x_train = ((x_train - mu) / std).values

        x_train_np = np.array(x_train)
        prev_idx_train = train_sample['prev_idx'].values
        x_train_stack = [x_train_np]

        for i in range(4):
            x_train_stack.insert(0, self.prev(x_train_stack[0],
                                              prev_idx_train))

        x_train_stack_sample = [i[idx_sample] for i in x_train_stack]
        x_train_stack_sample = np.transpose(np.asarray(x_train_stack_sample), (1, 0, 2))
        print(y_train.shape, y_train_sample.shape)

        idx = np.arange(x_train_stack_sample.shape[0])
        np.random.shuffle(idx)
        x_train_stack_sample = x_train_stack_sample[idx]
        y_train_sample = y_train_sample[idx]

        self.model.compile(optimizer=optimizers.RMSprop(lr=1e-4),
                           loss='categorical_crossentropy',
                           metrics=['accuracy'])
        print(self.model.summary())

        epochs = 50
        checkpoint = ModelCheckpoint(filepath=os.path.join(
            self._model_path, 'best_valid'),
                                     monitor='val_loss',
                                     mode='auto',
                                     save_best_only='True')
        early_stopping = CustomStopper(monitor='val_loss',
                                       patience=int(epochs / 10),
                                       start_epoch=10)
        #         early_stopping = EarlyStopping(monitor='val_loss', patience=5)
        callback_lists = [checkpoint, early_stopping]
        self.model.fit(x_train_stack_sample,
                       y_train_sample,
                       batch_size=2048,
                       epochs=epochs,
                       validation_split=0.1,
                       callbacks=callback_lists,
                       verbose=2)

    def label_predict(self, sample_daily, factor_list):
        self.model = models.load_model(
            os.path.join(self._model_path, 'best_valid'))

        x_stats = pd.read_pickle(
            os.path.join(self._model_path, 'mlgb_x_stats.pkl'))
        x_test = sample_daily[factor_list]
        x_test = (x_test - x_stats['mu']) / x_stats['std']

        x_test_stack = [np.array(x_test)]
        prev_idx_test = sample_daily['prev_idx'].values

        for i in range(4):
            x_test_stack.insert(0, self.prev(x_test_stack[-1], prev_idx_test))
        x_test_stack = np.transpose(np.asarray(x_test_stack), (1, 0, 2))

        y_test = sample_daily[self._label_name].values
        mlb = MultiLabelBinarizer(classes=[0,1,2])
        y_test = mlb.fit_transform(y_test)

        loss, acc = self.model.evaluate(x_test_stack, y_test, batch_size=2048)
        print('loss=',loss,'acc=',acc)
        y_pred = self.model.predict(x_test_stack)
        print(classification_report(y_test.argmax(axis=1), y_pred.argmax(axis=1), target_names=['bottom','medium','top']))

        label_pred = pd.DataFrame(index=sample_daily['stock'].values, columns=['0','1','2'], data=y_pred)
        return label_pred, acc
def preprocess_data(data):
    data=data.reset_index(drop=True).reset_index()
    data2=data.pivot(index='date',columns='stock',values='index')
    data2=data2.shift(1)
    data2=data2.unstack().swaplevel('date','stock').sort_index().reset_index().rename(columns={0:'prev_idx'})
    data2=data2.dropna()
    data=pd.merge(data,data2,how='left')
    data['prev_idx']=data['index']-data['prev_idx']
    data=data.drop(['index'],axis=1)
    data['prev_idx']=data['prev_idx'].fillna(-1).astype("int")
    return data
def preprocess_label(data,factor_name):
    factor_value = data[['date', 'stock',
                         factor_name]].pivot(index='date',
                                             columns='stock',
                                             values=factor_name)
    factor_rank = factor_value.rank(axis=1)
    factor_rank = pd.melt(factor_rank.reset_index(),
                          id_vars='date',
                          value_vars=factor_rank.columns)

    factor_label = factor_rank.copy()
    stocks_per_day = factor_value.shape[1] - factor_value.isna().sum(axis=1)
    factor_rank['stocks_num'] = stocks_per_day[factor_rank['date']].values

    factor_label = factor_label.rename(
        columns={'value': factor_name + '_bottom'})
    factor_label[factor_name + '_bottom'] = 0
    factor_label[factor_name + '_top'] = 0

    idx_bottom = factor_label.loc[factor_rank['value'] < 0.3 *
                                  factor_rank['stocks_num']].index
    idx_top = factor_label.loc[factor_rank['value'] > 0.7 *
                               factor_rank['stocks_num']].index
    
    factor_label.loc[idx_bottom, factor_name + '_bottom'] = 1
    factor_label.loc[idx_top, factor_name + '_top'] = 1
    data=pd.merge(data, factor_label,on=['date','stock'],how='left')
    return data
def update_model_predict(root_path='',path_sample=[],factor_list=[],
            today_date = '20200407',retrain_flag = True,lookback_period_max = 300,
            model_config_list = [
                    ('LSTM_Model','vwap','vwap_re_5d',5,240)
                        ],suffix=None):
    t = time.time()
    path_feature = '/data/group/800020/AlphaDataCenter/Department/DepartSample/Sample/feature/'
    label = pd.read_pickle('/data/user/013546/rubbish/label.pkl').fillna(0)
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
    
        training_sample = training_sample[['date','stock']+factor_list].merge(label,on=['date','stock'],how='left')
        training_sample = preprocess_data(training_sample)
        training_sample = preprocess_label(training_sample,'vwap_re_5d')
        print(len(training_sample))
        print('......................')   
    sample_daily = pd.read_pickle(path_feature+today_date+'.pkl')
    sample_daily = sample_daily[['date','stock']+factor_list].merge(label,on=['date','stock'],how='left')
    sample_daily = preprocess_data(sample_daily)
    sample_daily = preprocess_label(sample_daily,'vwap_re_5d')
    val_metrics=[]
    for config in model_config_list:
        print(config)
        excess = config[1]
        root_model_path = root_path+'Models/'
        root_predict_path = root_path+'DailyPrediction/'+excess+'/'
        if not suffix is None:
            root_model_path += suffix
            root_predict_path += suffix
        params={}
        params['label_name'] = ['vwap_re_5d_discre']
        params['weight'] = [-6,-2,0,0,0,10]
        params['time'] = excess
        params['modelname'] = config[0]
        params['model_path'] = root_model_path + params['modelname']+'/'
        params['prediction_path'] = root_predict_path + params['modelname']+'/'
        params['sample_path'] = path_sample
        print(params)
        execstr = config[0]+'(params)'
        
        K.clear_session()
        model = eval(execstr)
        if retrain_flag == True:
            gap_period = config[3]
            model_retrain_date = all_trading_days[:-gap_period-1]
#            model_train_date = model_retrain_date[:-20]
#            model_valid_date = model_retrain_date[-20:]
#            print(model_valid_date)
#            print(len(model_train_date))
            retrain_samples = training_sample[training_sample['date'].isin(model_retrain_date)]

#            valid_sample = training_sample[training_sample['date'].isin(model_valid_date)]
            t = time.time()
            if not os.path.exists(model._model_path):
                os.makedirs(model._model_path)
            model.get_model(retrain_samples.copy(),factor_list)
            print(model._modelname +' train finished' , time.time() - t)

#        pct_daily=[x.loc[pd.to_datetime([today_date])] for x in pct_list]
        pred,acc = model.label_predict(sample_daily, factor_list)
        if not os.path.exists(params['prediction_path']):
            os.makedirs(params['prediction_path'])
        pd.to_pickle(pred,params['prediction_path']+today_date+'.pkl')
        print(model._modelname +'   predict finished' , today_date, time.time() - t)
#         val_metrics.append([mae,rsquare])
#         cal_corr(pred, pct_daily)
#         val_metrics=np.mean(np.array(val_metrics),axis=0)
#         print(val_metrics)
import time
import os
close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
dates = list(close.index)
dates = [str(i.year)+str(i.month).zfill(2)+str(i.day).zfill(2) for i in dates]
train_start = '20180101'
date_start = '20200101'
date_end = '20200617'
step = 20
count = 0
lookback_period_max = 240
retrain_flag = True  
root_path = '/data/user/013546/AlphaDataCenter/'
suffix = 'depart_lstm_'+date_start+'_'+date_end+'/'
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Department/DepartSample/factor_info_new.pkl')['day_factors']
rubbish = ['Vwap_Close_Range_Diff', 'LongBear', 'LongBull', 
'BollingerDown20d', 'ShortBear', 'BollingerUp20d', 
 'ShortBull', 'RankNetProfitDps']
factor_list = sorted(list(set(factor_list)-set(rubbish)))
factor_list = factor_list
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
                lookback_period_max = lookback_period_max,suffix=suffix)
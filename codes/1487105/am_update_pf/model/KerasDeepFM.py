import sys
import os
from keras import models
from keras.callbacks import ModelCheckpoint,EarlyStopping
from sklearn.metrics import auc
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
from keras.layers import Dense, Activation, Flatten, Convolution1D, Dropout
from keras.layers import Concatenate, dot, Activation, Reshape
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
import sys 
sys.path.insert(0,'am_update_pf/')
from update_sample import *
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


    
class KerasModelDeepFM(BaseEstimator, TransformerMixin):
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
                greater_is_better = True, decay=0,use_first=True,Train_label=True, cn_label=True
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

        self.bestModelPath = bestModelPath
        self.log_dir = log_dir

        self.greater_is_better = greater_is_better
        self.decay = decay
        self.cn_label = cn_label

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
    
        # self.feat_index = Input(shape=(self.field_size,)) #None*F
        if self.dropout_keep_fm[2] == 0:
            self.feat_value = Input(shape=(self.field_size,)) #None*F    
        else:
            self.feat_value_ = Input(shape=(self.field_size,))
            self.feat_value = Dropout(self.dropout_keep_fm[2], seed=self.seed, name='feat_value',input_shape=(self.field_size,))(self.feat_value_)
        # self.embeddings = Embedding(self.feature_size, self.k, name='feature_embeddings', 
        #         embeddings_initializer=keras.initializers.TruncatedNormal(mean=0.0, stddev=0.02, seed=self.seed)\
        #         ,embeddings_regularizer=l1_l2(l2=self.l2,l1=self.l1))(self.feat_value) #None*F*k
        feat_value = Reshape((self.field_size, 1))(self.feat_value) #None*F*1
        self.embeddings = Dense(self.k, activation=None,use_bias=False,kernel_regularizer=keras.regularizers.l1_l2(l2=self.l2,l1=self.l1),\
                kernel_initializer=keras.initializers.TruncatedNormal(mean=0.0, stddev=0.02, seed=self.seed))(feat_value)

        # self.embeddings = Multiply()([self.embeddings, feat_value]) #None*F*8
    
        ###----first order------######
        self.y_first_order = self.feat_value
        ###----first order------######
        if self.cn_label == True:
            self.y_first_order_cn1 = Convolution1D(filters=1,kernel_size=4,strides=2,kernel_initializer=\
                keras.initializers.TruncatedNormal(mean=0.0, stddev=0.02, seed=self.seed))(Reshape((self.field_size, 1))(self.y_first_order))
            self.y_first_order_cn1 = Activation('relu')(self.y_first_order_cn1)
            # self.y_first_order_cn1 = Flatten()(self.y_first_order_cn1)

            self.y_first_order_cn2 = Convolution1D(filters=1,kernel_size=8,strides=4,kernel_initializer=\
                keras.initializers.TruncatedNormal(mean=0.0, stddev=0.02, seed=self.seed))(self.y_first_order_cn1)
            self.y_first_order_cn2 = Activation('relu')(self.y_first_order_cn2)
            self.y_first_order = Concatenate()([Flatten()(self.y_first_order_cn1),Flatten()(self.y_first_order_cn2)])
    
        ###------second order term-------###
        # sum_square part
        self.summed_feature_emb = MySumLayer(axis=1)(self.embeddings)                #None*k
        self.summed_feature_emb_squred = Multiply()([self.summed_feature_emb, self.summed_feature_emb]) #None*k
    
        # square_sum part
        self.squared_feature_emb = Multiply()([self.embeddings, self.embeddings])                 #None*F*k
        self.squared_sum_feature_emb = MySumLayer(axis=1)(self.squared_feature_emb)   #None*k
    
        # second order
        self.y_second_order = Subtract()([self.summed_feature_emb_squred, self.squared_sum_feature_emb])   #None*k
        self.y_second_order = Lambda(lambda x: x*0.5)(self.y_second_order)                      #None*k
        # self.y_second_order = MySumLayer(axis=1)(self.y_second_order) #None*1
        self.y_second_order = Dropout(self.dropout_keep_fm[1], seed=self.seed,name='y_second_order')(self.y_second_order)
    
        ##deep 
        self.y_deep = Dropout(self.dropout_keep_deep[0], seed=self.seed)(Reshape((self.field_size * self.k,))(self.embeddings))# # None*(F*k)
        input_size = self.feature_size * self.k        
        self.y_deep_ = []
        for i in range(0, len(self.deep_layers)):            
            if i == 0:
                glorot = np.sqrt(2.0 / (input_size + self.deep_layers[i]))
            else:
                glorot = np.sqrt(2.0 / (self.deep_layers[i-1] + self.deep_layers[i]))
            self.y_deep = Dense(self.deep_layers[i], activation=None,kernel_regularizer=keras.regularizers.l1_l2(l2=self.l2,l1=self.l1),\
                kernel_initializer=keras.initializers.TruncatedNormal(mean=0.0, stddev=glorot, seed=self.seed))(self.y_deep)
            self.y_deep = BatchNormalization()(self.y_deep,training=False)
            self.y_deep = Activation('tanh')(self.y_deep)#'relu','tanh'
            self.y_deep = Dropout(self.dropout_keep_deep[i+1], seed=self.seed)(self.y_deep) #None*32
            self.y_deep_.append(self.y_deep)
            
        self.y_first_order = Dropout(self.dropout_keep_fm[0], seed=self.seed,name='y_first_order')(self.y_first_order)
        #deepFM
        if self.use_fm and self.use_deep and self.use_first:
            self.concat_y = Concatenate()([self.y_first_order, self.y_second_order, self.y_deep]) 
            input_size = self.feature_size + self.k + self.deep_layers[-1]
        elif self.use_fm and self.use_first:
            self.concat_y = Concatenate()([self.y_first_order, self.y_second_order]) 
            input_size = self.feature_size + self.k
        elif self.use_deep and self.use_first:
            self.concat_y = Concatenate()([self.y_first_order, self.y_deep]) 
            input_size = self.feature_size + self.deep_layers[-1]
        else:
            self.concat_y = Concatenate()([self.y_first_order, self.y_second_order, self.y_deep_[-1], self.y_deep_[-2], self.y_deep_[-3]]) 
            input_size = self.feature_size + self.k + self.deep_layers[-1] + self.deep_layers[-2] + self.deep_layers[-3]            
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
        elif self.optimizer_type == 'SGD':            
            self.optimizer = keras.optimizers.SGD(lr=self.learning_rate,momentum=0,decay=0)#'sgd'#

        if self.loss_type == 'ranking_logloss':
            self.loss = binary_crossentropy_with_ranking
            print('use ranking_logloss')
        elif self.loss_type == 'logloss':
            self.loss = 'binary_crossentropy'
            self.metrics = auc
            greater_is_better=True
            print('use logloss')

        elif self.loss_type == 'mse':
            self.loss = 'mse'#'mean_squared_error'
            self.metrics = 'mean_squared_error'
            greater_is_better=False
            print('use mse')
        elif self.loss_type == 'mae':
            self.loss = 'mae'#'mean_squared_error'
            self.metrics = 'mean_absolute_error'
            greater_is_better=False
            print('use mae')    
        elif self.loss_type == 'coef':
            self.loss = self.correlation_coefficient_loss#'mean_squared_error'
            self.metrics = self.correlation_coefficient_loss
            greater_is_better=False
            print('use coef')    

        self.model.compile(optimizer=self.optimizer,
                loss=self.loss)#, metrics=[self.metrics]

class KerasDeepFM():
    
    def __init__(self,params):
        self._label_name = params['label_name']
        self._random_seed = 1989#params['random_seed']
        self._modelname =  params['modelname']
        self._model_path = params['model_path']
        self._prediction_path = params['prediction_path']
        self._strategy_type = params['strategy_type']
        self._dfm_params = {
                    'feature_size': 1,
                    'field_size': 1,
                    'k': 4,
                    'use_fm': False,
                    'use_deep': False,
                    'dropout_keep_fm': [0.2,0.2,0.2],#0.5, 0.6
                    'deep_layers': [64,256,512],#[8, 32, 64],
                    'dropout_keep_deep': [0.2,0.2,0.2,0.2],
                    'epoch': 30,
                    'batch_size': 512,
                    'learning_rate': 0.0001,#0.01,
                    'verbose': 1,
                    'random_seed': 1990,
                    'loss_type': 'coef',#@
                    'eval_metric': 'auc',
                    'l1':0.001,
                    'l2': 0.1,#0.9,
                    'greater_is_better': True,
                    'optimizer_type':'adam',
                    'Train_label':True,
                    'cn_label':False,
                }         
        if 'dfm_params' in params:
            self._dfm_params.update(params['dfm_params'])
        print(self._dfm_params)
    def revise_model_path(self, path):
        self._model_path = path
    
    def revise_label(self, label):
        self._label_name = label

    def revise_random_seed(self, seed):
        self._random_seed = seed


    def my_generator(self,dates,factor_list,batch_size):
        sample = load_sample(factor_list,dates,self._strategy_type,self._label_name,True)
        train_x = sample[factor_list].values
        train_y = sample[self._label_name].values
        total_size = len(train_x)
        
        while True:
            shuffle_index_list = np.random.permutation(len(train_x))
            train_x = train_x[shuffle_index_list]
            train_y = train_y[shuffle_index_list]
            for i in range(total_size//batch_size):
                yield train_x[i*batch_size:(i+1)*batch_size],train_y[i*batch_size:(i+1)*batch_size]
    def get_model(self,dates,factor_list):
        nn = len(factor_list)
        print('len factors',nn)            
        self._dfm_params['feature_size']=nn
        self._dfm_params['field_size']=nn
        print(self._dfm_params)
        np.random.seed(self._dfm_params['random_seed'])   
        np.random.shuffle(dates)
        print('date',dates[0])
        batch_size = self._dfm_params['batch_size']
        epochs = self._dfm_params['epoch']
         
        try:
            os.makedirs(self._model_path)
        except:
            pass

        valid_dates = []
        valid_dates.append(dates[:int(len(dates)/3)]) #@         
        i_model=0
        for dates_val in valid_dates:
            if os.path.isfile(os.path.join(self._model_path, 'model%s' % str(i_model) +'.h5')) and self._dfm_params['Train_label'] is False:
                print('Warning Exist',os.path.join(self._model_path, 'model%s' % str(i_model) +'.h5'))
                continue
            else:
                checkpoint = ModelCheckpoint(os.path.join(self._model_path, 'model%s' % str(i_model) +'.h5'), monitor='val_loss', \
                    save_best_only=True,mode='min',verbose=2,save_weights_only=True)
                earlystopping = EarlyStopping(monitor="val_loss", patience=3,mode='min')
                callback_list = [checkpoint,earlystopping]                 
                dates_train = sorted(list(set(dates)-set(dates_val)))
                np.random.shuffle(dates_train)
                print(i_model,'dates_train',dates_train[0])
                print(i_model,'dates_train',len(dates_train),len(dates_val),batch_size,len(dates_val)*3300//batch_size)
                dfm = KerasModelDeepFM(**self._dfm_params)
                history=dfm.model.fit_generator(self.my_generator(dates_train,factor_list,batch_size),steps_per_epoch=len(dates_train)*3300//batch_size,
                                            validation_data = self.my_generator(dates_val,factor_list,batch_size),validation_steps=len(dates_val)*3300//batch_size,
                                            epochs=epochs, verbose=2,shuffle=True,callbacks=callback_list)
                i_model +=1
                loss_dict = {}
                loss_dict['train_loss'] = history.history['loss']
                loss_dict['val_loss'] = history.history['val_loss']
                pd.to_pickle(loss_dict,os.path.join(self._model_path, 'model%s' % str(i_model) + '_history.pkl'))
                K.clear_session()
                tf.reset_default_graph()
    def label_predict(self, sample_daily, factor_list):
        res = []
        nn = len(factor_list)
        self._dfm_params['feature_size']=nn
        self._dfm_params['field_size']=nn
        self._dfm_params['Train_label'] = False 
        dfm = KerasModelDeepFM(**self._dfm_params)
        for j in range(1):
            dfm.model.load_weights(os.path.join(self._model_path, 'model%s' % str(j) +'.h5'))
            x_test = sample_daily[factor_list]
            y_pred = dfm.model.predict(x_test)
            label_pred = pd.Series(index=sample_daily['stock'].values, data=y_pred.flatten())
            res.append(label_pred)
            K.clear_session()
            tf.reset_default_graph()
        res = pd.concat(res, axis=1)
        prediction = res.mean(axis =1) 
        return prediction   

import numpy as np
import pandas as pd
import sys
sys.path.insert(0,'/data/user/013546/jupyter_path/')
import quadratic_weighted_kappa
from sklearn.cross_validation import KFold
import os.path
from sklearn.cross_validation import train_test_split
from scipy import optimize
from keras.models import Sequential,model_from_json
from keras.layers.core import Dense, Dropout, Activation
from keras.optimizers import Adadelta
from keras.layers.normalization import BatchNormalization
from keras.callbacks import Callback
from keras.layers.advanced_activations import PReLU
from keras.callbacks import EarlyStopping,ModelCheckpoint,ReduceLROnPlateau,TensorBoard
class CutPointOptimizer:
    
    def __init__(self, predicted, actual):
        self.predicted = predicted
        self.actual = actual

    def qwk(self, cutPoints):
        transformedPredictions = np.searchsorted(cutPoints, self.predicted) + 1   
        transformedPredictions = transformedPredictions.reshape(-1)
        return -1 * quadratic_weighted_kappa.quadratic_weighted_kappa(transformedPredictions, self.actual)
class clsvalidation_kappa(Callback):  #inherits from Callback
    
    def __init__(self, filepath, train_data=(), validation_data=(), patience=5):
        super(Callback, self).__init__()

        self.patience = patience
        self.X_val, self.y_val = validation_data 
        self.X_train, self.Y_train = train_data
        self.best = 0.0
        self.wait = 0  #counter for patience
        self.filepath=filepath
        self.best_rounds =1
        self.counter=0
        self.cutPoints = np.arange(1,21,1)
    
    def on_epoch_end(self, epoch, logs={}):
        
        self.counter +=1
        train_predictions = self.model.predict(self.X_train, verbose=0)
        cpo = CutPointOptimizer(train_predictions, self.Y_train)
        self.cutPoints = optimize.fmin(cpo.qwk, self.cutPoints)
        
        p = self.model.predict(self.X_val, verbose=0).reshape(-1) #score the validation data 
        
        p = np.searchsorted(self.cutPoints, p) + 1
        current = quadratic_weighted_kappa.quadratic_weighted_kappa(self.y_val.values.ravel(), p)       

        print('Epoch %d Kappa: %f | Best Kappa: %f \n' % (epoch,current,self.best))
    
    
        #if improvement over best....
        if current > self.best:
            self.best = current
            self.best_rounds=self.counter
            self.wait = 0
            self.model.save_weights(self.filepath, overwrite=True)
        else:
            if self.wait >= self.patience: #no more patience, retrieve best model
                self.model.stop_training = True
                print('Best number of rounds: %d \nKappa: %f \n' % (self.best_rounds, self.best))
                
                self.model.load_weights(self.filepath)
                           
            self.wait += 1 #incremental the number of times without improvement
class NN:
    def __init__(self, inputShape, layers, dropout = [], activation = 'relu', patience=5, init = 'uniform', loss = 'rmse', 
                 optimizer = 'adadelta', nb_epochs = 50,batch_size = 4056, verbose = 1,filepath=''):

        model = Sequential()
        for i in range(len(layers)):
            if i == 0:
                print ("Input shape: " + str(inputShape))
                print ("Adding Layer " + str(i) + ": " + str(layers[i]))
                model.add(Dense(layers[i], input_dim = inputShape, init = init))
            else:
                print ("Adding Layer " + str(i) + ": " + str(layers[i]))
                model.add(Dense(layers[i], init = init))
            #model.add(Activation(activation))
            model.add(PReLU())
            model.add(BatchNormalization())
            if len(dropout) > i:
                print ("Adding " + str(dropout[i]) + " dropout")
                model.add(Dropout(dropout[i]))
        model.add(Dense(1, init = init)) #End in a single output node for regression style output
        model.compile(loss=loss, optimizer=optimizer)
        self.optimizer = optimizer
        self.loss = loss    
        self.model = model
        self.nb_epochs = nb_epochs
        self.batch_size = batch_size
        self.verbose = verbose
        self.patience = patience
        self.filepath = filepath
    def fit(self, X_train, X_val,y_train,y_eval): 
        np.random.seed(1993)
        log_path = self.filepath+'log/'
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        callbacks= [TensorBoard(log_dir=log_path),EarlyStopping( monitor='val_loss',patience=self.patience,verbose=1,min_delta=1e-4),
                   ReduceLROnPlateau( monitor='val_loss',factor=0.1,patience=int(self.patience/2),verbose=1,epsilon=1e-4),
                   ModelCheckpoint( monitor='val_loss',filepath=self.filepath+'best_w.h5',save_best_only=True,save_weights_only=True)]
        
        self.model.fit(X_train, y_train, nb_epoch=self.nb_epochs, batch_size=self.batch_size, verbose = self.verbose,shuffle=True,
                       validation_data=(X_val, y_eval),callbacks=callbacks)
    def predict(self, X, batch_size = 10240, verbose = 1):
        if os.path.exists(self.filepath+'best_w.h5'):
            self.model.load_weights(self.filepath+'best_w.h5')
        return self.model.predict(X, batch_size = batch_size, verbose = verbose)[:,0]
class KappaNN():
    
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
    def save_model(self,model):
        model.save_weights(self._model_path+'model.h5')
        model_json = model.to_json()
        with open(self._model_path+'model.json', 'w') as json_file:
            json_file.write(model_json)
        return
    def load_model(self):
        with open(self._model_path+'model.json', 'r') as json_file: 
            loaded_model_json = json_file.read()
        model = model_from_json(loaded_model_json)
        model.load_weights(self._model_path+'model.h5')
        return model
    def get_model(self, sample, factor_list):
        np.random.seed(1993)
        g_num_1 = 20
        sample['rank'] = sample.groupby(by='date')['0930_1129_re_5d'].rank(pct=True,method='first')
        sample['rank'] = pd.cut(sample['rank'],bins=np.linspace(0,1,g_num_1+1),labels=np.arange(1,g_num_1+1,1)).astype(np.int64)
        X = sample[factor_list]
        y = sample[self._label_name]
        stocks = sample['stock'].unique().tolist()
        dates = sample['date'].unique().tolist()
        np.random.shuffle(stocks)
        np.random.shuffle(dates)
        train_stocks = stocks[:int(len(stocks)*0.8)]
        valid_stocks = stocks[int(len(stocks)*0.8):]
        train_dates = dates[:int(len(dates)*0.8)]
        valid_dates = dates[int(len(dates)*0.8):]
        train_sample = sample[(sample['date'].isin(train_dates))&(sample['stock'].isin(train_stocks))]
        valid_sample = sample[(sample['date'].isin(valid_dates))&(sample['stock'].isin(valid_stocks))]
        X_train,y_train = train_sample[factor_list],train_sample[self._label_name]
        X_val,y_eval = valid_sample[factor_list],valid_sample[self._label_name]
        mu = X.mean()
        std = X.std()
        std[std==0] = 1.e-6
        pd.DataFrame(index=['mu', 'std'], data=[mu, std]).T.to_pickle(os.path.join(self._model_path, 'x_stats.pkl'))
        X_train = ((X_train - mu) / std).values
        X_val = ((X_val-mu)/std).values
        cls = NN(inputShape = len(factor_list),layers = [200,300,200,100], dropout = [0.5, 0.5,0.25,0.25], activation='sigmoid', loss='mae', 
             optimizer = 'adam', init = 'glorot_normal', nb_epochs = 20,patience=4,filepath=self._model_path)
        cls.fit(X_train, X_val,y_train,y_eval)
        return

    def label_predict(self, sample_daily, factor_list):     
        from keras.models import load_model
#         import keras
#         keras.backend.clear_session()
        cls = NN(inputShape = len(factor_list),layers = [200,300,200,100], dropout = [0.5, 0.5,0.25,0.25], activation='sigmoid', loss='mae', 
             optimizer = 'adam', init = 'glorot_normal', nb_epochs = 20,patience=2,filepath=self._model_path)
        x_stats = pd.read_pickle(os.path.join(self._model_path, 'x_stats.pkl'))
        test_x = ((sample_daily[factor_list] - x_stats['mu']) / x_stats['std']).values
        y_pred = cls.predict(test_x)
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
    path_feature = path_sample
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
date_start = '20190101'
date_end = '20190630'
step = 20
count = 0
lookback_period_max = 300
retrain_flag = True  
root_path = '/data/user/013546/AlphaDataCenter/'
suffix = 'dnn_valid_'+date_start+'_'+date_end+'/'
model_config_list= [
            ('KappaNN','am','0930_1129_re_5d',5,lookback_period_max)
             ]
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
rubbish = ['Vwap_Close_Range_Diff', 'LongBear', 'LongBull', 
'BollingerDown20d', 'ShortBear', 'BollingerUp20d', 
 'ShortBull', 'RankNetProfitDps']
factor_list = sorted(list(set(factor_list)-set(rubbish)))
factor_list = factor_list
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
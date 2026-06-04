import numpy as np
import xgboost as xgb
import pickle
import pandas as pd

class Xgb_Reg_TS_Complex():
    
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
        dates = sample['date'].unique().tolist()
        dates = sorted(dates)
     
        for i in range(8):
            train_dates = dates[:25*(j+1)]
            validation_datesdates = dates[25*(i+1):25*(i+2)]
            validation_set = sample[sample['date'].isin(validation_dates)].copy()  
            validation_x = validation_set[factor_list]
            validation_y = validation_set[self._label_name]
            train_set = sample[sample['date'].isin(train_dates)].copy()  
            train_x = train_set[factor_list]
            train_y = train_set[self._label_name]
            xgb_model = xgb.XGBRegressor (
                        n_estimators=1000, nthread=24, min_child_weight = 0.1,reg_alpha = 10, gamma =1.0,
                        tree_method='gpu_hist', gpu_id=0,
                      colsample_bytree= 0.8, colsample_bylevel= 0.8, subsample=0.8 , seed=self._random_seed,  max_depth=8, learning_rate=0.1 )
                    
            xgb_model.fit(X=train_x, y=train_y, verbose=False, eval_set=[(train_x, train_y),(validation_x, validation_y)],
                     eval_metric=[ 'mae'], early_stopping_rounds = 20)
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'wb') as f:
                pickle.dump(obj =xgb_model,file= f)
            print('scores:', xgb_model.best_score, xgb_model.best_iteration)
        return
        

    def label_predict(self, sample_daily, factor_list):
                    
        res = []            
        for j in range(8):
            filename = self._model_path  +'model_'+str(j)+'.pkl'
            with open(filename, 'rb') as f:
                model = pickle.load(file=f)
            X_test = sample_daily[factor_list]
            y_pred = model.predict(X_test)
            label_pred = pd.Series(data=y_pred,index=sample_daily['stock'].values)
            res.append(label_pred)
        res = pd.concat(res, axis=1)
        prediction = res
        return prediction
def update_model_predict(root_path='',path_sample=[],factor_list=[],
            today_date = '20200407',retrain_flag = True,lookback_period_max = 300,
            model_config_list = [
                    ('XgboostReg_Model','vwap','vwap_re_1d',1,240),
                    ('DeepFM_Model','vwap','vwap_re_1d',1,240),
                    ('Lr_Model','vwap','vwap_re_5d',5,240)
                        ],suffix=None):
    t = time.time()
    path_feature = path_sample
#    label = pd.read_pickle('/data/user/013546/rubbish/map_act_label.pkl')
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
#        training_sample = training_sample[['date','stock']+factor_list].merge(label,on=['date','stock'],how='left')
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
            retrain_samples = retrain_samples[~np.isnan(retrain_samples[params['label_name']])]
            retrain_samples = retrain_samples.fillna(0)
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
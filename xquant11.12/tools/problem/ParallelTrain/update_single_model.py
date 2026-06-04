import sys 
sys.path.insert(0,'ParallelTrain/')
from config_path import *
import warnings
warnings.filterwarnings("ignore")
from KerasDeepFM_test_shN_qcut import *
from sklearn.externals.joblib import Parallel,delayed
import time
def get_trade_date(start_date, window):
    is_valid = pd.read_pickle(basic_daily_path + 'is_valid.pkl')
    if type(window) == type(start_date):
        return is_valid.loc[start_date:window].index
    elif window > 0:
        return is_valid.loc[start_date:].iloc[:window].index
    else:
        return is_valid.loc[:start_date].iloc[window:].index
def get_price_type(transaction_time='1300',transaction_period=120):
    d = '20140102'
    df = pd.read_pickle(basic_data_path+'minute/Amount/'+d+'.pkl').loc[d+transaction_time+'00':].iloc[:transaction_period]
    return df.index[0].strftime('%H%M')+'_'+df.index[-1].strftime('%H%M')

def get_factor_info(timepoint='1300',factor_info={}):
    factor_source_info = pd.read_pickle(factor_source_path)
    print(factor_source_path)
    day_factors = factor_info['day_factors']
    fix_factors = factor_info['fix_factors']
    factor_list = factor_info['factors']
    factor_info['own_day_factors'] = sorted(list(set(day_factors)&set(factor_source_info['own_day_factors'])))
    factor_info['depart_day_factors'] = sorted(list(set(day_factors) & set(factor_source_info['depart_day_factors'])))
    common_day_factors = sorted(list(set(factor_info['depart_day_factors'])&set(factor_info['own_day_factors'])))
    factor_info['own_day_factors'] = sorted(list(set(factor_info['own_day_factors'])-set(common_day_factors)))
    factor_info['extend_factors'] = sorted(list(set(factor_info['day_factors'])-set(factor_info['own_day_factors'])\
    -set(factor_info['depart_day_factors'])))
    factor_info['fix_sample_path'] = depart_sample_path + timepoint+'/'
    factor_info['timepoint'] = timepoint
    for k,v in factor_info.items():
        print(k,len(v))
    print('factor list',len(factor_list))
    return factor_info
def update_single_model(model_config = {'root_path':'','train_date':'20200407','model':'XgboostRegression',
                            'timepoint':'1300','label_name':'1300_1329_re_5d','gap':5,'train_window':240,'sample':True,
                            'factors_info':{},'factor_list':None,'dfm_params':None,
                           },suffix=None,pred_label=True):
    print('model_config_label_test',model_config['label_test'])
    t = time.time()
    root_model_path = model_config['root_path']+'Models/'+model_config['timepoint']+'/'+model_config['train_date']+'/'
    root_predict_path = model_config['root_path']+'/DailyPrediction/'+model_config['timepoint']+'/'
    model_config['factor_info'] = get_factor_info(model_config['timepoint'],model_config['factor_info'])
    if not suffix is None:
        root_model_path += suffix
        root_predict_path += suffix
    params={}
    params['label_name'] = model_config['label_name']
    params['modelname'] = model_config['model']+'_'+model_config['label_name']+'_'+model_config['label_test']
    params['model_path'] = root_model_path + params['modelname']+'/'
    params['prediction_path'] = root_predict_path + params['modelname']+'/'
    params['factor_info'] = model_config['factor_info']
    print(params['model_path'],params['prediction_path'])
    execstr = model_config['model']+'(params)'
    model = eval(execstr)
    gap_period = model_config['gap']
    all_trading_days = sorted([e[:-4] for e in os.listdir(day_depart_feature_path)])
    all_trading_days = [e for e in all_trading_days if e <= model_config['train_date']]
    model_retrain_date = all_trading_days[-model_config['train_window']- gap_period-1 :-gap_period-1]
    t = time.time()
    if not os.path.exists(model._model_path):
        os.makedirs(model._model_path)
    print(model._modelname +' re-train begin' , time.time() - t)
    factor_list = model_config['factor_info']['factors']
    if not model_config['sample']:
        model.get_model(model_retrain_date, factor_list,model_config['dfm_params'])
    else:
        sample = model.get_sample(model_retrain_date,model_config['label_name'],
                                              model_config['factor_info'])
        model.get_model(sample, factor_list,model_config['dfm_params'])
    print(model._modelname +' re-train finished' , time.time() - t)
def update_single_predict(model_config = {'root_path':'','train_date':'20200407','model':'XgboostRegression',
                            'timepoint':'1300','label_name':'1300_1329_re_5d','gap':5,'train_window':240,'sample':True,
                            'factors_info':{},'factor_list':None
                           },test_date_list=[],suffix=None,pred_label=True,act_check=False,pred_ep=''):
    t = time.time()
    root_model_path = model_config['root_path']+'Models/'+model_config['timepoint']+'/'+model_config['train_date']+'/'
    root_predict_path = model_config['root_path']+'/DailyPrediction/'+model_config['timepoint']+'/'
    model_config['factor_info'] = get_factor_info(model_config['timepoint'],model_config['factor_info'])
    if not suffix is None:
        root_model_path += suffix
        root_predict_path += suffix
    params={}
    params['label_name'] = model_config['label_name']
    params['modelname'] = model_config['model']+'_'+model_config['label_name']+'_'+model_config['label_test']
    params['model_path'] = root_model_path + params['modelname']+'/'
#    params['prediction_path'] = root_predict_path + params['modelname']+'/'
    params['factor_info'] = model_config['factor_info']
    pred_ep = str(pred_ep)
    params['prediction_path'] = root_predict_path + params['modelname']+'_'+pred_ep+'/'
    print(params['model_path'],params['prediction_path'])
    execstr = model_config['model']+'(params)'
    model = eval(execstr)
    t = time.time()
    factor_list = model_config['factor_info']['factors']
#    print(test_date_list)
    for today_date in test_date_list:
        sample,factor_list = model.get_sample(today_date,model_config['label_name'],
                                                  model_config['factor_info'])
#        pred = model.label_predict(sample, factor_list) #model_config['dfm_params']
        pred = model.label_predict(sample, factor_list, model_config['dfm_params'],pred_ep) #model_config['dfm_params']
        if not os.path.exists(model._prediction_path):
            os.makedirs(model._prediction_path)
        if pred_label:
            try:
                pred.to_csv(model._prediction_path + today_date +'.csv')
            except:
                pred[0].to_csv(model._prediction_path + today_date +'.csv')
                for i_ in range(len(pred[1])):
                    pred[1][i_].to_csv(model._prediction_path + today_date +'_%s.csv' % str(i_))

        if act_check:
            act_stat = pred.describe()
            act_stat = round(act_stat,2)
            act_stat = act_stat.astype('str')
            act_stat_ = act_stat.to_dict()

            act_dict_str = ''
            for key, value in act_stat_.items():
                act_dict_str=act_dict_str+key+':'+value+', '        
            lm.sendMessage("Train :%s,  %s, %s" % (params['modelname'],act_dict_str,today_date))    
        print(model._modelname +'   predict finished' , today_date, time.time() - t)
        print(params['model_path'],params['prediction_path'])


if __name__=='__main__':
    map_config = pd.read_pickle(sys.argv[2])
    update_single_model(model_config=map_config[int(sys.argv[1])])
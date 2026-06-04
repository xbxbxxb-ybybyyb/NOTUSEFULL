from sklearn.externals.joblib import Parallel,delayed
import warnings
warnings.filterwarnings("ignore")
import os
os.environ["MKL_NUM_THREADS"] = '4'
os.environ["NUMEXPR_NUM_THREADS"] = '4'
os.environ["OMP_NUM_THREADS"] = '4'


import time
import numpy as np 
import pandas as pd 
import sys 
import time 
from datetime import datetime
sys.path.insert(0,'ParallelTrain/')
from config_path import *
import update_single_model
def get_price_type(transaction_time='1300',transaction_period=120):
    assert transaction_time in ['0930','1000','1030','1100','1300','1330','1400','1430','vwap','vwaplf']
    if transaction_time in ['0930','1000','1030','1100','1300','1330','1400','1430']:
        d = '20140102'
        df = pd.read_pickle(basic_data_path+'minute/Amount/'+d+'.pkl').loc[d+transaction_time+'00':].iloc[:transaction_period]
        return df.index[0].strftime('%H%M')+'_'+df.index[-1].strftime('%H%M')
    else:
        return transaction_time[:4]
def cmd_help(t,path):
    # os.system('python3 '+'./ParallelTrain/update_single_model.py '+str(t)+' '+path)
    os.system('python3 ' + '/data/user/014342//ParallelTrain/update_single_model.py ' + str(t) + ' ' + path)
def parallel_train_model(root_path='',model_list=[],train_date_list=['20200103','20200110'],
                         timepoint_list=['0930','1000','1030','1100','1300','1330','1400','1430'],
                         num_threads=3,label_train=True,dfm_train_label=True):#timepoint_list=['am','pm','vwap']
    factor_custom_info = pd.read_pickle(factor_custom_path)
    fs = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
    #import os
    #del_list = [f[:-4] for f in os.listdir('/data/group/800020/AlphaDataCenter/Factor/fundamental_tmp/')]
    #fs = list(set(fs) - set(del_list))
    
    #fs = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
    #fs=pd.read_pickle('/data/user/012620/Share/fs_all_act_07_1788_20190701.pkl')
    model_name = 'DeepFM_test_shN_qcut'
    fs = sorted(fs)
    factor_custom_info={}
    factor_custom_info['vwaplf']={}
    factor_custom_info['vwaplf'][model_name]={}
    factor_custom_info['vwaplf'][model_name]['day_factors']=fs
    factor_custom_info['vwaplf'][model_name]['factors']=fs
    factor_custom_info['vwaplf'][model_name]['fix_factors']=[]
    

    nn = np.nan    
    drop=0.2
    drop_lr=0.2
    drop_first=0.2
    learning_rate = 1e-5
    batch_size = 512
    epoch = 20
    k = 1
    nn1 = 512
    nn2 = 256
    nn3 = 128
    nn4 = 0#0
    model_n=4    
    train_window = 480#240
    factor_drop_ratio=0.35
    em_initial_ones = True     
    use_fm_last = False   
    use_first = True
    use_deep=False
    optimizer_types=['adam']#['sgd','adamax','nadam']
    decay=0
    loss_type='coef'
    cn_label=False   
    label_ts = False
    activation_name = 'relu'#,'relu'
    kernel_initializer_names = ['glorot_normal']#['glorot_uniform','he_normal','lecun_normal','he_uniform','lecun_uniform','glorot_normal']        
    use_fm=False
    l2 = 0
    l1= 0
    optimizer_type = optimizer_types[0]
    kernel_initializer_name = kernel_initializer_names[0]
    dfm_params = {
        'feature_size': nn,
        'field_size': nn,
        'k': k,
        'use_fm': use_fm,
        'use_deep': use_deep,
        'dropout_keep_fm': [drop_lr, drop, drop_first],#0.5, 0.6
        'deep_layers': [nn1, nn2, nn3, nn4],#[8, 32, 64],
        'dropout_keep_deep': [drop, drop, drop, drop, drop],
        'epoch': epoch,
        'batch_size': batch_size,
        'learning_rate': learning_rate,#0.01,
        'verbose': 1,
        'random_seed': 1990,
        'loss_type': loss_type,#@
        'eval_metric': 'auc',
        'l1':l1,
        'l2': l2,#0.9,
        'greater_is_better': True,
        'optimizer_type':optimizer_type,
        'Train_label':dfm_train_label,
        'cn_label':cn_label,
        'model_n':model_n,
        'label_ts':label_ts,
        'activation_name':activation_name,
        'kernel_initializer_name':kernel_initializer_name,
        'use_first':use_first,
        'factor_drop_ratio':factor_drop_ratio,
        'em_initial_ones':em_initial_ones,
        'use_fm_last':use_fm_last
    }     

    model_config_list = []
    for model in model_list:
        for train_date in train_date_list:
            for timepoint in timepoint_list:
                model_config = {}
                model_config['root_path'] = root_path
                model_config['train_date'] = train_date
                model_config['model'] = model
                model_config['timepoint'] = timepoint
                if timepoint == 'vwaplf':
                    model_config['label_name'] = get_price_type(timepoint,30)+'_re_5d'
                else:
                    model_config['label_name'] = get_price_type(timepoint,30)+'_re_5d'
                model_config['gap'] = int(model_config['label_name'].split('_')[-1][:-1])
                label_test = '_test_'        
                model_config['train_window'] = train_window#240
                model_config['factor_info'] = factor_custom_info[timepoint][model]
                model_config['sample'] = False
                model_config['dfm_params'] = dfm_params                                                            
                model_config['label_test'] = label_test
                model_config_list.append(model_config)
    
    model_config_dict = dict(zip(np.arange(len(model_config_list)),model_config_list))
    if not os.path.exists(root_path+'config_data/'):
        os.makedirs(root_path+'config_data/')
    map_config_path = root_path+'config_data/map_config_dict_'+str(time.time())+'.pkl'
    pd.to_pickle(model_config_dict,map_config_path)
    if label_train:
        print('###########Train#############')
        Parallel(num_threads)(delayed(cmd_help)(k,map_config_path) for k in model_config_dict) 
    else:
        pass
    return model_config_dict
def get_train_test_map(start_date,end_date):
    close = pd.read_pickle(basic_data_path+'daily/close.pkl')
    all_dates = close.index.tolist()
    all_dates = sorted([i.strftime('%Y%m%d') for i in all_dates])
    retrain_flag = False  
   
    dates = [i for i in all_dates if i>=start_date and i<=end_date]
    step = 4#@
    count = -1
    train_test_map = {}
    this_train_date = ''

    for i in range(1,len(all_dates)):
        ds = all_dates[i-1]   
        if (ds<start_date)|(ds>end_date):
            continue
        de = all_dates[i]
        sample_date = ds
        if sample_date>='20191231':
            step = 1 #@           
        if count == -1 or (pd.to_datetime(de)-pd.to_datetime(ds)).days>1:
            count+=1
            if count % step == 0:
                this_train_date = ds          
        train_test_map[sample_date] = this_train_date
    return train_test_map
def get_key_by_value(s_dict, value):
    return [k for k, v in s_dict.items() if v == value]
def parallel_predict(model_config_dict,train_test_map,
                         num_threads=20,pred_ep=''):
    Parallel(num_threads)(delayed(update_single_model.update_single_predict)(v,get_key_by_value(train_test_map,v['train_date']),pred_ep=pred_ep) for k,v in model_config_dict.items()) 
    return model_config_dict
                            

train_test_map = get_train_test_map('20200416','20210422') #'20200403','20200814'
train_date_list=sorted(list(set([v for k,v in (train_test_map.items())])))
print('################')
print('train_date_list',train_date_list)
print('################')
time_train=['vwaplf']#'1000','1030','1100','1300','1330','1400','1430'
print('################time_train##########',time_train)
model_name = 'DeepFM_test_shN_qcut'
#model_name = 'DeepFM_test_shN'#DeepFM_test_shN
root_path = '/data/user/014342/AlphaTracer/mariner500/deep/new_958/'
model_config_dict = parallel_train_model(root_path=root_path,\
model_list=[model_name],train_date_list=train_date_list,timepoint_list=time_train,\
num_threads=4,label_train=True,dfm_train_label=True)#'1300'

model_config_dict = parallel_train_model(root_path=root_path,\
model_list=[model_name],train_date_list=train_date_list,timepoint_list=time_train,\
num_threads=4,label_train=True,dfm_train_label=False)#'1300'
print('################')      
label_pre_ep=True                  

parallel_predict(model_config_dict,train_test_map,
                        num_threads=1,pred_ep=20)

labels = list(set([v['label_test'] for k,v in model_config_dict.items()]))
print(labels)                        

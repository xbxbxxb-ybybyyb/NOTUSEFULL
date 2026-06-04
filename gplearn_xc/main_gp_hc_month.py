import pandas as pd
import numpy as np
import os
import time as mytime
import pickle
import shutil
import random
from my_gplearn_month.genetic import SymbolicRegressor
# from my_gplearn.genetic import SymbolicTransformer
# from gplearn.genetic import SymbolicTransformer
import sys
# print(os.path.abspath('../my_functions'))
sys.path.append(os.path.abspath('../my_functions'))
import my_fun as mf

BASE_DIR = r'/data/user/017839/my_python/gplearn_xc'
# BASE_DIR = r'D:/Work/遗传算法测试'

def get_top_bot_by_period3(p,period = 5):
    flag = np.ones_like(p) * np.nan
    for i in range(period,len(p) - period - 2):
        if p[i] >= np.max(p[i - period : i + period + 1]):
            flag[i] = 1
        elif p[i] <= np.min(p[i - period : i + period + 1]):
            flag[i] = -1    
    
    flag[0] = 1
    flag[-1] = 1
    
    return flag

def linear_top_bot(flag,p):
    last_index = 0
    p2 = np.ones_like(p) * np.nan
    for i in range(1,len(flag)):
        if not np.isnan(flag[i]):
            k = (p[i] - p[last_index]) / (i - last_index)
            for j in range(last_index,i + 1):
                p2[j] = p[last_index] + k * (j - last_index)
            last_index = i        

                
    return flag,p,p2

def load_data(index_code = '000906.SH',name = 'close',period = 63,zscore_n = 252,t1 = 20140101,t2 = 20221129):
    fn = BASE_DIR + r'/原始数据/%s.csv' % index_code
    df = pd.read_csv(fn,engine = 'python',index_col = 0,encoding = 'gbk')
    df = df[['trade_dt','s_dq_open','s_dq_high','s_dq_low','s_dq_close','s_dq_volume']]
    df = df.set_index('trade_dt')
    df = df.sort_index()
    # tlist = mf.get_list_trading_days(20140101,20191231)
    
    tlist_valid = mf.get_list_trading_days(t1,t2)
    t1 = mf.get_recent_trading_days(-zscore_n, t1)[0]
    tlist = mf.get_list_trading_days(t1,t2)
    # tlist = mf.get_list_trading_days(20100101, 20221129)
    df = df.reindex(tlist)
    df.columns = ['open','high','low','close','s_dq_volume']
    print(df.isna().sum())
    X_Train = df.values
    label = df.columns.tolist()
    # Y_Train = df['close'].values
        
    p = df['close'].values        
    flag = get_top_bot_by_period3(p,period)
    flag,p,p2 = linear_top_bot(flag,p)
    df['simple_close_%s' % period] = p2    
    df2 = df.copy()
    df2 = df2.reindex(tlist_valid)
    Y_Train = df2[name].values
    info_dict = {}
    info_dict['tlist'] = tlist_valid
    info_dict['fn'] = fn
    info_dict['code'] = index_code
    info_dict['name'] = name
    info_dict['zscore_n'] = zscore_n

    print(df)
    for sss in ['open','high','low']:
        df[sss] = df[sss] / df['close']
    for sss in ['close','s_dq_volume']:
        df[sss] = my_zscore(df[sss].values,n = zscore_n)
    for sss in ['open','high','low']:
        df[sss] = df[sss] * df['close']
    df = df.reindex(tlist_valid)
    
    X_Train = df[['open','high','low','close','s_dq_volume']].values

    return X_Train,Y_Train,label,info_dict


def load_data_diff(index_code='000906.SH', name='close', t1=20140101, t2=20221129):
    print(index_code)
    fn = BASE_DIR + r'/原始数据/%s.csv' % index_code
    df = pd.read_csv(fn, engine='python', index_col=0, encoding='gbk')
    df = df[['trade_dt', 's_dq_open', 's_dq_high', 's_dq_low', 's_dq_close', 's_dq_volume']]
    df = df.set_index('trade_dt')
    df = df.sort_index()

    # tlist = mf.get_list_trading_days(20140101,20191231)

    tlist_valid = mf.get_list_trading_days(t1, t2)
    t1 = mf.get_recent_trading_days(-1, t1)[0]
    tlist = mf.get_list_trading_days(t1, t2)
    # tlist = mf.get_list_trading_days(20100101, 20221129)
    df = df.reindex(tlist)
    df.columns = ['open', 'high', 'low', 'close', 's_dq_volume']

    df2 = df.copy()
    df2 = df2.reindex(tlist_valid)
    Y_Train = df2[name].values
    for label in ['open', 'high', 'low']:
        df[label] = df[label] / df['close'] - 1

    p = df['close'].values
    p[1:] = p[1:] / p[:-1] - 1
    v = df['s_dq_volume'].values
    v[1:] = v[1:] / v[:-1] - 1

    print(df.isna().sum())
    df = df.reindex(tlist_valid)
    X_Train = df.values
    label = df.columns.tolist()

    info_dict = {}
    info_dict['tlist'] = tlist_valid
    info_dict['fn'] = fn
    info_dict['code'] = index_code
    info_dict['name'] = name

    df = df.reindex(tlist_valid)

    X_Train = df[['open', 'high', 'low', 'close', 's_dq_volume']].values
    print(Y_Train[0])
    return X_Train, Y_Train, label, info_dict




def load_data_month(index_code='000906.SH', name='close', t1=20140101, t2=20221129):
    print(index_code)
    fn = BASE_DIR + r'/原始数据/%s.csv' % index_code
    df = pd.read_csv(fn, engine='python', index_col=0, encoding='gbk')
    df = df[['trade_dt', 's_dq_close']]
    df = df.set_index('trade_dt')
    df = df.sort_index()
    df.columns = ['close']
    
    f_df = pd.read_csv(BASE_DIR + r'/月频数据/预测结果_日期对齐.csv',engine = 'python',index_col = 0,encoding = 'gbk')
    df = df.reindex(f_df.index.tolist())
    
    tlist_valid = df.index.tolist()
    
    X_Train = f_df.values
    label = f_df.columns.tolist()
    Y_Train = df[name].values


    info_dict = {}
    info_dict['tlist'] = tlist_valid
    info_dict['fn'] = fn
    info_dict['code'] = index_code
    info_dict['name'] = name

    df = df.reindex(tlist_valid)


    print(Y_Train[0])
    return X_Train, Y_Train, label, info_dict








def my_zscore(data,n = 252):
    v = np.ones_like(data) * np.nan
    for i in range(n,len(data)):
        temp = data[i - n :i ]
        sigma = np.std(data[i - n : i],ddof = 1)
        mu = np.nanmean(data[i - n : i])
        v[i] = (data[i] - mu) / sigma
        
    return v



def train(label,X,y,score_df,metric='my_score',population_size = 100,parsimony_coefficient='fixed_10_15_1.5_0.1',random_state = 0,max_samples = 0.75,generations = 10,const_range = None,tournament_size = 100,test_mode = 1):
    function_set = ['plus','minus','mul','p_div','maxi','plus','minus','log','neg','Abs','sign','clear_by_cond','if_then_else','mean2','mean3','itself','ta_ht_dcphase','sig']
    ts_function_set = ['ts_ta_beta','ts_ta_dema','ts_ta_dema','ts_ta_kama','ts_ta_hma','ts_delay','ts_stddev','ts_delta','ts_corr_n','ts_cov_n','ts_sum','ts_mean','ts_max','ts_min','ts_prod','ts_wma','ts_emals']
    fixed_function_set = []

    est_gp = SymbolicRegressor(generations=generations, population_size=population_size,tournament_size = tournament_size,
                               function_set=function_set,
                               ts_function_set=ts_function_set,
                               fixed_function_set=fixed_function_set,
                               const_range=const_range,
                               parsimony_coefficient=parsimony_coefficient,
                               # parsimony_coefficient='fixed_10_15_1.5_0.1',
                               max_samples=max_samples, verbose=1,
                               stopping_criteria=999,
                               metric=metric,
                               random_state=random_state, n_jobs=-1, feature_names=label,test_mode = test_mode)

    est_gp.fit(X,y,score_df)
    return est_gp,X,y,score_df

def train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 2):
    for i in range(n_step):
        print('continue generatios = est_gp.generations + step')
        est_gp.set_params(generations = est_gp.generations + step,warm_start = True)
        est_gp.fit(X,y,score_df)
        save_result([info_dict,est_gp])


def get_train_result(gp):
    sss = []
    for program in gp._programs[-1]:
        sss.append([program.raw_fitness_,program.length_])
        
    return np.array(sss)


def load_data_list(main_index_code='000906.SH', index_list=['00300.SH', '000905.SH'], name='close', period=63,
                   zscore_n=252, t1=20140101, t2=20221129):
    # X_Train, Y_Train, label, info_dict = load_data(index_code=main_index_code, name=name, period=period,
    #                                                zscore_n=zscore_n, t1=t1, t2=t2)



    minor_list = []
    # info_dict0 = info_dict
    for index_code in index_list:
        # X_Train, Y_Train, label, _ = load_data(index_code=index_code, name=name, period=period, zscore_n=zscore_n,
        #                                        t1=t1, t2=t2)

        X_Train, Y_Train, label, _ = load_data_diff(index_code=index_code, name=name, t1=t1, t2=t2)

        minor_list.append([X_Train, Y_Train])


    X_Train, Y_Train, label, info_dict = load_data_diff(index_code=main_index_code, name=name, t1=t1, t2=t2)
    info_dict['index_list'] = index_list
    return X_Train, Y_Train, label, info_dict, minor_list


def load_data_list_month(main_index_code='000906.SH', index_list=['000300.SH', '000905.SH'], name='close', t1=20120101, t2=20221129):

    minor_list = []
    for index_code in index_list:

        X_Train, Y_Train, label, _ = load_data_month(index_code=index_code, name=name, t1=t1, t2=t2)

        minor_list.append([X_Train, Y_Train])


    X_Train, Y_Train, label, info_dict = load_data_month(index_code=main_index_code, name=name, t1=t1, t2=t2)
    info_dict['index_list'] = index_list
    return X_Train, Y_Train, label, info_dict, minor_list



def save_result(result,dn = BASE_DIR + r'/result'):
    today = int(mytime.strftime("%Y%m%d%H%M%S", mytime.localtime()))
    fn = dn + r'/gp_%s.pkl' % today
    n = 2
    while os.path.exists(fn):
        fn = dn + r'/gp_%s_%s.pkl' % (today,n)
        n = n + 1
    
    with open(fn,'wb') as file:
        pickle.dump(result,file)
    print('结果已保存',fn)

def save_code():
    dn = BASE_DIR + r'/result'
    dlist = os.listdir(dn)
    dlist.sort()
    fname = dlist[-1][3:-4]
    dn_out = BASE_DIR + r'/code_version/%s' % fname
    mf.my_create_dname(dn_out)
    shutil.copytree(BASE_DIR + r'/my_gplearn',dn_out + r'/my_gplearn')
    print('已备份文件%s' % dn_out)
    shutil.copy(BASE_DIR + r'/main_gp_hc.py',dn_out + r'/main_gp_hc.py')

    
# X_Train,Y_Train,label,info_dict = load_data(index_code = '000906.SH',name = 'close',period = 63,t1 = 20140101,t2 = 20221129)

# # print(123)
# X_Train,Y_Train,label,info_dict = load_data(index_code = '000906.SH',name = 'close',period = 63,t1 = 20140101,t2 = 20221129)
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Y_Train,metric = 'my_score_fixed_lose',population_size = 20000,parsimony_coefficient='fixed_15_20_4.5_0.1',random_state = random.randint(0,10000),generations = 5,max_samples = 0.7)
# save_result([info_dict,est_gp])
# train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 2)
#
#
#
# X_Train,Y_Train,label,info_dict = load_data(index_code = '000906.SH',name = 'close',period = 63,t1 = 20140101,t2 = 20221129)
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Y_Train,metric = 'my_score_fixed_lose',population_size = 20000,parsimony_coefficient='fixed_15_20_4.5_0.1',random_state = random.randint(0,10000),generations = 5,max_samples = 0.7,const_range = (-1.,1.))
# save_result([info_dict,est_gp])
# train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 2)
#
# # X_Train,Y_Train,label,info_dict = load_data(index_code = '000906.SH',name = 'simple_close_63',period = 63,t1 = 20140101,t2 = 20221129)
# # est_gp,X,y,score_df = train(label,X_Train,Y_Train,Y_Train,metric = 'my_score_fixed_lose',population_size = 20000,parsimony_coefficient='fixed_15_20_4.5_0.1',random_state = random.randint(0,10000),generations = 5,max_samples = 0.7)
# # save_result([info_dict,est_gp])
# # train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 2)

# X_Train,Y_Train,label,info_dict,Minor_List = load_data_list(main_index_code = '000906.SH',index_list = ['000300.SH','000905.SH'],name = 'close',period = 63,zscore_n = 252,t1 = 20140101,t2 = 20221129)
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Minor_List,metric = 'my_score_fixed_lose',population_size = 20000,parsimony_coefficient='fixed_15_20_4.5_0.1',random_state = random.randint(0,10000),generations = 5,max_samples = 0.7)
# save_result([info_dict,est_gp])

# X_Train,Y_Train,label,info_dict,Minor_List = load_data_list(main_index_code = '000906.SH',index_list = ['000300.SH','000905.SH'],name = 'close',period = 63,zscore_n = 252,t1 = 20140101,t2 = 20221129)
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Minor_List,metric = 'my_score_fixed_lose',population_size = 20000,parsimony_coefficient='fixed_20_50_0.5_0.2',random_state = random.randint(0,10000),generations = 5,max_samples = 0.7,const_range = (1, 1),tournament_size = 200)
# save_result([info_dict,est_gp])
# train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 2)
#
# X_Train,Y_Train,label,info_dict,Minor_List = load_data_list(main_index_code = '000906.SH',index_list = ['000300.SH','000905.SH'],name = 'close',period = 63,zscore_n = 252,t1 = 20140101,t2 = 20221129)
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Minor_List,metric = 'my_score_fixed_lose',population_size = 20000,parsimony_coefficient='fixed_20_50_0.5_0.2',random_state = random.randint(0,10000),generations = 5,max_samples = 0.7,const_range = (-1, 1),tournament_size = 200)
# save_result([info_dict,est_gp])
# train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 2)



# X_Train,Y_Train,label,info_dict,Minor_List = load_data_list(main_index_code = '000906.SH',index_list = ['000300.SH','000905.SH'],name = 'close',period = 63,zscore_n = 252,t1 = 20140101,t2 = 20221129)
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Minor_List,metric = 'my_score_rl_only',population_size = 20000,parsimony_coefficient='fixed_20_50_0.5_0.1',random_state = random.randint(0,10000),generations = 5,max_samples = 0.7,const_range = (-1, 1),tournament_size = 1000)
# save_result([info_dict,est_gp])
# train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 2)

#
# X_Train,Y_Train,label,info_dict,Minor_List = load_data_list(main_index_code = '000906.SH',index_list = ['000300.SH','000905.SH'],name = 'close',period = 63,zscore_n = 252,t1 = 20140101,t2 = 20221129)
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Minor_List,metric = 'my_score_rl_only_auto_para',population_size = 20000,parsimony_coefficient='fixed_20_50_0.5_0.1',random_state = random.randint(0,10000),generations = 5,max_samples = 0.7,const_range = (-1, 1),tournament_size = 200)
# save_result([info_dict,est_gp])
# train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 1)
#
# X_Train,Y_Train,label,info_dict,Minor_List = load_data_list(main_index_code = '000906.SH',index_list = ['000300.SH','000905.SH'],name = 'close',period = 63,zscore_n = 252,t1 = 20140101,t2 = 20221129)
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Minor_List,metric = 'my_score_fixed_lose',population_size = 20000,parsimony_coefficient='fixed_15_20_4.5_0.1',random_state = random.randint(0,10000),generations = 5,max_samples = 0.7,const_range = (-1, 1),tournament_size = 200)
# save_result([info_dict,est_gp])
# train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 1)
#
#
# X_Train,Y_Train,label,info_dict,Minor_List = load_data_list(main_index_code = '000906.SH',index_list = ['000300.SH','000905.SH'],name = 'close',period = 63,zscore_n = 252,t1 = 20140101,t2 = 20221129)
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Minor_List,metric = 'my_score_rl_only',population_size = 20000,parsimony_coefficient='fixed_20_50_0.5_0.1',random_state = random.randint(0,10000),generations = 1,max_samples = 0.7,const_range = (-1, 1),tournament_size = 200)
# save_result([info_dict,est_gp])
# train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 1)
# # save_code()
#
# X_Train,Y_Train,label,info_dict,Minor_List = load_data_list(main_index_code = '000906.SH',index_list = ['000300.SH','000905.SH'],name = 'close',period = 63,zscore_n = 252,t1 = 20140101,t2 = 20221129)
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Minor_List,metric = 'my_score_lose_penalty',population_size = 20000,parsimony_coefficient='fixed_20_50_0.5_0.1',random_state = random.randint(0,10000),generations = 5,max_samples = 0.7,const_range = (-1, 1),tournament_size = 200)
# save_result([info_dict,est_gp])
# train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 1)
# save_code()



# X_Train,Y_Train,label,info_dict,Minor_List = load_data_list(main_index_code = '000906.SH',index_list = ['000300.SH','000905.SH'],name = 'close',period = 63,zscore_n = 252,t1 = 20100104,t2 = 20221129)
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Minor_List,metric = 'my_score_fixed_lose',population_size = 20000,parsimony_coefficient='fixed_15_20_4.5_0.1',random_state = random.randint(0,10000),generations = 5,max_samples = 0.85,const_range = (-1, 1),tournament_size = 200)
# save_result([info_dict,est_gp])
# train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 1)
#
#
# X_Train,Y_Train,label,info_dict,Minor_List = load_data_list(main_index_code = '000906.SH',index_list = ['000300.SH','000905.SH'],name = 'close',period = 63,zscore_n = 252,t1 = 20100104,t2 = 20221129)
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Minor_List,metric = 'my_score_rl_only',population_size = 20000,parsimony_coefficient='fixed_20_50_0.5_0.1',random_state = random.randint(0,10000),generations = 1,max_samples = 0.85,const_range = (-1, 1),tournament_size = 200)
# save_result([info_dict,est_gp])
# train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 1)
# # save_code()
#
# X_Train,Y_Train,label,info_dict,Minor_List = load_data_list(main_index_code = '000906.SH',index_list = ['000300.SH','000905.SH'],name = 'close',period = 63,zscore_n = 252,t1 = 20100104,t2 = 20221129)
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Minor_List,metric = 'my_score_lose_penalty',population_size = 20000,parsimony_coefficient='fixed_20_50_0.5_0.1',random_state = random.randint(0,10000),generations = 5,max_samples = 0.85,const_range = (-1, 1),tournament_size = 200)
# save_result([info_dict,est_gp])
# train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 1)
# save_code()



# X_Train,Y_Train,label,info_dict,Minor_List = load_data_list(main_index_code = '000906.SH',index_list = ['000300.SH','000905.SH'],name = 'close',period = 63,zscore_n = 252,t1 = 20100104,t2 = 20221129)
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Minor_List,metric = 'my_score_fixed_sharp',population_size = 20000,parsimony_coefficient='fixed_20_50_0.5_0.1',random_state = random.randint(0,10000),generations = 5,max_samples = 0.85,const_range = (-1, 1),tournament_size = 200)
# save_result([info_dict,est_gp])
# train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 1)
# save_code()

# X_Train,Y_Train,label,info_dict,Minor_List = load_data_list(main_index_code = '000906.SH',index_list = ['000300.SH','000905.SH'],name = 'close',period = 63,zscore_n = 252,t1 = 20100104,t2 = 20221129)


# X_Train, Y_Train, label, info_dict, Minor_List = load_data_list_month()
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Minor_List,metric = 'my_score_return_only_month',population_size = 200,parsimony_coefficient='auto',random_state = random.randint(0,10000),generations = 5,max_samples = 0.7,const_range = (-1, 1),tournament_size = 10)
# save_result([info_dict,est_gp])


# X_Train, Y_Train, label, info_dict, Minor_List = load_data_list_month()
# X_Train,Y_Train,label,info_dict,Minor_List = load_data_list(main_index_code = '000906.SH',index_list = ['000300.SH','000905.SH'],name = 'close',period = 63,zscore_n = 252,t1 = 20100104,t2 = 20221129)
# est_gp,X,y,score_df = train(label,X_Train,Y_Train,Minor_List,metric = 'my_score_return_only_month',population_size = 200,parsimony_coefficient='auto',random_state = random.randint(0,10000),generations = 5,max_samples = 0.7,const_range = (-1, 1),tournament_size = 10)
# save_result([info_dict,est_gp])



X_Train,Y_Train,label,info_dict,Minor_List = load_data_list_month(main_index_code = '000906.SH',index_list = ['000300.SH','000905.SH'],name = 'close',t1 = 20120201,t2 = 20230101)
est_gp,X,y,score_df = train(label,X_Train,Y_Train,Minor_List,metric = 'my_score_return_only_month',population_size = 20000,parsimony_coefficient='fixed_5_20_0.003_0.02',random_state = random.randint(0,10000),generations = 5,max_samples = 0.7,const_range = None,tournament_size = 200,test_mode = 0)
save_result([info_dict,est_gp])
# train_by_step(est_gp,X,y,score_df,info_dict,step = 5,n_step = 1)
save_code()
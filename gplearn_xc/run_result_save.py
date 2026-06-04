import pandas as pd
import numpy as np

from tqdm import tqdm
from joblib import Parallel, delayed

import os
import time as mytime
import pickle
import shutil
import random
from my_gplearn.genetic import SymbolicRegressor

import sys
# print(os.path.abspath('../my_functions'))
sys.path.append(os.path.abspath('../my_functions'))
import my_fun as mf

# BASE_DIR = r'D:/Work/遗传算法测试'

BASE_DIR = r'/data/user/017839/my_python/gplearn_xc'


def get_fitness_list(gp_gen,gen = 0):
    # gp_gen = est_gp._programs[gen]
    fit_list = []
    for i in range(len(gp_gen)):
        if gp_gen[i] is None:
            fitness = np.nan
            oob_fitness = np.nan
            length = np.nan
        else:
            fitness = gp_gen[i].raw_fitness_
            oob_fitness = gp_gen[i].oob_fitness_
            length = gp_gen[i].length_
        fit_list.append([gen,i,fitness,oob_fitness,length])
    return fit_list

def get_fitness_parallel(est_gp,n_jobs = -1):
    n_gen = len(est_gp._programs)
    # gp_gen = est_gp._programs[gen]
    result = Parallel(n_jobs=n_jobs,verbose = 0)(delayed(get_fitness_list)(est_gp._programs[i],i) for i in tqdm(range(n_gen),position = 0))
    
    rlist = []
    for i in result:
        rlist = rlist + i
        
    result = pd.DataFrame(rlist,columns = ['gen','idx','fitness','out_fitness','length'])
    result = result.sort_values(by = 'out_fitness',ascending = False)
    return result
        
def load_result(fn):
    with open(BASE_DIR + r'/result/%s' % fn,'rb') as file:
        result = pickle.load(file)
    print(result[0])
    est_gp = result[1]
    # for i in est_gp._programs[0]:
    #     print(i.__str__())
    result = get_fitness_parallel(est_gp)
    name = fn[:-4]
    print(BASE_DIR + r'/result_df')
    mf.my_create_dname(BASE_DIR + r'/result_df')
    mf.my_create_dname(BASE_DIR + r'/result_df/%s' % name)
    print(name,name)
    result.to_csv(BASE_DIR + r'/result_df/%s/%s.csv' % (name,name),encoding = 'gbk')



def save_functions(fn_train, index):
    # fn_train = BASE_DIR + r'/result/%s' % fn_train
    file_name = fn_train.split('\\')[-1]
    file_name = file_name[:-4]

    flag = 1
    for i in index:
        gen, idx = i
        gen = int(gen)
        idx = int(idx)
        save_name = '%s_index_%s_%s.pkl' % (file_name, gen, idx)
        # if not os.path.exists(BASE_DIR + r'/result_df/%s/%s' % (file_name,save_name)):
        #     flag = 1
        #     break

    if flag == 1:
        with open(BASE_DIR + r'/result/%s' % fn_train, 'rb') as file:
            result = pickle.load(file)

        with open(BASE_DIR + r'/result_df/%s/%s' % (file_name, 'info.txt'), 'w') as file:
            file.write(str(result[0]))
            print(str(result[0]))



        est_gp = result[1]
        # return est_gp
        with open(BASE_DIR + r'/result_df/%s/%s' % (file_name, 'info.pkl'), 'wb') as file:
            para_info ={}
            para_info['fitness_mode'] = est_gp.metric
            para_info['len_penalty'] = est_gp.parsimony_coefficient
            para_info['population_size'] = est_gp.population_size
            para_info['tournament_size'] = est_gp.tournament_size
            para_info['train_percent'] = est_gp.max_samples
            pickle.dump(para_info,file)
            print(para_info)

        for i in index:
            gen, idx = i
            gen = int(gen)
            idx = int(idx)
            program = est_gp._programs[gen][idx]
            save_name = '%s_index_%s_%s.pkl' % (file_name, gen, idx)
            print('生成函数文件:%s' % save_name)
            with open(BASE_DIR + r'/result_df/%s/%s' % (file_name,save_name), 'wb') as file:
                pickle.dump(program, file)
        print(result[0])
    else:
        print('%s的函数已存在' % file_name)

BASE_DIR = r'/data/user/017839/my_python/gplearn_xc'

def load_data_diff(index_code='000906.SH', name='close', t1=20140101, t2=20221129):
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

    return X_Train, Y_Train, label, info_dict

def load_data_list(main_index_code='000906.SH', index_list=['00300.SH', '000905.SH'], name='close', period=63,
                   zscore_n=252, t1=20140101, t2=20221129):
    # X_Train, Y_Train, label, info_dict = load_data(index_code=main_index_code, name=name, period=period,
    #                                                zscore_n=zscore_n, t1=t1, t2=t2)

    X_Train, Y_Train, label, info_dict = load_data_diff(index_code=main_index_code, name=name, t1=t1, t2=t2)

    minor_list = []
    # info_dict0 = info_dict
    for index_code in index_list:
        # X_Train, Y_Train, label, _ = load_data(index_code=index_code, name=name, period=period, zscore_n=zscore_n,
        #                                        t1=t1, t2=t2)

        X_Train, Y_Train, label, _ = load_data_diff(index_code=index_code, name=name, t1=t1, t2=t2)

        minor_list.append([X_Train, Y_Train])
    info_dict['index_list'] = index_list
    return X_Train, Y_Train, label, info_dict, minor_list



# name = 'gp_20230718125348'
# load_result(name + '.pkl')
# gen = 9
# idx = 120
# save_functions(name + '.pkl', [[gen,idx]])
# fn = r'%s_index_%s_%s.pkl' % (name,gen,idx)
# with open(BASE_DIR + r'/result_df/%s/%s' % (name,fn), 'rb') as file:
#     program = pickle.load(file)
# print(program.__str__())
#
# from fitness import _create_signal_by_percentile
# from fitness import _my_score_rl_only_auto_para
# from fitness import _my_score_fixed_lose
# from fitness import _my_score_rl_only
# from fitness import _my_score_fixed_lose_auto_para
# score_list1 = []
# score_list2 = []
# for code in ['000300.SH','000905.SH','000906.SH']:
#     X_Train, Y_Train, label, info_dict, Minor_List = load_data_list(main_index_code=code, index_list=[],
#                                                                     name='close', period=63, zscore_n=252, t1=20140101,
#
#                                                                  t2=20221129)
#
#     y_pred = program.execute(X_Train)
#     print(y_pred[-10:])
#     print(Y_Train[-10:])
#
#
#     signal = _create_signal_by_percentile(y_pred)
#
#     max_sample = 0.7
#     print(len(y_pred) * max_sample)
#     index1 = range(int(len(y_pred) * max_sample))
#     index2 = range(int(len(y_pred) * max_sample),len(y_pred))
#
#     # score1 = _my_score_fixed_lose(Y_Train,y_pred,index1)
#     # score2 = _my_score_fixed_lose(Y_Train,y_pred,index2)
#     # score1 = _my_score_fixed_lose(Y_Train,y_pred,index1)
#     # score2 = _my_score_fixed_lose(Y_Train,y_pred,index2)
#     score1 = _my_score_rl_only_auto_para(Y_Train,y_pred,index1)
#     score2 = _my_score_rl_only_auto_para(Y_Train,y_pred,index2)
#     # score1 = _my_score_fixed_lose_auto_para(Y_Train,y_pred,index1)
#     # score2 = _my_score_fixed_lose_auto_para(Y_Train,y_pred,index2)
#     score_list1.append(score1)
#     score_list2.append(score2)
#     print(score1,score2)
#     #     # return result
#     # # load_result('gp_20230320115402.pkl')
#     # # load_result('gp_20230320105119.pkl')
#     # rname = 'gp_20230717140401.pkl'
#     # # load_result(rname)
#     # save_functions(rname, [[3,525]])
#     # # print(1111)
# print(np.mean(score_list1),np.mean(score_list2))
#
name = 'gp_20231117141318'
# load_result(name + '.pkl')
save_functions(name + '.pkl', [[4,4970],[4,7620],[0,7884],[4,1032]])
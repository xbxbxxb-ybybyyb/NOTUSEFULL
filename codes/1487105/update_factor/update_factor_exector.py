# -*- coding: utf-8 -*-
import json
import numpy as np
import pandas as pd
import scipy.io as sio
import os
import sys
import datetime
from copy import deepcopy
import time
import pickle
from pickle import dump
from xquant.compute.aimr import AIMR
from sklearn.externals.joblib import Parallel,delayed
import sys
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=pd.io.pytables.PerformanceWarning)
sys.path.insert(0,'update_factor/')
from update_factor_exector import *
from config_path import *
#sys.path.insert(0,alpha_tool_path)
sys.path.insert(0,factor_management_path)


num_threads=24   
def save_data(factor,factor_type,df_update):
    if not os.path.exists(factor_help_path):
        os.makedirs(factor_help_path)
    if not os.path.exists(factor_data_path):
        os.makedirs(factor_data_path)
    if isinstance(df_update,dict):
        file = open(factor_help_path + factor + '.pkl','wb')
        pickle.dump(df_update,file)
        file.close()
        return 
    factor_path = factor_data_path + factor_type + '/'
    if(factor.endswith('Help')):
        factor_path = factor_help_path
    store_factor_list = os.listdir(factor_path)
    store_factor_list = [f[:-4] for f in store_factor_list]
    for indexs in df_update.index:
        num_valid_entry = np.sum(pd.notnull(df_update.loc[indexs]))
        if(num_valid_entry==0):
            print ('warning: invalid update for '+factor+' in'+str(indexs))
    

    if factor not in store_factor_list:
        print('warning: ', factor, ' not in database\n')
        df_update.to_pickle(factor_path + factor + '.pkl')
    else:
        store_data = pd.read_pickle(factor_path + factor + '.pkl')
        store_date = store_data.index
        update_date = df_update.index
        store_data=store_data.append(df_update)

        store_data = store_data.loc[~store_data.index.duplicated(keep='last')].sort_index()

        store_data.to_pickle(factor_path + factor + '.pkl')   
def parse_argument():
    if (len(sys.argv) != 3) and (len(sys.argv) != 1):
        raise Exception("0 or 2 arguments are needed")
    argus = {}
    argus['num_argv'] = len(sys.argv)
    if argus['num_argv'] == 3:
        print('start date: ', sys.argv[1])
        print('end date: ', sys.argv[2])
        argus['start_date'] = sys.argv[1]       # start date
        argus['end_date'] = sys.argv[2]         # end date
    return argus

def change_permission(store_path):
    # factor_type=['barra','call_auction','daily','est','minute']
    factor_type=os.listdir(store_path)
    for d in factor_type:
        factor_type_path=store_path+d+'/'
        os.system('chmod 755 -R ' + factor_type_path)
        factorlist=os.listdir(factor_type_path)
        for f in factorlist:
#             factor_store_path=factor_type_path+f
            os.system('chmod 755 -R '+factor_type_path+f)

def catalog_factor(catalog_path, suffix,catalog_type):

    all_data = []
    
    data_path = catalog_path + catalog_type + '/'
    if suffix == '.json':
        data_path += 'parameter_json/'
    data_list = os.listdir(data_path)
    data_list = [d[:-len(suffix)] for d in data_list if d.endswith(suffix)]
    all_data += data_list

    return all_data

def catalog_data(catalog_path, suffix):

    all_data = []
    catalog = {}
    
    if suffix == '.json':
        catalog_type = ['barra','daily']
    elif suffix == '.pkl':
        catalog_type = os.listdir(catalog_path)
    else:
        raise AssertionError('wrong suffix: %s' %suffix)

    for t in catalog_type:
        data_path = catalog_path + t + '/'
        if suffix == '.json':
            data_path += 'parameter_json/'
        data_list = os.listdir(data_path)
        data_list = [d[:-len(suffix)] for d in data_list if d.endswith(suffix)]
        all_data += data_list
        catalog[t] = data_list

    return all_data, catalog


def draw_factor_dependence_graph(factor_list, factor_param_catalog, factor_management_path):

    factor_type = {}
    factor_dependence_graph = []

    # _, factor_param_catalog = catalog_data(factor_management_path, '.json')

    for t,param in factor_param_catalog.items():

        t_factor = list(set(factor_list).intersection(param))
        for f in t_factor:
            factor_type[f] = t
            with open(factor_management_path + t + '/parameter_json/' + f + '.json') as json_data:
                j = json.load(json_data)
#             print(f)
#             print(j)
            dep_factor = list(set(j['def_arg']).intersection(factor_list))
            factor_dependence_graph += [(dep_f, f) for dep_f in dep_factor]


    return factor_dependence_graph, factor_type


def top_sort(factor_list, factor_dependence_graph):

    factor_update_order = []

    while len(factor_list)>0:

        node = deepcopy(factor_list)

        factor_w_dep = [dep[1] for dep in factor_dependence_graph]
        node = list(set(node).difference(factor_w_dep))
        if len(node)==0:
            node = factor_list

        factor_dep_g = []
        for dep in factor_dependence_graph:
            if dep[0] not in node:
                factor_dep_g.append(dep)
        factor_dependence_graph = factor_dep_g

        factor_list = list(set(factor_list).difference(node))

        factor_update_order.append(node)

    return factor_update_order
def cal_single_factor(f,f_type,start_date,end_date):
    factor_param_path = factor_management_path + f_type + '/parameter_json/' + f + '.json'
    sys.path.insert(0,factor_management_path + f_type + '/compute_script/')
    import Util
    from AlphaFactor import AlphaFactor
    import_str = 'from '+f+' import '+f
    exec(import_str)
    class_str = f+'('+'\''+factor_param_path+'\''+')'
    f_object = eval(class_str)
    df_update = f_object.calculate(start_date, end_date)
    package = __import__(f)
    f_object = getattr(package, f)(factor_param_path)
    df_update = f_object.calculate(start_date, end_date)
    if(isinstance(df_update,dict) or isinstance(df_update,pd.DataFrame)):
        save_data(f,f_type,df_update)

    return 
def cmd_help(f,f_type,start_date,end_date):
    os.system('python3 '+'update_factor/calc_single_factor.py '+f+' '+f_type+' '+start_date+' '+end_date)
def update_factor(factor_list,start_date='', end_date='',cmd_exec=False):

    all_factor_param, factor_param_catalog = catalog_data(factor_management_path, '.json')

    assert len(factor_list) > 0, 'empty factor list, nothing to update'
    invalid_factor = list(set(factor_list).difference(all_factor_param))
    assert len(invalid_factor) == 0, 'invalid factor in factor list: ' + str(invalid_factor)

    factor_dependence_graph, factor_type = draw_factor_dependence_graph(factor_list, factor_param_catalog, factor_management_path)

    factor_update_order = top_sort(factor_list, factor_dependence_graph)
    print('factor dependency graph has '+str(len(factor_update_order))+' layers.')
    for i in range(len(factor_update_order)):
        if cmd_exec:
            Parallel(n_jobs=num_threads)(delayed(cmd_help)(f,factor_type[f],start_date,end_date) for f in factor_update_order[i]) 
        else:
            Parallel(n_jobs=num_threads)(delayed(cal_single_factor)(f,factor_type[f],start_date,end_date) for f in factor_update_order[i])      
    return 

def check_factor_update_success(need_factor_list,f_type,start_date,end_date):
    f_type_path = factor_data_path+f_type+'/'
    factor_list = os.listdir(f_type_path)
    factor_list = [f[:-4] for f in factor_list if f.endswith('.pkl')]
    help_factor_list = os.listdir(factor_help_path)
    help_factor_list = [f[:-4] for f in help_factor_list if f.endswith('.pkl')]
    is_valid = pd.read_pickle(basic_data_path+'daily/is_valid.pkl').loc[start_date:end_date]
    success_update_factors = []
    fail_update_factors = list(set(need_factor_list).difference(set(factor_list+help_factor_list)))
    print('fail_update_factors:',len(fail_update_factors))
    for f in sorted(list(set(need_factor_list)&set(factor_list))):
        df_f = pd.read_pickle(f_type_path+f+'.pkl').loc[start_date:end_date]
        cond1 = df_f.index.tolist()==is_valid.index.tolist()
        null_sum = df_f.isnull().sum(axis=1)
        cond2 = len(null_sum[null_sum==len(is_valid.columns)])<1
        if cond1 & cond2:
            success_update_factors.append(f)
        else :
            print(f,cond1,cond2)
            fail_update_factors.append(f)
    return success_update_factors,fail_update_factors

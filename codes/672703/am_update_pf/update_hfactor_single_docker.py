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
import sys
from xquant.compute.aimr import AIMR
from sklearn.externals.joblib import Parallel,delayed
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=pd.io.pytables.PerformanceWarning)

sys.path.insert(0,'/data/group/800020/AlphaTools/')
factor_management_path = '/data/group/800020/Halpha/hf/'
basic_data_path = '/data/group/800020/AlphaDataCenter/Basic/'
factor_help_path = '/data/group/800020/AlphaDataCenter/Transit/factor_intermediate/'
update_factor_help_path = '/data/group/800020/AlphaDataCenter/Transit/update_factor/'
data_center_path = '/data/group/800020/AlphaDataCenter/'
factor_data_path = '/data/group/800020/AlphaDataCenter/HFactor/'

num_threads=24
def save_data(factor,factor_type,df_update):
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
    factor_type=['one_pm']
    for d in factor_type:
        factor_type_path=store_path+d+'/'
        os.system('chmod 755 -R ' + factor_type_path)
        factorlist=os.listdir(factor_type_path)
        for f in factorlist:
#             factor_store_path=factor_type_path+f
            os.system('chmod 755 -R '+factor_type_path+f)

def catalog_factor(catalog_path, suffix,catalog_type):

    all_data = []
    
    data_path = catalog_path + t + '/'
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
        catalog_type = [ 'one_pm']
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
    import xfactor.Util as Util
    from AlphaFactor import AlphaFactor
    from HFactor import HFactor
    import_str = 'from '+f+' import '+f
    exec(import_str)
    class_str = f+'('+'\''+factor_param_path+'\''+')'
    f_object = eval(class_str)
    df_update = f_object.calculate(start_date, end_date)
    package = __import__(f)
    f_object = getattr(package, f)(factor_param_path)
    df_update = f_object.calculate(start_date, end_date,mode=mode)
    if(isinstance(df_update,dict) or isinstance(df_update,pd.DataFrame)):
        save_data(f,f_type,df_update)

    return 
def update_factor(factor_list,start_date='', end_date=''):

    all_factor_param, factor_param_catalog = catalog_data(factor_management_path, '.json')

    assert len(factor_list) > 0, 'empty factor list, nothing to update'
    invalid_factor = list(set(factor_list).difference(all_factor_param))
    assert len(invalid_factor) == 0, 'invalid factor in factor list: ' + str(invalid_factor)

    factor_dependence_graph, factor_type = draw_factor_dependence_graph(factor_list, factor_param_catalog, factor_management_path)

    factor_update_order = top_sort(factor_list, factor_dependence_graph)
    print('factor dependency graph has '+str(len(factor_update_order))+' layers.')
    if not os.path.exists(update_factor_help_path):
        os.makedirs(update_factor_help_path)
    for i in range(len(factor_update_order)):
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
    for f in sorted(list(set(need_factor_list)&set(factor_list))):
        df_f = pd.read_pickle(f_type_path+f+'.pkl').loc[start_date:end_date]
        cond1 = df_f.index.tolist()==is_valid.index.tolist()
        null_sum = df_f.isnull().sum(axis=1)
        cond2 = len(null_sum[null_sum==len(is_valid.columns)])<1
        if cond1 & cond2:
            success_update_factors.append(f)
        else :
            fail_update_factors.append(f)
    return success_update_factors,fail_update_factors

argus = pd.read_pickle(update_factor_help_path+'hstart_end_date.pkl')
today = datetime.date.today().strftime('%Y%m%d')
batch_factor=int(AIMR.getParam()[0])
if(not 'start_date' in argus.keys()):
    argus['start_date']=today
if(not 'end_date' in argus.keys()):
    argus['end_date']=today
if(type(argus['start_date'])==int):
    argus['start_date']=str(argus['start_date'])
if(type(argus['end_date'])==int):
    argus['end_date']=str(argus['end_date'])
mode = 1
t0=time.time()
catalog_type=['one_pm']
for t in catalog_type:
    if not os.path.exists(factor_data_path+t+'/'):
        os.makedirs(factor_data_path+t+'/')
    factor_list=catalog_factor(factor_management_path,'.json',t)
    this_factor_list = pd.read_pickle(update_factor_help_path+'hfactor_dict.pkl')[batch_factor]
    factor_list = sorted(list(set(factor_list)&set(this_factor_list)))
    update_factor(factor_list,argus['start_date'], argus['end_date'])
    # success_update_factors,fail_update_factors = check_factor_update_success(factor_list,t,argus['start_date'],argus['end_date'])
    print("update "+t+' '+str(batch_factor)+" finished.")
    # print(str(len(success_update_factors))+' factor updated success.')
    # print(str(len(fail_update_factors))+' factor updated fail.')
    # print(str(fail_update_factors)+' updated fail.')

change_permission(factor_data_path)

